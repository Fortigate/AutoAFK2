"""AFK Journey Metadata."""

import time
from datetime import datetime, timezone
from typing import Union  # TODO: Update Python. Union required for Python <3.10


class AFKJMetadata:
    """AFKJ Metadata Class."""

    def __init__(self, server: str) -> None:
        """Initialize AFKJ Metadata.

        Args:
            server (str): Short server name.
        """
        self.server: str = server  # Call setter

        self._last_corrupt: Union[float, None] = None
        self._last_synergy: Union[float, None] = None
        self.current_time_utc: datetime = datetime.now(timezone.utc)
        self.first_stage_won: bool = False
        self.formation: int = 1
        self.load_formations: bool = True
        self.stage_defeats: int = 0
        self.version: str = "3.3.1b"

        # Quick storage for commonly used regions
        self.regions: dict[str, tuple[int, int, int, int]] = {
            # locate
            "sunandstars": (770, 40, 100, 100),
            "main_menu": (900, 1750, 150, 150),
            "menu_activities": (20, 950, 1050, 800),
            "back": (50, 1750, 150, 150),
            "chat_window": (184, 362, 850, 1300),
            "right_sidebar": (888, 744, 190, 1000),
            "chat_selection": (20, 300, 170, 900),
            "top_third": (0, 0, 1080, 640),
            "middle_third": (0, 640, 1080, 640),
            "bottom_third": (0, 1280, 1080, 640),
            "bottom_buttons": (0, 1620, 1080, 300),
            "confirm_deny": (500, 1100, 500, 300),
            "battle_modes": (20, 580, 1050, 1100),
            "action_buttons": (
                400,
                1050,
                300,
                500,
            ),  # gives out of bounds error and I'm too tired to work out why
            "levelup": (150, 900, 950, 50),
            "levelup_hero": (1000, 1700, 80, 60),
            "x3_and_skip": (720, 1450, 350, 110),
        }

    @property
    def last_synergy(self) -> Union[float, None]:
        """Get last_synergy time.

        Returns:
            float | None: Time of last synergy battle request.
        """
        return self._last_synergy

    @last_synergy.setter
    def last_synergy(self) -> None:
        """Set last_synergy time."""
        self._last_synergy = time.time() - 300

    @property
    def last_corrupt(self) -> Union[float, None]:
        """Get last_corrupt time.

        Returns:
            float | None: Time of last corrupt creature battle request.
        """
        return self._last_corrupt

    @last_corrupt.setter
    def last_corrupt(self) -> None:
        """Set last_corrupt time."""
        self._last_corrupt = time.time()

    @property
    def server(self) -> str:
        """Get game server.

        Returns:
            str: Time of last corrupt creature battle request.
        """
        return self._server

    @server.setter
    def server(self, value: str) -> None:
        """Set server game path.

        Args:
            value (str): Short server name.
        """
        if value == "global":
            self._server = "com.farlightgames.igame.gp"
        elif value == "vn":
            self._server = "com.farlightgames.igame.gp.vn"
