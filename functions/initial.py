import time
import random
import asyncio
import traceback
import ccxt
from typing import List

from libs.py_eth_async.client import Client
from libs.pretty_utils.miscellaneous.time_and_date import unix_to_strtime

from data import config
from data.models import Settings, WorkStatuses
from utils.db_api.database import db
from utils.db_api.models import Wallet
from tasks.controller import Controller
from utils.encryption import get_private_key
from utils.miscellaneous.postpone import postpone
from functions.select_random_action import select_random_action

from libs.py_eth_async.data.models import Networks
from data.config import logger, semaphore, lock

async def update_expired() -> None:
    now = int(time.time())
    expired_wallets: List[Wallet] = db.all(
        Wallet, Wallet.status.is_(WorkStatuses.Initial)
                & (Wallet.next_initial_action_time <= now)
    )
    if expired_wallets:
        settings = Settings()

        for wallet in expired_wallets:
            wallet.next_initial_action_time = now + random.randint(0, int(settings.initial_actions_delay.to_ / 2))
            logger.info(
                f'{wallet.address} | action time was re-generated: {unix_to_strtime(wallet.next_initial_action_time)}')
            # await print_to_log(
            #     text=f'Action time was re-generated: {unix_to_strtime(wallet.next_initial_action_time)}.',
            #     color=color, thread=thread, wallet=wallet
            # )
        db.commit()


def get_activate_chain() -> List[Networks]:
    settings = Settings()
    chains = [Networks.Polygon, Networks.Celo, Networks.Base, Networks.Optimism,
              Networks.Avalanche, Networks.BSC, Networks.Moonbeam]
    activate_chain = [chain for chain in chains if settings.source_chains[chain.name]]
    return activate_chain


async def get_chain_with_balance(wallet: Wallet) -> List[Networks]:
    settings = Settings()
    chains = get_activate_chain()
    chains_with_suff_balance = []
    min_balances = settings.chains_min_balances

    for chain in chains:
        client = Client(private_key=get_private_key(wallet.private_key), network=chain, proxy=wallet.proxy)
        balance = await client.wallet.balance()
        if balance.Ether > min_balances[chain.name]:
            chains_with_suff_balance.append(chain)

    return chains_with_suff_balance


async def withdraw(wallet: Wallet):
    settings = Settings()
    chains = get_activate_chain()
    usable_chains_for_with: List[Networks] = [chain for chain in chains if settings.withdrawal_networks[chain.name]]
    if not usable_chains_for_with:
        logger.warning('No withdrawal_networks - check config')
    chain = random.choice(usable_chains_for_with)
    amount = round(
        random.uniform(settings.withdrawal_amounts[chain.name][0],
                       settings.withdrawal_amounts[chain.name][1]),
        6)

    logger.warning(f'Not enought balance to perform any actions, Trying to withdraw {amount} {chain.coin_symbol} '
                   f'from {chain.cex} into {chain.name}')

    okx_fees = {
        'polygon': 0.1,
        'base': 0.00004,
        'optimism': 0.00004,
        'moonbeam': 0.01,
    }

    if chain.cex == 'OKX':
        if not settings.okx.credentials.api_key:
            logger.error('OKX API not filled in')

        account_okx = ccxt.okx({
            'apiKey': settings.okx.credentials.api_key,
            'secret': settings.okx.credentials.secret_key,
            'password': settings.okx.credentials.passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }})
        try:
            logger.info(f'OKX | {wallet.address} - Trying to withdraw {chain.coin_symbol} on {chain.name} '
                        f'via {chain.cex}')
            account_okx.withdraw(
                code=chain.coin_symbol,
                amount=amount,
                address=wallet.address,
                params={
                    "chain": chain.cex_network,
                    "fee": okx_fees[chain.name],
                    "pwd": settings.okx.credentials.passphrase
                }
            )
            logger.success(f'OKX | {wallet.address} - successfully withdrawn {amount}{chain.coin_symbol} '
                           f'on {chain.name}')
        except Exception as error:
            logger.error(f'OKX | {wallet.address} - Unable to withdraw, please check config + balances on OKX')

    elif chain.cex == 'Binance':
        if not settings.binance.credentials.api_key:
            logger.error('Binance API not filled in')

        account_binance = ccxt.binance({
            'apiKey': settings.binance.credentials.api_key,
            'secret': settings.binance.credentials.secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }})

        try:
            logger.info(f'Binance | {wallet.address} - Trying to withdraw {chain.coin_symbol} on {chain.name} '
                        f'via {chain.cex}')
            status = account_binance.withdraw(
                code=chain.coin_symbol,
                amount=amount,
                address=wallet.address,
                params={
                    "network": chain.cex_network
                }
            )
            logger.success(f'Binance | {wallet.address} - successfully withdrawn {amount}{chain.coin_symbol} '
                           f'on {chain.name}')
        except Exception as error:
            logger.error(f'Binance | {wallet.address} - Unable to withdraw, please check config + balances on Binance')
    else:
        logger.error("Unable to withdraw")

    wallet.next_initial_action_time = int(time.time() + (60 * random.randint(30, 180)))
    db.commit()


