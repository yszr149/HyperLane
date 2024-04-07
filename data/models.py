import random
import inspect

from dataclasses import dataclass
from typing import Union, Optional
from decimal import Decimal
from eth_utils import to_wei, from_wei

from libs.py_okx_async.models import OKXCredentials, BinanceCredentials
from libs.pretty_utils.miscellaneous.files import read_json
from libs.py_eth_async.data.models import Network, Networks, GWei, RawContract
from libs.pretty_utils.type_functions.classes import AutoRepr, Singleton, ArbitraryAttributes
from data.config import ABIS_DIR
from libs.py_eth_async.data.models import DefaultABIs
from data.config import SETTINGS_FILE


class ProgramActions:
    ImportWallets = ArbitraryAttributes(Selection=1)
    # ExportWallets = ArbitraryAttributes(Selection=2)
    # OKXWithdrawal = ArbitraryAttributes(Selection=3)
    StartScript = ArbitraryAttributes(Selection=2)
    # CheckBalance = ArbitraryAttributes(Selection=5)


@dataclass
class FromTo:
    from_: Union[int, float]
    to_: Union[int, float]


class BaseContract(RawContract):
    def __init__(self,
                 title,
                 address,
                 abi,
                 min_value: Optional[float] = 0,
                 stable: Optional[bool] = False,
                 belongs_to: Optional[str] = "",
                 decimals: Optional[int] = 18,
                 token_out_name: Optional[str] = '',
                 ):
        super().__init__(address, abi)
        self.title = title
        self.min_value = min_value
        self.stable = stable
        self.belongs_to = belongs_to  # Имя помойки например AAVE
        self.decimals = decimals
        self.token_out_name = token_out_name


class SwapInfo:
    def __init__(self, token_from: BaseContract, token_to: BaseContract, swap_platform: BaseContract):
        self.token_from = token_from
        self.token_to = token_to
        self.swap_platform = swap_platform


class OkxModel:
    withdraw_amount: FromTo
    delay_between_withdrawals: FromTo
    credentials: OKXCredentials


class BinaceModel:
    withdraw_amount: FromTo
    delay_between_withdrawals: FromTo
    credentials: BinanceCredentials


class WorkStatuses:
    NotStarted = 'not started'
    Withdrawn = 'withdrawn'
    Bridged = 'bridged'
    # Filled = 'filled'
    Initial = 'initial'
    Activity = 'activity'


@dataclass
class BinanceCredentials:
    """
    An instance that contains OKX API key data.

    Attributes:
        api_key (str): an API key.
        secret_key (str): a secret key.
        passphrase (str): a passphrase.

    """
    api_key: str
    secret_key: str

    def completely_filled(self) -> bool:
        """
        Check if all required attributes are specified.

        Returns:
            bool: True if all required attributes are specified.

        """
        return all((self.api_key, self.secret_key))


class BinanceModel:
    required_minimum_balance: float
    withdraw_amount: FromTo
    delay_between_withdrawals: FromTo
    credentials: BinanceCredentials


class Settings(Singleton, AutoRepr):
    def __init__(self):
        json = read_json(path=SETTINGS_FILE)
        self.use_private_key_encryption = json['use_private_key_encryption']
        self.maximum_gas_price: GWei = GWei(json['maximum_gas_price'])
        self.oklink_api_key = json['oklink_api_key']
        self.okx = OkxModel()
        self.okx.withdraw_amount = FromTo(
            from_=json['okx']['withdraw_amount']['from'],
            to_=json['okx']['withdraw_amount']['to'],
        )
        self.okx.required_minimum_balance = json['okx']['required_minimum_balance']
        self.okx.credentials = OKXCredentials(
            api_key=json['okx']['credentials']['api_key'],
            secret_key=json['okx']['credentials']['secret_key'],
            passphrase=json['okx']['credentials']['passphrase']
        )
        self.binance = BinanceModel()
        self.binance.credentials = BinanceCredentials(
            api_key=json['binance']['credentials']['api_key'],
            secret_key=json['binance']['credentials']['secret_key'],
        )
        self.initial_actions_delay: FromTo = FromTo(
            from_=json['initial_actions_delay']['from'], to_=json['initial_actions_delay']['to']
        )
        self.h_mekr: FromTo = FromTo(from_=json['h_mekr']['from'], to_=json['h_mekr']['to'])
        self.h_nft: FromTo = FromTo(from_=json['h_nft']['from'], to_=json['h_nft']['to'])
        self.hFT_amount_for_mint_and_bridge: FromTo = FromTo(
            from_=json['hFT_amount_for_mint_and_bridge']['from'], to_=json['hFT_amount_for_mint_and_bridge']['to']
        )
        self.source_chains = json['source_chains']
        self.destination_chains = json['destination_chains']
        self.chains_min_balances = json['chains_min_balances']
        self.withdrawal_networks = json['withdrawal_networks']
        self.withdrawal_amounts = json['withdrawal_amounts']



