import os
import sys
import asyncio
import getpass
import aiofiles
import json

from loguru import logger
from utils.miscellaneous.create_files import create_files

from data import config
from functions.Export import Export

from functions.Import import Import
from functions.initial import initial
from utils.encryption import get_cipher_suite
from data.config import SALT_PATH, CIPHER_SUITE, BALANCE
from data.models import ProgramActions, Settings, Networks, Wei

from utils.user_menu import get_action
from utils.db_api.database import get_wallets, db
from utils.db_api.models import Wallet
from utils.adjust_policy import set_windows_event_loop_policy
from libs.py_eth_async.client import Client


def check_encrypt_param(settings):
    if settings.use_private_key_encryption:
        if not os.path.exists(SALT_PATH):
            print(f'You need to add salt.dat to {SALT_PATH} for correct decryption of private keys!\n'
                  f'After the program has started successfully, you can delete this file. \n\n'
                  f'If you do not need encryption, please change use_private_key_encryption to False.')
            sys.exit(1)
        with open(SALT_PATH, 'rb') as f:
            salt = f.read()
        user_password = getpass.getpass('[DECRYPTOR] Write here you password '
                                        '(the field will be hidden): ').strip().encode()
        CIPHER_SUITE.append(get_cipher_suite(user_password, salt))


async def start_withdraw_okx_and_bridge():
    settings = Settings()

    if not settings.oklink_api_key:
        logger.error('Specify the API key for Oklink.com!')
        return

    if not settings.okx.credentials.completely_filled():
        logger.error('OKX credentials not filled')
        return

    wallets = db.all(
        Wallet,
        Wallet.status.is_not('initial')
        & Wallet.status.is_not('activity')
    )
    if not wallets:
        logger.error('Вы не добавили кошельки в бд или нет подходящих кошельков для бриджа по статусу!')
        return
    # await pre_initial()


async def start_script():
    wallets = get_wallets()
    if not wallets:
        logger.error('Вы не добавили кошельки в бд!')
        return

    await asyncio.wait([
        asyncio.create_task(initial())
    ])


async def get_balance(client):
    for _ in range(100):
        try:
            return Wei(await client.w3.eth.get_balance(client.account.address))
        except asyncio.TimeoutError:
            await asyncio.sleep(1)


async def check_wallet_balance(wallet, networks, balances_dict):
    wallet_balances = {}
    for network in networks:
        client = Client(private_key=wallet.private_key, network=network, proxy=wallet.proxy)
        balance = await get_balance(client)
        wallet_balances[network.name] = float(balance.Ether)
    balances_dict[wallet.address] = wallet_balances


async def check_account_balances():
    wallets = get_wallets()
    if not wallets:
        logger.error('Вы не добавили кошельки в бд!')
        return

    networks = [Networks.Scroll, Networks.Arbitrum, Networks.Optimism, Networks.Base, Networks.Linea]
    balances_dict = {}
    tasks = []

    for wallet in wallets:
        task = asyncio.create_task(check_wallet_balance(wallet, networks, balances_dict))
        tasks.append(task)

    await asyncio.gather(*tasks)

    async with aiofiles.open(BALANCE, 'w') as file:
        await file.write(json.dumps(balances_dict, indent=4))

    logger.info('Проверка завершена.')


def print_logo():
    print("""\

     █████╗ ██████╗ ██████╗ ██╗   ██╗███████╗███████╗██████╗ ███████╗
    ██╔══██╗██╔══██╗██╔══██╗██║   ██║╚══███╔╝██╔════╝██╔══██╗██╔════╝
    ███████║██████╔╝██████╔╝██║   ██║  ███╔╝ █████╗  ██████╔╝███████╗
    ██╔══██║██╔══██╗██╔══██╗██║   ██║ ███╔╝  ██╔══╝  ██╔══██╗╚════██║
    ██║  ██║██║  ██║██████╔╝╚██████╔╝███████╗███████╗██║  ██║███████║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝
    """)


if __name__ == '__main__':
    print_logo()
    create_files()
    set_windows_event_loop_policy()
    main_settings = Settings()
    check_encrypt_param(main_settings)
    loop = asyncio.new_event_loop()

    try:

        action = get_action()

        match action:

            # Импорт
            case ProgramActions.ImportWallets.Selection:
                asyncio.run(Import.wallets())
            #
            # # Экспорт
            # case ProgramActions.ExportWallets.Selection:
            #     asyncio.run(Export.wallets())

            # Подготовка кошелька (вывод-бридж)
            # case ProgramActions.OKXWithdrawal.Selection:
            #     loop = asyncio.get_event_loop()
            #     loop.run_until_complete(start_withdraw_okx_and_bridge())
            #
            #     # asyncio.run не работает с okx!
            #     # asyncio.run(start_withdraw_okx_and_bridge())

            # Запуск основных действий
            case ProgramActions.StartScript.Selection:
                asyncio.run(start_script())

            # case ProgramActions.CheckBalance.Selection:
            #     asyncio.run(check_account_balances())


    except (KeyboardInterrupt, TypeError):
        print()
        logger.info('Программа завершена')
        print()
        sys.exit(1)

    except ValueError as err:
        print(f"{config.RED}Value error: {err}{config.RESET_ALL}")

    except BaseException as e:
        logger.error('main')
        print(f'\n{config.RED}Something went wrong: {e}{config.RESET_ALL}\n')

    if action and action != ProgramActions.StartScript:
        input(f'\nPress {config.LIGHTGREEN_EX}Enter{config.RESET_ALL} to exit.\n')
