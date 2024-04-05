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
            'polygon': 1,
            'celo': 1,
            'base': 0.00045,
            'optimism': 0.00045,
            'avalanche': 0.00045,
            'bsc': 0.0025911,
            'moonbeam': 2
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
            'polygon': [1.2, 3],
            'celo': [1,2],
            'base': [0.006, 0.01],
            'optimism': [0.006, 0.01],
            'avalanche': [0.035, 0.066],
            'bsc': [0.0027586, 0.0051724],
            'moonbeam': [2.5, 4]

        },
    }
    write_json(path=config.SETTINGS_FILE, obj=update_dict(modifiable=current_settings, template=settings), indent=2)


create_files()