async def start_task(wallet):
    async with semaphore:
        now = int(time.time())
        settings = Settings()

        chain_with_balance = await get_chain_with_balance(wallet)
        if not chain_with_balance:
            await withdraw(wallet)
            wallet.next_initial_action_time = now + random.randint(
                int(settings.initial_actions_delay.from_ / 6), int(settings.initial_actions_delay.to_ / 3)
            )
            # logger.warning('Insufficient balance! Not chain with native balance, will try again a bit later')  # Mb прикрутить тут мост
            async with lock:
                db.commit()
            return

        sender_chain = random.choice(chain_with_balance)
        client = Client(
            private_key=get_private_key(wallet.private_key),
            network=sender_chain,
            proxy=wallet.proxy
        )

        controller = Controller(client=client)
        action = await select_random_action(controller=controller, wallet=wallet, initial=True)

        if action is None:
            wallet.next_initial_action_time = now + random.randint(
                int(settings.initial_actions_delay.from_),
                int(settings.initial_actions_delay.to_)
            )
            async with lock:
                db.commit()
            return

        if action == 'No chains with balance':  # TODO okx withdraw function on random chain
            wallet.status = WorkStatuses.NotStarted
            wallet.next_activity_action_time = now + random.randint(
                settings.initial_actions_delay.from_, settings.initial_actions_delay.to_
            )

        else:
            status = await action()
            now = int(time.time())
            if 'Failed' not in status:
                wallet.next_initial_action_time = now + random.randint(
                    settings.initial_actions_delay.from_, settings.initial_actions_delay.to_
                )
                logger.success(status)
                # print_color = color
            else:
                wallet.next_initial_action_time = now + random.randint(5 * 60, 10 * 60)
                # print_color = config.RED
                logger.error(status)
            # await print_to_log(text=status, color=print_color, thread=thread, wallet=wallet)

        async with lock:
            db.commit()


async def initial() -> None:
    delay = 10
    await update_expired()
    next_message_time = 0
    try:
        next_action_time = min((wallet.next_initial_action_time for wallet in db.all(
            Wallet, Wallet.status.is_(WorkStatuses.Initial)
        )))
        logger.info(f'The next closest action will be performed at {unix_to_strtime(next_action_time)}.')
        # await print_to_log(
        #     text=f'The next closest action will be performed at {unix_to_strtime(next_action_time)}.',
        #     color=color, thread=thread
        # )
    except:
        pass

    while True:
        try:
            now = int(time.time())
            wallets: Wallet = db.all(
                Wallet, Wallet.status.is_(WorkStatuses.Initial) & (Wallet.next_initial_action_time <= now)
            )

            if wallets:
                settings = Settings()
                client = Client(private_key='', network=Networks.Ethereum)
                gas_price = await client.transactions.gas_price(w3=client.w3)
                if float(gas_price.GWei) > settings.maximum_gas_price:
                    await postpone(seconds=int(delay / 2))
                    if next_message_time <= time.time():
                        next_message_time = now + 30 * 60
                        logger.info(
                            f'Current gas price is too high: {gas_price.GWei} > {settings.maximum_gas_price.GWei}!')
                        # await print_to_log(
                        #     text=f'Current gas price is too high: {gas_price.GWei} > {settings.maximum_gas_price.GWei}!',
                        #     color=color, thread=thread
                        # )
                    continue

                task = []
                for wallet in wallets:
                    task.append(asyncio.create_task(start_task(wallet)))

                await asyncio.gather(*task)

                try:
                    next_action_time = min((wallet.next_initial_action_time for wallet in db.all(
                        Wallet, Wallet.status.is_(WorkStatuses.Initial)
                    )))
                    logger.info(f'The next closest action will be performed at {unix_to_strtime(next_action_time)}.')
                    # await print_to_log(
                    #     text=f'The next closest action will be performed at {unix_to_strtime(next_action_time)}.',
                    #     color=color, thread=thread
                    # )

                except:
                    pass

        except BaseException as e:
            logger.error('initial')
            print(traceback.print_exc())
            logger.error(f'Something went wrong: {e}')
            # await print_to_log(text=f'Something went wrong: {e}', color=config.RED, thread=thread)

        finally:
            await asyncio.sleep(delay)


color = config.GREEN
thread = 'Initial'
