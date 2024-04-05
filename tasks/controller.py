from typing import Optional
from libs.py_eth_async.client import Client

# from data.models import Tokens, Liquidity_Tokens, Lending_Tokens, Pools
from utils.db_api.models import Wallet
from tasks.base import Base

from data.models import Routers, Lending_Tokens


from tasks.merkly_ft import MerklyHMerk
from tasks.merkly_nft import MerklyHNFT


class Controller(Base):
    def __init__(self, client: Client):
        super().__init__(client)

        self.h_merk = MerklyHMerk(client=client)
        self.h_nft = MerklyHNFT(client=client)

    async def get_activity_count(self, wallet: Wallet = None):
        # TODO get all activity
        txs = await Base.get_txs(account_address=self.client.account.address, proxy=wallet.proxy)
        tx_total = len(txs)
        h_mekr_bridge = await self.count_h_mekr_bridge(txs)
        h_nft_bridge = await self.count_h_nft_bridge(txs)
        return tx_total, h_mekr_bridge, h_nft_bridge

    # TODO CALCULATION IS SHIT ASK ED. Each CHAIN Must be checked
    async def count_h_mekr_bridge(self, txs: Optional[list[dict]] = None, wallet: Wallet = None) -> int:
        result_count = 0
        if not txs:
            txs = await Base.get_txs(account_address=self.client.account.address, proxy=wallet.proxy)

        result_count += len(await self.find_txs(
            to=Routers.MERKLY_POLYGON_hFT.address,
            function_name='0xf3931d5d',
            txs=txs
        ))

        result_count += len(await self.find_txs(
            to=Routers.MERKLY_BSC_hFT.address,
            function_name='0x40c10f19',
            txs=txs
        ))

        return result_count

    async def count_h_nft_bridge(self, txs: Optional[list[dict]] = None, wallet: Wallet = None) -> int:
        result_count = 0

        if not txs:
            txs = await Base.get_txs(account_address=self.client.account.address, proxy=wallet.proxy)

        result_count += len(await self.find_txs(
            to=Routers.MERKLY_POLYGON_hNFT.address,
            function_name='0xf5c358c6',
            txs=txs
        ))

        return result_count