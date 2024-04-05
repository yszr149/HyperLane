import random
import time

import aiohttp
import asyncio
from loguru import logger

from hexbytes import HexBytes
from web3 import Web3
from web3.exceptions import ContractCustomError, ContractLogicError, TransactionNotFound
from fake_useragent import UserAgent
from typing import Optional, Union, Dict, Any
from web3.middleware import geth_poa_middleware

from libs.py_eth_async.client import Client
from aiohttp_proxy import ProxyConnector
from libs.pretty_utils.type_functions.floats import randfloat
from libs.py_eth_async.data.models import TxArgs, Ether, Wei, Unit, TokenAmount

# from data.config import logger
from data.models import Settings, SwapInfo

from data.exceptions import GetOKlinkTokenBalanceError, NoApiKeyFound
from data.models import Settings, Tokens, Liquidity_Tokens, Lending_Tokens

from utils.encryption import get_private_key
from libs.py_eth_async.data.models import Networks
from data.config import logger
from typing import List



from data.models import (
    Settings,
    TokenAmount,
    Tokens,
    Liquidity_Tokens,
    Lending_Tokens,
    Ether,
)

settings = Settings()
OKLINK_URL = 'https://www.oklink.com'
CHAIN_SHORT_NAME = 'scroll'


class Base:
    def __init__(self, client: Client):
        self.client = client

    async def get_decimals(self, contract_address: str) -> int:
        contract = await self.client.contracts.default_token(contract_address=contract_address)
        return await contract.functions.decimals().call()

    def get_random_amount(self):
        settings = Settings()
        return Ether(randfloat(
            from_=settings.eth_amount_for_swap.from_,
            to_=settings.eth_amount_for_swap.to_,
            step=0.0000001
        ))

    async def check_balance_insufficient(self, amount):
        """returns if balance does not have enough token"""
        settings = Settings()
        balance = await self.client.wallet.balance()
        # if balance < amount + settings.minimal_balance:
        if balance.Ether < amount.Ether:
            return True
        return False

    async def submit_transaction(self, tx_params, test=False):
        gas = await self.client.transactions.estimate_gas(w3=self.client.w3, tx_params=tx_params)

        tx_params['gas'] = gas.Wei

        if test:
            print(tx_params['data'])
            return "test", "test"
        else:
            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            return await tx.wait_for_receipt(client=self.client, timeout=300), tx.hash.hex()

    async def base_swap_eth_to_token(
            self,
            swap_data,
            amount,
            swap_info: SwapInfo,
            tx_paramam_have=False,
            test=False
    ):
        failed_text = (f'Failed to swap {swap_info.token_from.title} '
                       f'to {swap_info.token_to.title} via {swap_info.swap_platform.title}')

        try:
            if test:
                print(swap_data)

            if await self.check_balance_insufficient(amount):
                msg = (f'{self.client.account.address} | {swap_info.swap_platform.title} '
                       f'| swap_eth | insufficient eth balance')
                logger.error(msg)
                return msg

            logger.info(
                f'{self.client.account.address} | {swap_info.swap_platform.title} | swap_eth | amount: {amount.Ether}')

            if tx_paramam_have:
                tx_params = swap_data
            else:
                gas_price = await self.client.transactions.gas_price(w3=self.client.w3)

                tx_params = {
                    'gasPrice': gas_price.Wei,
                    'from': self.client.account.address,
                    'to': swap_info.swap_platform.address,
                    'data': swap_data,
                    'value': amount.Wei
                }

            try:
                receipt, tx_hash = await self.submit_transaction(tx_params)
                if receipt:
                    msg = (f'{amount.Ether} {swap_info.token_from.title} was swapped to '
                           f'{swap_info.token_to.title} via {swap_info.swap_platform.title}: {tx_hash}')
                    check_tx = await self.wait_tx_status(tx_hash=tx_hash)
                    if check_tx:
                        logger.success(msg)
                        return msg

                msg = (f'Failed to swap {swap_info.token_from.title} '
                       f'to {swap_info.token_to.title} via {swap_info.swap_platform.title}')
                logger.error(msg)
                return msg
            except (ContractCustomError, ContractLogicError):
                msg = (f'Failed to swap {swap_info.token_from.title} '
                       f'to {swap_info.token_to.title} via {swap_info.swap_platform.title}. ContractCustomError or ContractLogicError')
                logger.error(msg)
                return msg

        except BaseException as e:
            logger.error(f'{swap_info.swap_platform}.swap_eth')
            return f'{failed_text}: {e}'

    async def base_swap_token_to_eth(
            self,
            tx_contract,
            swap_data,
            swap_info: SwapInfo,
            tx_paramam_have=False,
            test=False
    ):
        failed_text = (f'Failed to swap {swap_info.token_from.title}'
                       f' to {swap_info.token_to.title} via {swap_info.swap_platform.title}')

        try:
            if test:
                print(swap_data)
            token_balance = await self.client.wallet.balance(token=swap_info.token_from.address)

            if not token_balance.Wei:
                msg = (f'{self.client.account.address} |'
                       f' {swap_info.swap_platform.title} | swap_token | insufficient token balance')
                logger.error(msg)

                return msg
            logger.info(
                f'{self.client.account.address} | {swap_info.swap_platform.title}'
                f' | swap_token | amount: {token_balance.Ether}')

            if not await self.approve_interface(
                    token_address=swap_info.token_from.address,
                    spender=tx_contract.address,
                    amount=token_balance
            ):
                msg = f'{failed_text}: token not approved.'
                logger.info(msg)
                return msg

            await asyncio.sleep(random.randint(10, 20))
            if tx_paramam_have:
                tx_params = swap_data
            else:
                gas_price = await self.client.transactions.gas_price(w3=self.client.w3)

                tx_params = {
                    'gasPrice': gas_price.Wei,
                    'from': self.client.account.address,
                    'to': tx_contract.address,
                    'data': swap_data
                }

            receipt, tx_hash = await self.submit_transaction(tx_params)

            if receipt:
                msg = (f'{token_balance.Ether} {swap_info.token_from.title}'
                       f' was swapped to {swap_info.token_to.title} via {swap_info.swap_platform.title}: {tx_hash}')
                check_tx = await self.wait_tx_status(tx_hash=tx_hash)
                if check_tx:
                    logger.success(msg)
                    return msg

            msg = (f'Failed to swap {swap_info.token_from.title}'
                   f' to {swap_info.token_to.title} via {swap_info.swap_platform.title}')
            logger.error(msg)
            return msg

        except BaseException as e:
            logger.error(f'{swap_info.swap_platform.title}.swap_token')
            return f'{failed_text}: {e}'

    async def eth_to_weth(self, amount: TokenAmount):
        failed_text = 'Failed to wrap ETH'

        try:
            logger.info(f'{self.client.account.address} | eth -> weth')
            contract = await self.client.contracts.get(contract_address=Tokens.WETH)
            settings = Settings()
            if not amount:
                amount = Ether(randfloat(
                    from_=settings.eth_amount_for_swap.from_,
                    to_=settings.eth_amount_for_swap.to_,
                    step=0.0000001
                ))

            balance = await self.client.wallet.balance()

            if float(balance.Ether) < float(amount.Ether) + settings.minimal_balance:
                logger.error(f'{self.client.account.address} | Base | eth_to_weth | insufficient eth balance')
                msg = f'{failed_text}: insufficient balance.'
                logger.warning(msg)
                return msg

            gas_price = await self.client.transactions.gas_price(w3=self.client.w3)

            tx_params = {
                'gasPrice': gas_price.Wei,
                'from': self.client.account.address,
                'to': contract.address,
                'data': contract.encodeABI('deposit'),
                'value': amount.Wei
            }
            gas_limit = await self.client.transactions.estimate_gas(w3=self.client.w3, tx_params=tx_params)
            tx_params['gas'] = gas_limit.Wei
            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

            if receipt:
                msg = f'ETH was wrapped: {tx.hash.hex()}'
                logger.success(msg)
                return msg

            return f'{failed_text}!'

        except BaseException as e:
            logger.error('Base.eth_to_weth')
            return f'{failed_text}: {e}'

    async def weth_to_eth(self) -> str:
        failed_text = 'Failed to unwrap ETH'

        try:
            logger.info(f'{self.client.account.address} | weth -> eth')
            weth_balance = await self.client.wallet.balance(token=Tokens.WETH)

            if not weth_balance.Wei:
                logger.error(f'{self.client.account.address} | Base | weth_to_eth | insufficient weth balance')
                return f'{failed_text}: insufficient balance.'

            contract = await self.client.contracts.get(contract_address=Tokens.WETH)
            args = TxArgs(
                wad=weth_balance.Wei
            )
            gas_price = await self.client.transactions.gas_price(w3=self.client.w3)
            tx_params = {
                'from': self.client.account.address,
                'to': contract.address,
                'data': contract.encodeABI('withdraw', args=args.tuple()),
            }

            gas_limit = await self.client.transactions.estimate_gas(w3=self.client.w3, tx_params=tx_params)
            tx_params['gas'] = gas_limit.Wei
            tx = await self.client.transactions.sign_and_send(tx_params=tx_params)
            receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

            if receipt:
                return f'ETH was unwrapped: {tx.hash.hex()}'

            return f'{failed_text}!'

        except BaseException as e:
            logger.error('Base.weth_to_eth')
            return f'{failed_text}: {e}'

    async def approve_interface(self, token_address, spender, amount: Optional[TokenAmount] = None) -> bool:
        logger.info(
            f'{self.client.account.address} | start approve token_address: {token_address} for spender: {spender}'
        )
        balance = await self.client.wallet.balance(token=token_address)

        if balance <= 0:
            logger.error(f'{self.client.account.address} | approve | zero balance')
            return False

        if not amount or amount.Wei > balance.Wei:
            amount = balance

        approved = await self.client.transactions.approved_amount(
            token=token_address,
            spender=spender,
            owner=self.client.account.address
        )

        if amount.Wei <= approved.Wei:
            logger.info(f'{self.client.account.address} | approve | already approved')
            return True

        tx = await self.client.transactions.approve(
            token=token_address,
            spender=spender,
            amount=amount
        )
        receipt = await tx.wait_for_receipt(client=self.client, timeout=300)

        if receipt:
            return True

        return False

    async def get_token_price(self, token_symbol='ETH', default_value=-1) -> Union[int, float]:
        token_symbol = token_symbol.upper()
        params = {
            'fsym': token_symbol,
            'tsyms': 'USD'
        }

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    logger.info(
                        f'{self.client.account.address} | getting {token_symbol} price')
                    async with session.get(
                            f'https://min-api.cryptocompare.com/data/price', params=params
                    ) as r:
                        result_dict = await r.json()
                        if 'HasWarning' in result_dict and not result_dict['HasWarning']:
                            logger.error(
                                f'{self.client.account.address} | getting {token_symbol}'
                                f' price | {result_dict["Message"]}'
                            )
                            return default_value
                        return result_dict['USD']

            except Exception as e:
                logger.error(f'{self.client.account.address} | getting {token_symbol} price: {e}')
                await asyncio.sleep(5)

    async def _get_token_price(self, token_symbol='ETH', default_value=-1) -> Optional[float]:
        token_symbol = token_symbol.upper()

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                            f'https://api.binance.com/api/v3/depth?limit=1&symbol={token_symbol}USDT') as r:

                        if r.status != 200:
                            logger.error(f'code: {r.status} | json: {r.json()}')
                            return None
                        result_dict = await r.json()

                        if 'asks' not in result_dict:
                            logger.error(
                                f'code: {r.status} | json: {r.json()}')
                            return None
                        return float(result_dict['asks'][0][0])

            except Exception as e:
                logger.error(
                    f'getting {token_symbol} price: {e}')

                await asyncio.sleep(5)

    @staticmethod
    async def get_txs_old(account_address: str, offset: int, limit: int = 100,
                          direction: str = 'older') -> Dict[str, Any]:
        params = {
            'limit': limit,
            'direction': direction,
            'accountAddress': account_address,
            'offset': offset
        }

        async with aiohttp.ClientSession() as session:
            async with await session.get('https://zksync2-mainnet-explorer.zksync.io/transactions',
                                         params=params) as r:
                return await r.json()

    @staticmethod
    async def _get_txs(account_address: str, page: int = 1, limit: int = 50, proxy: Optional[str] = None) -> list[dict]:
        settings = Settings()
        url = 'https://www.oklink.com'

        if not 'http://' in proxy:
            proxy = f'http://{proxy}'

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'user-agent': UserAgent().chrome,
            'Ok-Access-Key': settings.oklink_api_key,
        }

        params = {
            'chainShortName': CHAIN_SHORT_NAME,
            'address': account_address,
            'limit': limit,
            'page': page
        }
        async with aiohttp.ClientSession() as session:
            async with await session.get(
                    url + '/api/v5/explorer/address/transaction-list',
                    params=params,
                    headers=headers,
                    proxy=proxy
            ) as r:
                return (await r.json())['data'][0]['transactionLists']

    @staticmethod
    async def get_txs(account_address: str, proxy: Optional[str] = None) -> list[dict]:
        page = 1
        limit = 50
        txs_lst = []
        txs = await Base._get_txs(account_address=account_address, page=page, limit=limit, proxy=proxy)
        txs_lst += txs
        while len(txs) == limit:
            page += 1
            txs = await Base._get_txs(account_address=account_address, page=page, limit=limit, proxy=proxy)
            txs_lst += txs
        return txs_lst

    async def find_txs(
            self,
            to: str,
            function_name: str,
            txs: Optional[list[dict]] = None,
            status: tuple[str] = ('included', 'verified')
    ) -> list:

        if not txs:
            txs = await Base.get_txs(account_address=self.client.account.address, proxy=self.client.proxy)
        result_txs = []
        for tx in txs:
            if (
                    tx and
                    'state' in tx and
                    tx['state'] == 'success' and
                    # strtime_to_unix(
                    #     strtime=received_at, format='%Y-%m-%dT%H:%M'
                    # ) >= settings.txs_after_timestamp and
                    # 'data' in tx and
                    # 'contractAddress' in tx['data'] and
                    'to' in tx and tx['to'].lower() == to.lower() and
                    # tx['data']['contractAddress'].lower() == to.lower() and
                    # 'calldata' in tx['data'] and
                    # tx['data']['calldata'].lower()[:10] == function_name.lower()
                    'methodId' in tx and tx['methodId'].lower() == function_name.lower()
            ):
                result_txs.append(tx)
        return result_txs

    @staticmethod
    async def find_tx_by_method_id(client: Client, address: str, to: str, method_id: str):
        txs = {}
        coin_txs = (await client.network.api.functions.account.txlist(address))['result']
        for tx in coin_txs:
            if tx.get('isError') == '0' and tx.get('to') == to.lower() and method_id in tx.get('methodId'):
                txs[tx.get('hash')] = tx
        return txs

    @staticmethod
    async def get_max_priority_fee_per_gas(w3: Web3, block: dict) -> int:
        block_number = block['number']
        latest_block_transaction_count = w3.eth.get_block_transaction_count(block_number)
        max_priority_fee_per_gas_lst = []

        for i in range(latest_block_transaction_count):
            try:
                transaction = w3.eth.get_transaction_by_block(block_number, i)
                if 'maxPriorityFeePerGas' in transaction:
                    max_priority_fee_per_gas_lst.append(transaction['maxPriorityFeePerGas'])

            except Exception:
                continue

        if not max_priority_fee_per_gas_lst:
            max_priority_fee_per_gas = w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_lst.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_lst[len(max_priority_fee_per_gas_lst) // 2]

        return max_priority_fee_per_gas

    @staticmethod
    async def get_base_fee(w3: Web3, increase_gas: float = 1.):
        last_block = await w3.eth.get_block('latest')
        return int(last_block['baseFeePerGas'] * increase_gas)

    @staticmethod
    async def get_max_fee_per_gas(w3: Web3, max_priority_fee_per_gas: Unit) -> Wei:
        base_fee = await Base.get_base_fee(w3=w3)
        # print('base_fee', base_fee)
        return Wei(base_fee + max_priority_fee_per_gas.Wei)

    @staticmethod
    async def send_transaction(
            client: Client,
            private_key: str,
            to: str,
            data,
            from_=None,
            increase_gas=1.1,
            value=None,
            max_priority_fee_per_gas: Optional[int] = None,
            max_fee_per_gas: Optional[int] = None
    ):
        if not from_:
            from_ = client.account.address

        tx_params = {
            'chainId': await client.w3.eth.chain_id,
            'nonce': await client.w3.eth.get_transaction_count(client.account.address),
            'from': Web3.to_checksum_address(from_),
            'to': Web3.to_checksum_address(to),
            'data': data,
        }

        if client.network.tx_type == 2:
            w3 = Web3(provider=Web3.HTTPProvider(endpoint_uri=client.network.rpc))
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            last_block = w3.eth.get_block('latest')

            if not max_priority_fee_per_gas:
                max_priority_fee_per_gas = await Base.get_max_priority_fee_per_gas(w3=w3, block=last_block)

            if not max_fee_per_gas:
                base_fee = int(last_block['baseFeePerGas'] * 1.125)
                max_fee_per_gas = base_fee + max_priority_fee_per_gas
            tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            tx_params['maxFeePerGas'] = max_fee_per_gas

        else:
            tx_params['gasPrice'] = await client.w3.eth.gas_price

        if value:
            tx_params['value'] = value

        try:
            tx_params['gas'] = int(await client.w3.eth.estimate_gas(tx_params) * increase_gas)
        except Exception as err:
            logger.error(
                f'{client.account.address} | Transaction failed | {err}')
            return None

        sign = client.w3.eth.account.sign_transaction(tx_params, private_key)
        return await client.w3.eth.send_raw_transaction(sign.rawTransaction)

    def get_session(self):
        if self.client.proxy:
            return ProxyConnector.from_url(self.client.proxy)
        return None

    async def get_token_list(self,
                             account_address: str,
                             page: int = 1,
                             limit: int = 50,
                             protocol_type: str = 'token_20'):
        settings = Settings()
        headers = {'Ok-Access-Key': settings.oklink_api_key}
        async with aiohttp.ClientSession() as session:
            try:
                params = {
                    'chainShortName': CHAIN_SHORT_NAME,
                    'address': account_address,
                    'limit': limit,
                    'page': page,
                    'protocolType': protocol_type
                }

                async with await session.get(
                        f'{OKLINK_URL}/api/v5/explorer/address/token-balance',
                        params=params,
                        headers=headers,
                ) as response:
                    result = await response.json()
                    if response.status == 200:
                        pages = result['data'][0]['totalPage']
                        token_list = result['data'][0]['tokenList']
                        return int(pages), token_list
                    elif response.status == 429:
                        logger.warning(f'{account_address} | повторная попытка список токенов и транзакций')
                        await asyncio.sleep(15)
                        return await self.get_token_list(account_address, page, limit, protocol_type)
                    else:
                        raise NoApiKeyFound("Please check if you have OkLink API key in files/settings.json")
            except GetOKlinkTokenBalanceError:
                raise GetOKlinkTokenBalanceError("Unable to get balances from OKLINK")

    async def filter_tokens(self,
                            token_list,
                            token_balances,
                            exclude_tickers: list,
                            token=True
                            ) -> dict:
        filtered_tokens = {}
        # for my_token in token_balances:
        #     for usable_token in token_list:
        #         if (my_token['tokenContractAddress'].lower() == usable_token.address.lower()
        #                 and my_token['symbol'] != exclude_tickers):
        #             if token and float(my_token['valueUsd']) > 0.1:  # checking if USD value if greater than 0.1$
        #                 filtered_tokens.append(usable_token)
        #             if not token:  # applicable to LP's and Lending tokens
        #                 if float(my_token['holdingAmount']) >= usable_token.min_value:
        #                     filtered_tokens.append(usable_token)
        # REWROTE for dict return

        # TODO add WETH balance check
        for my_token in token_balances:
            for usable_token in token_list:
                if (my_token['tokenContractAddress'].lower() == usable_token.address.lower()
                        and my_token['symbol'] not in exclude_tickers):
                    if token and float(my_token['valueUsd']) > 0.1:
                        filtered_tokens[usable_token] = Ether(my_token['holdingAmount'])  # Token class : Ether(balance)
                    if not token:  # applicable to LP's and Lending tokens
                        if float(my_token['holdingAmount']) >= usable_token.min_value:
                            filtered_tokens[usable_token] = Ether(my_token['holdingAmount'])

        return filtered_tokens

    async def get_all_tokens(self, account_address: str, exclude_tickers: list = []) -> tuple[dict, dict, dict]:
        results = []
        page = 1

        while True:
            pages, result = await self.get_token_list(account_address, page)
            results += result

            if pages == 0 or page == pages:
                break

            page += 1
        tokens = await self.filter_tokens(Tokens.get_token_list(), results, exclude_tickers=exclude_tickers, token=True)
        lending = await self.filter_tokens(Lending_Tokens.get_token_list(), results, token=False,
                                           exclude_tickers=exclude_tickers)
        lp = await self.filter_tokens(Liquidity_Tokens.get_token_list(), results, token=False,
                                      exclude_tickers=exclude_tickers)
        return tokens, lending, lp,

    async def wait_tx_status(self, tx_hash: HexBytes, max_wait_time=100) -> bool:
        start_time = time.time()
        while True:
            try:
                receipts = await self.client.w3.eth.get_transaction_receipt(tx_hash)
                status = receipts.get("status")
                if status == 1:
                    return True
                elif status is None:
                    await asyncio.sleep(0.3)
                else:
                    return False
            except TransactionNotFound:
                if time.time() - start_time > max_wait_time:
                    logger.exception(f'{self.client.account.address} получил неудачную транзакцию')
                    return False
                await asyncio.sleep(3)

    async def get_chain_to_transfer_with_balance(self):
        settings = Settings()
        chains = self.get_activate_chain()
        chains_with_suff_balance = []
        min_balances = settings.chains_min_balances

        for chain in chains:
            client = Client(private_key=self.client.account.key, network=chain, proxy=self.client.proxy)
            balance = await client.wallet.balance()
            if balance.Ether > min_balances[chain.name] and self.client.network.name != chain.name:
                chains_with_suff_balance.append(chain)

        if not chains_with_suff_balance:
            return 'No chains with balance (base)'

        chain = random.choice(chains_with_suff_balance)

        return chain

    def get_activate_chain(self):
        settings = Settings()
        chains = [Networks.Polygon, Networks.Celo, Networks.Base, Networks.Optimism,
                  Networks.Avalanche, Networks.BSC, Networks.Moonbeam]
        activate_chain = [chain for chain in chains if settings.destination_chains[chain.name]]
        return activate_chain
