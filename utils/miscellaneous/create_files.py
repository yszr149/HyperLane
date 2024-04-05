import time
from typing import Optional

from libs.pretty_utils.type_functions.dicts import update_dict
from libs.pretty_utils.miscellaneous.files import touch, write_json, read_json

from data import config
from utils.miscellaneous.create_spreadsheet import create_spreadsheet


def create_files():
    touch(path=config.FILES_DIR)
    create_spreadsheet(path=config.IMPORT_FILE, headers=('private_key', 'name', 'proxy'),
                       sheet_name='Wallets')

    try:
        current_settings: Optional[dict] = read_json(path=config.SETTINGS_FILE)

    except:
        current_settings = {}

    settings = {
        'use_private_key_encryption': False,
        'maximum_gas_price': 75,
        'oklink_api_key': '',
        'okx': {
            'required_minimum_balance': 0.0001,
            'withdraw_amount': {'from': 0.001, 'to': 0.009},
            'credentials': {
                'api_key': '',
                'secret_key': '',
                'passphrase': '',
            }
        },
        'binance': {
            'required_minimum_balance': 0.0001,
            'withdraw_amount': {'from': 0.001, 'to': 0.009},
            'credentials': {
                'api_key': '',
                'secret_key': '',
            }
        },
        'initial_actions_delay': {'from': 432000, 'to': 1728000},
        'h_mekr': {'from': 1, 'to': 10},
        'h_nft': {'from': 1, 'to': 3},
        'hFT_amount_for_mint_and_bridge': {'from': 1, 'to': 20},
        'chains_min_balances': {
            'polygon': 0.25,
            'celo': 0.2,
            'base': 0.0002,
            'optimism': 0.0002,
            'avalanche': 0.0088,
            'bsc': 0.00055908,
            'moonbeam': 0.5
        },
        'source_chains': {
            'polygon': True,
            'celo': True,
            'base': True,
            'optimism': True,
            'avalanche': True,
            'bsc': True,
            'moonbeam': True
        },
        'destination_chains': {
            'polygon': True,
            'celo': True,
            'base': True,
            'optimism': True,
            'avalanche': True,
            'bsc': True,
            'moonbeam': True
        },
        'withdrawal_networks': {
            'polygon': True,
            'celo': True,
            'base': True,
            'optimism': True,
            'avalanche': True,
            'bsc': True,
            'moonbeam': True
        },
        'withdrawal_amounts': {
            'polygon': [0.5, 2.5],
            'celo': [0.18, 1],
            'base': [0.0021, 0.0032],
            'optimism': [0.00013, 0.00078],
            'avalanche': [0.007, 0.0375],
            'bsc': [0.00084, 0.00335],
            'moonbeam': [0.45, 3]

        },
    }
    write_json(path=config.SETTINGS_FILE, obj=update_dict(modifiable=current_settings, template=settings), indent=2)


create_files()