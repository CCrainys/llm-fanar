# Copyright 2022 MosaicML LLM Foundry authors
# SPDX-License-Identifier: Apache-2.0

"""Resume from a checkpoint with a different dataset, enabling proto-curriculum-learning.

This callback is currently experimental. The API may change in the future.
"""

import logging
from typing import Any, Dict
from composer.core import Callback
from streaming import StreamingDataset
from torch.utils.data import DataLoader

log = logging.getLogger(__name__)

class CurriculumLearning(Callback):
    """Starts a new epoch with a different dataset when resuming from a checkpoint.
	
	This callback is currently experimental. The API may change in the future.

    Args:
        dataset_index (int): The index of the dataset currently being used.
		current_dataset_config (Dict): The configuration of the dataset currently being used.
        dataset (StreamingDataset): The dataset currently being used.
    """
    def __init__(self,
                 dataset_index: int,
                 dataloader: DataLoader,
                 current_dataset_config: Dict):
        self.dataset_index = dataset_index
        self.saved_dataset_index = 0
        self.all_dataset_configs = []
        # The current dataset config is resolved and passed in train.py
        self.current_dataset_config = current_dataset_config
        self.new_dataset_setup = False

        # Must pass in dataset directly since it is not actually accessible at Event.INIT in
        # Composer. We need to get the new dataset state to override checkpoint dataset state.
        # Check if we are using a StreamingDataset
        dataset = dataloader.dataset
        if not isinstance(dataset, StreamingDataset):
            raise ValueError(f"CurriculumLearning callback only supports StreamingDataset ",
                             f"because it requires loading and saving dataset state. ",
                             f"Instead, got a dataset of type {type(dataset)}")
        # Save the current dataset state so we can restore it if needed.
        self.current_dataset_state = dataset.state_dict(0, False)
        log.info("Dataset state at init: ", self.current_dataset_state)
        
    def after_load(self, state, logger):
        del logger

		# As saved_dataset_index is loaded from state_dict, this only run when
        # a user explicitly increments the dataset_index and not on any other
		# resumption, including autoresume.
        dataset = state._train_dataloader.dataset
        if self.saved_dataset_index < self.dataset_index:
			# Ignore the dataset state that was read in from the checkpoint, and
            # replace with the new dataset state. This preserves resumption info.
            dataset.load_state_dict(self.current_dataset_state)
            # Start a new epoch since we are using a new dataset.
            # This will also reset the sample_in_epoch written to checkpoint,
            # making sure that subsequent resumptions proceed correctly.
            state.timestamp.to_next_epoch()
            self.new_dataset_setup = True
        log.info("Dataset state after checkpoint load: ", dataset.state_dict(0, False))
    
    def state_dict(self):
        if self.new_dataset_setup:
            # Append the new dataset config to the list of all dataset configs.
            self.all_dataset_configs.append(self.current_dataset_config)
        log.info("CurriculumLearning callback dataset index: ", self.dataset_index)
        log.info("CurriculumLearning callback all dataset configs: ", self.all_dataset_configs)
        return {'dataset_index': self.dataset_index,
                'all_dataset_configs': self.all_dataset_configs}
    
    def load_state_dict(self, state: Dict[str, Any]):
        self.saved_dataset_index = state.get('dataset_index', 0) 
        self.all_dataset_configs = state.get('all_dataset_configs', [])
        log.info("Datasets trained on with CurriculumLearning callback: ")
        for i, dataset_config in enumerate(self.all_dataset_configs):
            log.info(f"Dataset {i} config:")
            log.info(dataset_config)