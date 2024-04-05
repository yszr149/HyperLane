import random

from data.config import logger
from tasks.controller import Controller
from utils.db_api.models import Wallet
from functools import partial

from data.models import TokenAmount, Settings, Ether, Tokens


def action_add(
        available_action,
        h_mekr_bridge=False,
        h_nft_bridge=False,
):
    weight = 0.2
    if h_mekr_bridge:
        weight = 0.2
        action = available_action.mint_and_bridge_token
    elif h_nft_bridge:
        weight = 0.2
        action = available_action.mint_and_bridge_nft
    else:
        logger.error("GLOBAL ERROR IN ADDING ACTION")
    return [partial(action)], [weight]


async def select_random_action(controller: Controller, wallet: Wallet, initial: bool = True):
    settings = Settings()

    possible_actions = []
    weights = []

    h_mekr_bridge = 0
    h_nft_bridge = 0
    tx_total = 0

    if initial:
        # tx_total, h_mekr_bridge, h_nft_bridge = await controller.get_activity_count(wallet=wallet)
        msg = (f'{wallet.address} | total tx/action tx: {tx_total}/{h_mekr_bridge + h_nft_bridge}'
               f' | amount hMerk bridged: {h_mekr_bridge}/{wallet.h_mekr}; amount hNFT bridged: {h_nft_bridge}/{wallet.h_nft}')
        logger.info(msg)

        if h_mekr_bridge >= wallet.h_mekr and h_nft_bridge >= wallet.h_nft:
            return 'Processed'

    # I - hMERK via Merkly
    if h_mekr_bridge < int(wallet.h_mekr):
        actions, w = action_add(controller.h_merk, h_mekr_bridge=True)
        possible_actions.extend(actions)
        weights.extend(w)

    # II - hNFT via Merkly
    if h_nft_bridge < int(wallet.h_nft):
        actions, w = action_add(controller.h_nft, h_nft_bridge=True)
        possible_actions.extend(actions)
        weights.extend(w)

    logger.info(f'Possible actions {len(possible_actions)} : {possible_actions}')

    if possible_actions:
        action = random.choices(possible_actions, weights=weights)[0]
        if action:
            return action

    msg = f'{wallet.address} | select_random_action | can not choose the action'
    logger.info(msg)

    return None