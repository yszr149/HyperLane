import logging
import random
import asyncio

from libs.py_eth_async.data.models import TxArgs

from loguru import logger

from tasks.base import Base
from data.models import Tokens, Routers, Network


#  Made by Toby
class MerklyHNFT(Base):
    NAME = 'Mint and Bridge hNFT'

    CONTRACT_MAP = {
        'polygon': Routers.MERKLY_POLYGON_hNFT,
        'base': Routers.MERKLY_BASE_hNFT,
        'optimism': Routers.MERKLY_OPTIMISM_hNFT,
        'moonbeam': Routers.MERKLY_MOONBEAM_hNFT,
        'celo': Routers.MERKLY_CELO_hNFT,
        'arbitrum': Routers.MERKLY_ARBITRUM_hNFT,
        'bsc': Routers.MERKLY_BSC_hNFT
    }

    async def _get_fee_mint(self, contract):
        fee = await contract.functions.fee().call()
        return fee

    async def mint(self):
        failed_text = f'Failed mint hNFT via Merkly'
        chain_name = self.client.network.name

        logger.info(f'Starting to mint hNFT on {chain_name}')

        contract = await self.client.contracts.get(self.CONTRACT_MAP[chain_name])
        fee = await self._get_fee_mint(contract=contract)
        logger.info(f'Success get fee for mint hNFT')

        amount = 1
        params = TxArgs(
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
                return f'{amount} hNFT was minted via Merkly {tx_hash}'
        return f'{failed_text}!'

    async def _get_fee_bridge(self, contract, domain: int):
        fee = await contract.functions.quoteBridge(_destination=domain).call()
        return fee

    async def bridge(self, dest_chain: Network):
        failed_text = f'Failed bridge hNFT via Merkly'
        logger.info(f'Starting bridge hNFT from {self.client.network.name} to {dest_chain.name}')

        nft = self.CONTRACT_MAP[self.client.network.name]
        contract = await self.client.contracts.get(nft)

        fee = await self._get_fee_bridge(contract=contract, domain=dest_chain.chain_id)
        logger.info(f'Success get fee for bridge')

        balance_nft = await contract.functions.balanceOf(self.client.account.address).call()
        if not balance_nft:
            return f'{failed_text} | No NFT after mint via Merkly'

        id_last_nft = await contract.functions.tokenOfOwnerByIndex(owner=self.client.account.address,
                                                                   index=balance_nft - 1).call()
        args = TxArgs(
            _destination=dest_chain.chain_id,
            _Id=id_last_nft,
        )

        tx_params = {
            'from': self.client.account.address,
            'to': nft.address,
            'data': contract.encodeABI('bridgeNFT', args=args.tuple()),
            'value': fee
        }

        receipt, tx_hash = await self.submit_transaction(tx_params)
        if receipt:
            check_tx = await self.wait_tx_status(tx_hash=tx_hash)
            if check_tx:
                return f'hNFT was bridged via Merkly {tx_hash}'
        return f'{failed_text}!'


    async def mint_and_bridge_nft(self):
        dest_chain = await self.get_chain_to_transfer_with_balance()

        if isinstance(dest_chain, str):
            return 'No chains with balance'
        dest_chain: Network

        failed_text = f'Failed mint and bridge hNFT from {self.client.network.name} to {dest_chain.name}'
        try:

            res = await self.mint()
            if 'Failed' in res:
                return 'Failed mint hNFT, check mint function via Merkly'
            logger.info(res)

            await asyncio.sleep(random.randint(8, 20))

            res = await self.bridge(dest_chain=dest_chain)
            if 'Failed' in res:
                return 'Failed mint hNFT via Merkly'
            logger.info(res)

            return 'Success mint and bridge hNFT via Merkly'

        except BaseException as e:
            logging.exception(f'Merkly.mint-bridge_NFT: {Tokens.hMERK.title}')
            return f'{failed_text}: {e}'

