import logging
from typing import List

from data import config
from data.models import Settings, WorkStatuses
from utils.db_api.database import db
from utils.db_api.models import Wallet

from libs.pretty_utils.miscellaneous.time_and_date import unix_to_strtime


def print_rpcs(rpcs):
    emp_str = ""
    for rpc in rpcs:
        emp_str += str(rpc) + "\n"

    return emp_str


async def print_summary():
    try:
        settings = Settings()

        pre_initial_wallets_number = 0
        nearest_pre_initial_wallet = '-'
        latest_pre_initial_wallet = '-'
        pre_initial_wallets: List[Wallet] = db.all(
            Wallet, Wallet.status.is_not(WorkStatuses.Initial) & Wallet.status.is_not(WorkStatuses.Activity))

        if pre_initial_wallets:
            pre_initial_wallets_number = len(pre_initial_wallets)
            nearest_pre_initial_wallet = unix_to_strtime(min((
                wallet.next_pre_initial_action_time for wallet in pre_initial_wallets
            )))
            latest_pre_initial_wallet = unix_to_strtime(max((
                wallet.next_pre_initial_action_time for wallet in pre_initial_wallets
            )))

        initial_wallets_number = 0
        nearest_initial_wallet = '-'
        latest_initial_wallet = '-'
        initial_wallets: List[Wallet] = db.all(Wallet, Wallet.status.is_(WorkStatuses.Initial))

        if initial_wallets:
            initial_wallets_number = len(initial_wallets)
            nearest_initial_wallet = unix_to_strtime(min((
                wallet.next_initial_action_time for wallet in initial_wallets
            )))
            latest_initial_wallet = unix_to_strtime(max((
                wallet.next_initial_action_time for wallet in initial_wallets
            )))
        activity_wallets_number = 0
        nearest_activity_wallet = '-'
        latest_activity_wallet = '-'
        activity_wallets: List[Wallet] = db.all(Wallet, Wallet.status.is_(WorkStatuses.Activity))

        if activity_wallets:
            activity_wallets_number = len(activity_wallets)
            nearest_activity_wallet = unix_to_strtime(min((
                wallet.next_activity_action_time for wallet in activity_wallets
            )))
            latest_activity_wallet = unix_to_strtime(max((
                wallet.next_activity_action_time for wallet in activity_wallets
            )))
        rpcs = settings.rpcs

        print(f'''
{config.LIGHTGREEN_EX}---------- Summary statistics ---------- {config.RESET_ALL}
The RPCs:
{config.LIGHTGREEN_EX}{print_rpcs(rpcs)}
The maximum gas price: {config.LIGHTGREEN_EX}{settings.maximum_gas_price.GWei}{config.RESET_ALL}

Wallets performing the pre-initial actions: {config.LIGHTGREEN_EX}{pre_initial_wallets_number}{config.RESET_ALL}
Nearest: {config.LIGHTGREEN_EX}{nearest_pre_initial_wallet}{config.RESET_ALL}
Latest: {config.LIGHTGREEN_EX}{latest_pre_initial_wallet}{config.RESET_ALL}

Wallets performing the initial actions: {config.LIGHTGREEN_EX}{initial_wallets_number}{config.RESET_ALL}
Nearest: {config.LIGHTGREEN_EX}{nearest_initial_wallet}{config.RESET_ALL}
Latest: {config.LIGHTGREEN_EX}{latest_initial_wallet}{config.RESET_ALL}

Wallets performing the activity actions: {config.LIGHTGREEN_EX}{activity_wallets_number}{config.RESET_ALL}
Nearest: {config.LIGHTGREEN_EX}{nearest_activity_wallet}{config.RESET_ALL}
Latest: {config.LIGHTGREEN_EX}{latest_activity_wallet}{config.RESET_ALL}
{config.LIGHTGREEN_EX}----------------------------------------{config.RESET_ALL}
''')

    except:
        logging.exception('print_summary')
