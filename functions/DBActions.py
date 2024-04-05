import logging

from data import config
from utils.db_api.database import db, get_wallets, get_wallet
from utils.miscellaneous.read_spreadsheet import read_spreadsheet


class DBActions:
    @staticmethod
    async def delete() -> None:
        deleted = []
        wallets = read_spreadsheet(path=config.IMPORT_FILE)

        if wallets:
            for wallet in wallets:
                try:
                    wallet = get_wallet(private_key=wallet['private_key'])

                    if wallet:
                        db.s.delete(wallet)
                        deleted.append(wallet)

                except:
                    logging.exception('DBActions.delete')

            db.commit()
            text = ''

            if deleted:
                text += '\n--- Deleted\nN\taddress\tname'
                for i, wallet in enumerate(deleted):
                    text += f'\n{i + 1}\t{wallet.address}\t{wallet.name}'
                print(f'{text}\n\nDone!')

        else:
            print(f'{config.RED}There are no addresses on the file!{config.RESET_ALL}')

    @staticmethod
    async def completely() -> None:
        for wallet in get_wallets():
            db.s.delete(wallet)

        db.commit()
        print('Done!')
