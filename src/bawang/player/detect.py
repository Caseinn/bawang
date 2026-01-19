import shutil
from typing import Optional

from bawang import config


def detect_player() -> Optional[str]:
    for player in config.PREFERRED_PLAYERS:
        if shutil.which(player):
            return player
    return None
