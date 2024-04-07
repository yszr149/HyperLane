import logging
import random
import asyncio

from loguru import logger
from libs.py_eth_async.data.models import TxArgs

from tasks.base import Base
from data.models import Tokens, Routers, Network


#  Made by Toby
class MerklyHMerk(Base):
    NAME = 'Mint and Bridge hMERK'

    CONTRACT_MAP = {
        'polygon': Routers.MERKLY_POLYGON_hFT,
        'base': Routers.MERKLY_BASE_hFT,
        'optimism': Routers.MERKLY_OPTIMISM_hFT,
        'moonbeam': Routers.MERKLY_MOONBEAM_hFT,
        'celo': Routers.MERKLY_CELO_hFT,
        'arbitrum': Routers.MERKLY_ARBITRUM_hFT,
        'bsc': Routers.MERKLY_BSC_hFT
    }

    async def _get_fee_mint(self, contract):
        fee = await contract.functions.fee().call()
        return fee

    async def mint(self):
        failed_text = f'Failed mint hMERK via Merkly'
        chain_name = self.client.network.name

        logger.info(f'Starting to mint hMERK on {chain_name}')

        contract = await self.client.contracts.get(self.CONTRACT_MAP[chain_name])
        fee = await self._get_fee_mint(contract=contract)
        logger.info(f'Success get fee for mint')

        amount = random.randint(1, 1)
        params = TxArgs(
            user=self.client.account.address,
            amount=amount,
        )

        tx_params = {
            'from': self.client.account.address,
            'to': contract.address,
            'data': contract.encodeABI('mint', args=params.tuple()),
            'value': fee
        }

        receipt, tx_hash = await self.submit_transaction(tx_params)
        if receipt:
            check_tx = await self.wait_tx_status(tx_hash=tx_hash)
            if check_tx:
                return f'{amount} hMERK was minted via Merkly {tx_hash}'
        return f'{failed_text}!'

    async def _get_fee_bridge(self, contract, domain: int):
        fee = await contract.functions.quoteBridge(_destination=domain).call()
        return fee

    async def bridge(self, dest_chain: Network):
        failed_text = f'Failed bridge hMERK via Merkly'
        logger.info(f'Starting bridge hMERK from {self.client.network.name} to {dest_chain.name}')

        token = self.CONTRACT_MAP[self.client.network.name]

        contract = await self.client.contracts.get(token)
        fee = await self._get_fee_bridge(contract=contract, domain=dest_chain.chain_id)
        logger.info(f'Success get fee for bridge')

        amount = await self.client.wallet.balance(token.address)

        args = TxArgs(
            _destination=dest_chain.chain_id,
            _Id=amount.Wei,
        )

        tx_params = {
            'from': self.client.account.address,
            'to': token.address,
            'data': contract.encodeABI('bridgeHFT', args=args.tuple()),
            'value': fee
        }

        receipt, tx_hash = await self.submit_transaction(tx_params)
        if receipt:
            check_tx = await self.wait_tx_status(tx_hash=tx_hash)
            if check_tx:
                return f'hFT was bridged via Merkly {tx_hash}'
        return f'{failed_text}!'

    async def mint_and_bridge_token(self):
        dest_chain = await self.get_chain_to_transfer_with_balance()

        if isinstance(dest_chain, str):
            return 'No chains with balance'
        dest_chain: Network

        failed_text = f'Failed mint and bridge from {self.client.network.name} to {dest_chain.name}'
        try:
            token_balance = await self.client.wallet.balance((self.CONTRACT_MAP[self.client.network.name]).address)

            if not token_balance.Ether:
                res = await self.mint()
                if 'Failed' in res:
                    return 'Failed mint, check mint function'
                logger.info(res)

            await asyncio.sleep(random.randint(8, 20))

            res = await self.bridge(dest_chain=dest_chain)
            if 'Failed' in res:
                return 'Failed, bridge hMERK via Merkly'
            logger.info(res)

            return 'Success mint and bridge hMERK via Merkly'

        except BaseException as e:
            logging.exception(f'Merkly.mint-bridge_hMERK: {Tokens.hMERK.title}')
            return f'{failed_text}: {e}'