settings = Settings()

class Routers(Singleton):
    """
    An instance with router contracts
        variables:
            ROUTER: BaseContract
            ROUTER.title = any
    """
    # hFT
    MERKLY_POLYGON_hFT = BaseContract(
        title='MINT_CONTRACT', address='0x574E69C50e7D13B3d1B364BF0D48285A5aE2dF56',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_BASE_hFT = BaseContract(
        title='MINT_CONTRACT', address='0x5454cF5584939f7f884e95DBA33FECd6D40B8fE2',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_SCROLL_hFT = BaseContract(
        title='MINT_CONTRACT', address='0x904550e0D182cd4aEe0D305891c666a212EC8F01',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_OPTIMISM_hFT = BaseContract(
        title='MINT_CONTRACT', address='0x32F05f390217990404392a4DdAF39D31Db4aFf77',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_MOONBEAM_hFT = BaseContract(
        title='MINT_CONTRACT', address='0xf3D41b377c93fA5C3b0071966f1811c5063fAD40',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_CELO_hFT = BaseContract(
        title='MINT_CONTRACT', address='0xad8676147360dBc010504aB69C7f1b1877109527',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_ARBITRUM_hFT = BaseContract(
        title='MINT_CONTRACT', address='0xFD34afDFbaC1E47aFC539235420e4bE4A206f26D',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )
    MERKLY_BSC_hFT = BaseContract(
        title='MINT_CONTRACT', address='0x7b4f475d32f9c65de1834A578859F9823bE3c5Cf',
        abi=read_json(path=(ABIS_DIR, 'merkly_ft.json'))
    )


    # hNFT
    MERKLY_POLYGON_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x7daC480d20f322D2ef108A59A465CCb5749371c4',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_BASE_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x7dac480d20f322d2ef108a59a465ccb5749371c4',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_SCROLL_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x7daC480d20f322D2ef108A59A465CCb5749371c4',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_OPTIMISM_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x2a5c54c625220cb2166C94DD9329be1F8785977D',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_MOONBEAM_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x7daC480d20f322D2ef108A59A465CCb5749371c4',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_CELO_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x7f4CFDf669d7a5d4Adb05917081634875E21Df47',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_ARBITRUM_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0x7daC480d20f322D2ef108A59A465CCb5749371c4',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )
    MERKLY_BSC_hNFT = BaseContract(
        title='MINT_CONTRACT', address='0xf3D41b377c93fA5C3b0071966f1811c5063fAD40',
        abi=read_json(path=(ABIS_DIR, 'merkly_nft.json'))
    )


class Tokens(Singleton):
    """
    An instance with token contracts
        variables:
            TOKEN: BaseContract
            TOKEN.title = symbol from OKLINK
    """
    # ETH = BaseContract(
    #     title='ETH', address='0x0000000000000000000000000000000000000000',
    #     abi=DefaultABIs.Token,
    #     token_out_name="ETH",
    # )

    hMERK = BaseContract(
        title='hMERK', address='0x904550e0D182cd4aEe0D305891c666a212EC8F01',
        abi=DefaultABIs.Token,
        belongs_to='Merkly Hyperlane FT',
        decimals=18
    )

    @staticmethod
    def get_token_list():
        return [
            value for name, value in inspect.getmembers(Tokens)
            if isinstance(value, BaseContract)
        ]


class Pools(Singleton):
    """
        An instance with pool contracts
            variables:
                POOL: BaseContract
                POOL.TITLE = any
    """
    # SYNCSWAP_WETH_USDC = BaseContract(
    #     title='USDC/WETH cSLP', address='0x814a23b053fd0f102aeeda0459215c2444799c70',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='Scroll',
    #     token_out_name='USDC',
    #     decimals=18
    # )
    # SYNCSWAP_WETH_WBTC = BaseContract(
    #     title='WBTC/WETH cSLP', address='0x914995cB63da121F14d51BC094CA72fC967b1F46',
    #     abi=DefaultABIs.Token,
    #     belongs_to='Scroll',
    #     token_out_name='WBTC'
    # )
    # SYNCSWAP_WETH_USDT = BaseContract(
    #     title='WETH/USDT cSLP', address='0x78ea8E533c834049dE625e05F0B4DeFfe9DB5f6e',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='Scroll',
    #     token_out_name='USDT',
    #     decimals=18
    # )
    # SYNCSWAP_WETH_DAI = BaseContract(
    #     title='WETH/DAI cSLP', address='0xB39880C7a0B752179d6D7d9Ae594Ab4C02d6E5b8',
    #     abi=DefaultABIs.Token,
    #     belongs_to='Scroll',
    #     token_out_name='DAI'
    # )
    #
    # SYNCSWAP_USDC_USDT = BaseContract(  # COPY
    #     title='USDC/USDT sSLP', address='0x2076d4632853FB165Cf7c7e7faD592DaC70f4fe1',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='Scroll',
    #     token_out_name='USD stable sSLP',
    #     decimals=18
    # )


class Lending_Tokens(Singleton):
    """
        An instance with lending contracts
            variables:
                LENDING_TOKEN: BaseContract
                LENDING_TOKEN.title = symbol from Oklink
    """

    # lETH = BaseContract(
    #     title='lETH', address='0x274C3795dadfEbf562932992bF241ae087e0a98C',
    #     abi=DefaultABIs.Token,
    #     token_out_name="ETH",
    #     decimals=18,
    #     belongs_to='LayerBank'
    # )
    # mETH = BaseContract(
    #     title='mETH', address='0xb21EA1d83197C766f7258d16a33F64d16ee06681',
    #     abi=DefaultABIs.Token,
    #     token_out_name="ETH",
    #     decimals=18,
    #     belongs_to='Meow'
    # )
    # mUSDC = BaseContract(
    #     title='mUSDC', address='0x6919384b81A0b59740FD467761375a06FB8Ba80E',
    #     abi=DefaultABIs.Token,
    #     token_out_name="USDC",
    #     decimals=18,
    #     belongs_to='Meow'
    # )
    # mDAI = BaseContract(
    #     title='mDAI', address='0xe90e84c81C2636Ac759A4E8d96A217b6710b8204',
    #     abi=DefaultABIs.Token,
    #     token_out_name="DAI",
    #     decimals=18,
    #     belongs_to='Meow'
    # )
    #
    # aScrWETH = BaseContract(
    #     title="aScrWETH", address='0xf301805be1df81102c957f6d4ce29d2b8c056b2a',
    #     abi=read_json(path=(ABIS_DIR, 'WETH.json')),
    #     min_value=0.0001,
    #     belongs_to='AAVE',
    #     token_out_name='ETH',
    #     decimals=18
    # )
    # aScrUSDC = BaseContract(
    #     title="aScrUSDC", address='0x1D738a3436A8C49CefFbaB7fbF04B660fb528CbD',
    #     abi=DefaultABIs.Token,
    #     belongs_to='AAVE',
    #     token_out_name='USDC',
    #     decimals=6
    # )

    @staticmethod
    def get_token_list():
        return [
            value for name, value in inspect.getmembers(Lending_Tokens)
            if isinstance(value, BaseContract)
        ]


class Liquidity_Tokens(Singleton):
    """
        An instance with LP contracts
            variables:
                LP_TOKEN: BaseContract
                LP_TOKEN.title = symbol from Oklink
     """

    # # LP_INSTANCE = BaseContract(
    # #     title='TITLE_FROM_OKLIMK', address='0x', abi=read_json(path=(ABIS_DIR, 'example.json'))
    # # )
    #
    # SYNCSWAP_WETH_USDC = BaseContract(
    #     title='USDC/WETH cSLP', address='0x814a23b053fd0f102aeeda0459215c2444799c70',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='SyncSwapLiquidity',
    #     token_out_name='USDC',
    #     decimals=18
    # )
    # SYNCSWAP_WETH_WBTC = BaseContract(
    #     title='WBTC/WETH cSLP', address='0x914995cB63da121F14d51BC094CA72fC967b1F46',
    #     abi=DefaultABIs.Token,
    #     belongs_to='SyncSwapLiquidity',
    #     token_out_name='WBTC'
    # )
    # SYNCSWAP_WETH_USDT = BaseContract(
    #     title='WETH/USDT cSLP', address='0x78ea8E533c834049dE625e05F0B4DeFfe9DB5f6e',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='SyncSwapLiquidity',
    #     token_out_name='USDT',
    #     decimals=18
    # )
    # SYNCSWAP_WETH_DAI = BaseContract(
    #     title='WETH/DAI cSLP', address='0xB39880C7a0B752179d6D7d9Ae594Ab4C02d6E5b8',
    #     abi=DefaultABIs.Token,
    #     belongs_to='SyncSwapLiquidity',
    #     token_out_name='DAI'
    # )
    #
    # SYNCSWAP_USDC_USDT = BaseContract(  # COPY
    #     title='USDC/USDT sSLP', address='0x2076d4632853FB165Cf7c7e7faD592DaC70f4fe1',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='SyncSwapLiquidity',
    #     token_out_name='USD stable sSLP',
    #     decimals=18
    # )
    #
    # SPACE_FI_ETH_USDC = BaseContract(
    #     title='nSLP', address='0x6905c59be1a7ea32d1f257e302401ec9a1401c52',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     # abi=read_json(path=(ABIS_DIR, 'space_fi.json')),
    #     belongs_to='SpaceFiLiquidity',
    #     token_out_name='USDC',
    #     decimals=18
    # )
    # SPACE_FI_ETH_USDT = BaseContract(
    #     title='nSLP', address='0x33c00e5E2Cf3F25E7c586a1aBdd8F636037A57a0',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='SpaceFiLiquidity',
    #     token_out_name='USDT',
    #     decimals=18
    # )
    # SPACE_FI_ETH_DAI = BaseContract(
    #     title='nSLP', address='0x6b39911E2FeC73a995B1Db414E9E948d17b53c6d',
    #     abi=read_json(path=(ABIS_DIR, 'sync_swap_liquidity.json')),
    #     belongs_to='SpaceFiLiquidity',
    #     token_out_name='DAI',
    #     decimals=18
    # )

    @staticmethod
    def get_token_list():
        return [
            value for name, value in inspect.getmembers(Liquidity_Tokens)
            if isinstance(value, BaseContract)
        ]


class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        """
        A token amount instance.

        :param Union[int, float, str, Decimal] amount: an amount
        :param int decimals: the decimals of the token (18)
        :param bool wei: the 'amount' is specified in Wei (False)
        """
        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals

        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

        self.decimals = decimals


unit_denominations = {
    'wei': 10 ** -18,
    'kwei': 10 ** -15,
    'mwei': 10 ** -12,
    'gwei': 10 ** -9,
    'szabo': 10 ** -6,
    'finney': 10 ** -3,
    'ether': 1,
    'kether': 10 ** 3,
    'mether': 10 ** 6,
    'gether': 10 ** 9,
    'tether': 10 ** 12,
}


class Unit(AutoRepr):
    """
    An instance of an Ethereum unit.

    Attributes:
        unit (str): a unit name.
        decimals (int): a number of decimals.
        Wei (int): the amount in Wei.
        KWei (Decimal): the amount in KWei.
        MWei (Decimal): the amount in MWei.
        GWei (Decimal): the amount in GWei.
        Szabo (Decimal): the amount in Szabo.
        Finney (Decimal): the amount in Finney.
        Ether (Decimal): the amount in Ether.
        KEther (Decimal): the amount in KEther.
        MEther (Decimal): the amount in MEther.
        GEther (Decimal): the amount in GEther.
        TEther (Decimal): the amount in TEther.

    """
    unit: str
    decimals: int
    Wei: int
    KWei: Decimal
    MWei: Decimal
    GWei: Decimal
    Szabo: Decimal
    Finney: Decimal
    Ether: Decimal
    KEther: Decimal
    MEther: Decimal
    GEther: Decimal
    TEther: Decimal

    def __init__(self, amount: Union[int, float, str, Decimal], unit: str) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.
            unit (str): a unit name.

        """
        self.unit = unit
        self.decimals = 18
        self.Wei = to_wei(amount, self.unit)
        self.KWei = from_wei(self.Wei, 'kwei')
        self.MWei = from_wei(self.Wei, 'mwei')
        self.GWei = from_wei(self.Wei, 'gwei')
        self.Szabo = from_wei(self.Wei, 'szabo')
        self.Finney = from_wei(self.Wei, 'finney')
        self.Ether = from_wei(self.Wei, 'ether')
        self.KEther = from_wei(self.Wei, 'kether')
        self.MEther = from_wei(self.Wei, 'mether')
        self.GEther = from_wei(self.Wei, 'gether')
        self.TEther = from_wei(self.Wei, 'tether')

    def __add__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(self.Wei + other.Wei)

        elif isinstance(other, int):
            return Wei(self.Wei + other)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei + GWei(other).GWei)

            else:
                return Ether(self.Ether + Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __radd__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(other.Wei + self.Wei)

        elif isinstance(other, int):
            return Wei(other + self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei + self.GWei)

            else:
                return Ether(Ether(other).Ether + self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __sub__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(self.Wei - other.Wei)

        elif isinstance(other, int):
            return Wei(self.Wei - other)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei - GWei(other).GWei)

            else:
                return Ether(self.Ether - Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __rsub__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return Wei(other.Wei - self.Wei)

        elif isinstance(other, int):
            return Wei(other - self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei - self.GWei)

            else:
                return Ether(Ether(other).Ether - self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __mul__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(self.Ether)) * Decimal(str(other.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(self.Wei * other.Wei / denominations)

        elif isinstance(other, int):
            return Wei(self.Wei * other)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei * GWei(other).GWei)

            else:
                return Ether(self.Ether * Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __rmul__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(other.Ether)) * Decimal(str(self.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(other.Wei * self.Wei / denominations)

        elif isinstance(other, int):
            return Wei(other * self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei * self.GWei)

            else:
                return Ether(Ether(other).Ether * self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __truediv__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(self.Ether)) / Decimal(str(other.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(self.Wei / other.Wei * denominations)

        elif isinstance(other, int):
            return Wei(self.Wei / Decimal(str(other)))

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(self.GWei / GWei(other).GWei)

            else:
                return Ether(self.Ether / Ether(other).Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __rtruediv__(self, other):
        if isinstance(other, TokenAmount):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            if self.unit != 'ether':
                raise ArithmeticError('You can only perform this action with an Ether unit!')

            return Ether(Decimal(str(other.Ether)) / Decimal(str(self.Ether)))

        if isinstance(other, Unit):
            if isinstance(other, Unit) and self.unit != other.unit:
                raise ArithmeticError('The units are different!')

            denominations = int(Decimal(str(unit_denominations[self.unit])) * Decimal(str(10 ** self.decimals)))
            return Wei(other.Wei / self.Wei * denominations)

        elif isinstance(other, int):
            return Wei(Decimal(str(other)) / self.Wei)

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return GWei(GWei(other).GWei / self.GWei)

            else:
                return Ether(Ether(other).Ether / self.Ether)

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __iadd__(self, other):
        return self.__add__(other)

    def __isub__(self, other):
        return self.__sub__(other)

    def __imul__(self, other):
        return self.__mul__(other)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __lt__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei < other.Wei

        elif isinstance(other, int):
            return self.Wei < other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei < GWei(other).GWei

            else:
                return self.Ether < Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __le__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei <= other.Wei

        elif isinstance(other, int):
            return self.Wei <= other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei <= GWei(other).GWei

            else:
                return self.Ether <= Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __eq__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei == other.Wei

        elif isinstance(other, int):
            return self.Wei == other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei == GWei(other).GWei

            else:
                return self.Ether == Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __ne__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei != other.Wei

        elif isinstance(other, int):
            return self.Wei != other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei != GWei(other).GWei

            else:
                return self.Ether != Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __gt__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei > other.Wei

        elif isinstance(other, int):
            return self.Wei > other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei > GWei(other).GWei

            else:
                return self.Ether > Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")

    def __ge__(self, other):
        if isinstance(other, (Unit, TokenAmount)):
            if self.decimals != other.decimals:
                raise ArithmeticError('The values have different decimals!')

            return self.Wei >= other.Wei

        elif isinstance(other, int):
            return self.Wei >= other

        elif isinstance(other, float):
            if self.unit == 'gwei':
                return self.GWei >= GWei(other).GWei

            else:
                return self.Ether >= Ether(other).Ether

        else:
            raise ArithmeticError(f"{type(other)} type isn't supported!")


class Wei(Unit):
    """
    An instance of a Wei unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'wei')


class MWei(Unit):
    """
    An instance of a MWei unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'mwei')


class GWei(Unit):
    """
    An instance of a GWei unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'gwei')


class Szabo(Unit):
    """
    An instance of a Szabo unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'szabo')


class Finney(Unit):
    """
    An instance of a Finney unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'finney')


class Ether(Unit):
    """
    An instance of an Ether unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'ether')


class KEther(Unit):
    """
    An instance of a KEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'kether')


class MEther(Unit):
    """
    An instance of a MEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'mether')


class GEther(Unit):
    """
    An instance of a GEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'gether')


class TEther(Unit):
    """
    An instance of a TEther unit.
    """

    def __init__(self, amount: Union[int, float, str, Decimal]) -> None:
        """
        Initialize the class.

        Args:
            amount (Union[int, float, str, Decimal]): an amount.

        """
        super().__init__(amount, 'tether')
