from typing import Optional

from sqlalchemy.orm import declarative_base
from libs.pretty_utils.type_functions.classes import AutoRepr
from sqlalchemy import (Column, Integer, Text, Boolean)
from data.models import WorkStatuses

# --- Wallets
Base = declarative_base()


class Wallet(Base, AutoRepr):
    __tablename__ = 'wallets'
    id = Column(Integer, primary_key=True)
    private_key = Column(Text, unique=True)
    address = Column(Text)
    name = Column(Text)
    proxy = Column(Text)
    next_initial_action_time = Column(Integer)
    h_mekr = Column(Integer)
    h_nft = Column(Integer)
    status = Column(Text)

    def __init__(self, private_key: str, proxy: str, h_mekr: int, h_nft: int, address: Optional[str] = None,
                 name: Optional[str] = None) -> None:
        self.private_key = private_key
        self.address = address
        self.name = name
        self.proxy = proxy
        self.next_initial_action_time = 0
        self.h_mekr = h_mekr
        self.h_nft = h_nft
        self.status = WorkStatuses.Initial
