import re
import sys
import random
from loguru import logger

from libs.py_eth_async.client import Client

from data import config
from data.models import Settings
from utils.db_api.models import Wallet

from libs.pretty_utils.type_functions.floats import randfloat
from libs.py_eth_async.data.models import Network, Networks

from utils.encryption import get_private_key
from utils.db_api.database import get_wallet, db
from utils.miscellaneous.read_spreadsheet import read_spreadsheet


class Import:
    @staticmethod
    async def wallets() -> None:
        print(f'''Open and fill in the spreadsheet called {config.LIGHTGREEN_EX}import.xlsx{config.RESET_ALL}.\n''')
        input(f'Then press {config.LIGHTGREEN_EX}Enter{config.RESET_ALL}.')
        wallets = read_spreadsheet(path=config.IMPORT_FILE)

        if wallets:
            settings = Settings()
            imported = []
            edited = []
            total = len(wallets)
            sys_exit = False

            for num, wallet in enumerate(wallets):
                logger.info(f'Importing {num+1} out of {len(wallets)} accounts!')
                try:
                    private_key = get_private_key(wallet['private_key'])
                    name = wallet['name']
                    name = str(name) if name else None
                    proxy = wallet['proxy']
                    # mail_data = wallet['mail_data']

                    if 'wrong password or salt' in private_key:
                        logger.error(f'Wrong password or salt! Decrypt private key not possible')
                        sys_exit = True
                        break

                    if not all((private_key,)):
                        print(
                            f"{config.RED}You didn't specify one or more of the mandatory values: "
                            f"private_key!{config.RESET_ALL}"
                        )
                        continue

                    if re.match(r'\w' * 64, private_key):
                        wallet_instance = get_wallet(private_key=private_key)

                        if wallet_instance and wallet_instance.name != name:
                            wallet_instance.name = name
                            db.commit()
                            edited.append(wallet_instance)

                        elif not wallet_instance:
                            client = Client(private_key=private_key, network=Networks.Ethereum)
                            address = client.account.address
                            h_mekr = random.randint(settings.h_mekr.from_, settings.h_mekr.to_)
                            h_nft = random.randint(settings.h_nft.from_, settings.h_nft.to_)
                            wallet_instance = Wallet(
                                private_key=wallet['private_key'], address=address, name=name,
                                proxy=proxy,h_mekr = h_mekr, h_nft=h_nft)
                            db.insert(wallet_instance)
                            imported.append(wallet_instance)

                except:
                    logger.error('Import.wallets')
                    print(f'{config.RED}Failed to import wallet!{config.RESET_ALL}')

            if sys_exit:
                sys.exit(1)

            text = ''
            if imported:
                text += (f'\n--- Imported\nN\t{"address":<72}{"name":<16}'
                         f'{"h_mekr":<10}')
                for i, wallet in enumerate(imported):
                    text += (f'\n{i + 1:<8}{wallet.address:<72}{wallet.name:<16}'
                             f'{wallet.h_mekr:<10}')

                text += '\n'

            if edited:
                text += (f'\n--- Edited\nN\t{"address":<72}{"name":<16}'
                         f'{"h_mekr":<10}')
                for i, wallet in enumerate(edited):
                    text += (f'\n{i + 1:<8}{wallet.address:<72}{wallet.name:<16}'
                             f'{wallet.h_mekr:<10}')

                text += '\n'

            print(
                f'{text}\nDone! {config.LIGHTGREEN_EX}{len(imported)}/{total}{config.RESET_ALL} wallets were imported, '
                f'name have been changed at {config.LIGHTGREEN_EX}{len(edited)}/{total}{config.RESET_ALL}.'
            )

        else:
            print(f'{config.RED}There are no wallets on the file!{config.RESET_ALL}')