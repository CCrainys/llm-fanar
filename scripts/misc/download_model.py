# Copyright 2022 MosaicML LLM Foundry authors
# SPDX-License-Identifier: Apache-2.0

"""Script to download model weights from Hugging Face Hub or a cache server.

Download from Hugging Face Hub:
    python download_model.py hf --model mosaicml/mpt-7b --save-dir <save_dir> --token <token>

Download from ORAS registry:
    python download_model.py oras --registry <registry> --path mosaicml/mpt-7b --save-dir <save_dir>

Download from an HTTP file server:
    python download_model.py http --host https://server.com --path mosaicml/mpt-7b --save-dir <save_dir>
"""
import argparse
import logging
import os

from llmfoundry.utils.model_download_utils import (
    download_from_hf_hub, download_from_http_fileserver, download_from_oras)

HF_TOKEN_ENV_VAR = 'HUGGING_FACE_HUB_TOKEN'

logging.basicConfig(format=f'%(asctime)s: %(levelname)s: %(name)s: %(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='download_from', required=True)

    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('--save-dir', type=str, required=True)

    # Add subparser for downloading from Hugging Face Hub.
    hf_parser = subparsers.add_parser('hf', parents=[base_parser])
    hf_parser.add_argument('--model', type=str, required=True)
    hf_parser.add_argument('--prefer-safetensors', type=bool, default=True)
    hf_parser.add_argument('--token',
                           type=str,
                           default=os.getenv(HF_TOKEN_ENV_VAR))

    # Add subparser for downloading from ORAS registry.
    oras_parser = subparsers.add_parser('oras', parents=[base_parser])
    oras_parser.add_argument('--registry', type=str, required=True)
    oras_parser.add_argument('--path', type=str, required=True)
    oras_parser.add_argument('--username', type=str, default='')
    oras_parser.add_argument('--password', type=str, default='')
    oras_parser.add_argument('--concurrency', type=int, default=10)

    # Add subparser for downloading from an HTTP file server.
    http_parser = subparsers.add_parser('http', parents=[base_parser])
    http_parser.add_argument('--host', type=str, required=True)
    http_parser.add_argument('--path', type=str, required=True)
    http_parser.add_argument('--ignore-cert',
                             action='store_true',
                             default=False)

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    download_from = args.download_from

    if download_from == 'http':
        download_from_http_fileserver(args.host, args.path, args.save_dir,
                                      args.ignore_cert)
    elif download_from == 'hf':
        download_from_hf_hub(args.model,
                             save_dir=args.save_dir,
                             token=args.token,
                             prefer_safetensors=args.prefer_safetensors)
    elif download_from == 'oras':
        download_from_oras(args.registry, args.path, args.save_dir,
                           args.username, args.password, args.concurrency)
