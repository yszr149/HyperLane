import time
import random
import ccxt

from loguru import logger
from libs.py_okx_async.models import Chains
from libs.py_eth_async.client import Client
from libs.py_eth_async.data.models import Networks
from libs.pretty_utils.type_functions.floats import randfloat
from withdrawal.okx_actions import OKXActions


from utils.encryption import get_private_key
from data.models import Settings, Scroll
from utils.db_api.models import Wallet


async def okx_withdraw(wallets: list[Wallet]):
    settings = Settings()
    okx = OKXActions(credentials=settings.okx.credentials)

    for num, wallet in enumerate(wallets, start=1):
        logger.info(f'{num}/{len(wallets)} wallets')
        eth_client = Client(private_key=get_private_key(wallet.private_key), network=Networks.Ethereum, proxy=wallet.proxy)
        evm_client = Client(private_key=get_private_key(wallet.private_key), network=Scroll, proxy=wallet.proxy)

        if settings.use_official_bridge:
            balance = await eth_client.wallet.balance()
        else:
            balance = await evm_client.wallet.balance()

        if float(balance.Ether) >= settings.okx.required_minimum_balance:
            continue

        amount_to_withdraw = randfloat(
            from_=settings.okx.withdraw_amount.from_,
            to_=settings.okx.withdraw_amount.to_,
            step=0.0000001
        )

        res = await okx.withdraw(
            to_address=str(eth_client.account.address),
            amount=amount_to_withdraw,
            token_symbol='ETH',
            chain=Chains.ERC20 if settings.use_official_bridge else Chains.zkSyncEra
        )

        if 'Failed' not in res:
            logger.success(f'{wallet.name}: {res}')
            if num == len(wallets):
                logger.success(f'OKX withdraw successfully completed with {len(wallets)} wallets')
                continue
            time.sleep(random.randint(
                settings.okx.delay_between_withdrawals.from_, settings.okx.delay_between_withdrawals.to_))
        else:
            logger.error(f'{wallet.name}: {res}')


async def binance_withdraw(wallets: list[Wallet]):
    settings = Settings()
    account_binance = ccxt.binance({
        'apiKey': settings.binance.credentials.api_key,
        'secret': settings.binance.credentials.secret_key,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot'
        }
    })

    for num, wallet in enumerate(wallets, start=1):
        logger.info(f'{num}/{len(wallets)} wallets')

        # evm_client = Client(private_key=get_private_key(wallet.private_key), network=EVM_network, proxy=wallet.proxy)
        fee = 0.0002
        symbol = 'ETH'
        amount = randfloat(
            from_=settings.binance.withdraw_amount.from_,
            to_=settings.binance.withdraw_amount.to_,
            step=0.0000001)+fee

        try:
            account_binance.withdraw(
                code='ETH',
                amount=amount,
                address=wallet.address,
                tag=None,
                params={
                    "network": Scroll.name
                }
            )
            logger.success(f'Binance successfully withdrawn {symbol} to {wallet.address}:{wallet.name} '
                           f'on {Scroll.name}')
            if num == len(wallets):
                logger.success(f'OKX withdraw successfully completed with {len(wallets)} wallets')
                continue
            time.sleep(random.randint(
                settings.okx.delay_between_withdrawals.from_, settings.okx.delay_between_withdrawals.to_))
        except Exception as error:
            logger.error(f'{wallet.address}:{wallet.name}: {error}')
