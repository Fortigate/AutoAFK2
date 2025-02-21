"""AFKJ Automation functions."""

import inspect
import math
import time
from configparser import ConfigParser
from datetime import datetime
from humanfriendly import format_timespan
from logging import Logger
from typing import Any

from interaction.emulator_interaction import EmulatorInteractions


class AFKJAutomation(EmulatorInteractions):
    """AFKJ Automation Class."""

    def __init__(self, config: ConfigParser, logger: Logger, metadata) -> None:
        """Initialize AFKJ automation functions.

        Args:
            config (ConfigParser): Configurations from settings.ini.
            logger (Logger): Logger.
            metadata (_type_): AFKJ metadata.
        """
        super().__init__(config=config, logger=logger)
        self.metadata: Any = metadata

    def team_up(self) -> None:
        """Perma-loop for finding and joining Corrupt Creatures.

        This perma-loop is called from the startup flags and will continuously search for Corrupt Creatures
        to join. It will also handle Synergy battles and lending heroes. It will restart itself if it gets
        stuck or times out for any reason.
        """
        timer = 0
        start: float = time.time()

        while True:
            # Naughty perma-loop, nested inside another when we call this with startup flags so calling 'return' will start from the top
            # First ensure we're at the main map
            while not self.is_visible(
                "labels/sunandstars",
                region=self.metadata.regions["sunandstars"],
                seconds=0,
            ):
                self.click(
                    "buttons/back", suppress=True, region=self.metadata.regions["back"]
                )
                self.click_location("neutral")

            # Then open team-up chat
            while not self.is_visible(
                "teamup/teamup",
                click=True,
                region=self.metadata.regions["chat_selection"],
            ):  # Open the Team-Up section
                self.click(
                    "teamup/chat",
                    seconds=2,
                    suppress=True,
                    region=self.metadata.regions["right_sidebar"],
                )  # Open Chat window
                self.click(
                    "teamup/chat_yellow",
                    retry=5,
                    seconds=2,
                    suppress=True,
                    confidence=0.7,
                    region=self.metadata.regions["right_sidebar"],
                )  # Open Chat window

            # Loop while searching for 'Join' button
            while not self.is_visible(
                "teamup/join",
                seconds=0,
                confidence=0.8,
                region=self.metadata.regions["chat_window"],
            ):

                # If it's been more than 300s we might be stuck so we try these to get back to the chat window
                if (time.time() - self.metadata.last_corrupt) > 300 and (
                    time.time() - self.metadata.last_synergy
                ) > 300:
                    self.click(
                        "teamup/chat",
                        seconds=0,
                        suppress=True,
                        region=self.metadata.regions["right_sidebar"],
                    )  # Ensure we actually have chat open
                    self.click(
                        "teamup/teamup",
                        seconds=0,
                        suppress=True,
                        region=self.metadata.regions["chat_selection"],
                    )  # Ensure we're in the right section
                    self.click(
                        "buttons/back",
                        seconds=0,
                        suppress=True,
                        region=self.metadata.regions["back"],
                    )  # Somehow we open afk rewards occasionally, this will exit that
                    self.is_visible(
                        "buttons/confirm",
                        region=self.metadata.regions["confirm_deny"],
                        click=True,
                    )  # to catch 'Reconnect to chat?'
                    self.swipe(1000, 1500, 1000, 500, 500)

                # Synergy battle hero lending is handled here for reasons
                if self.is_visible(
                    "teamup/synergy",
                    seconds=0,
                    region=self.metadata.regions["chat_window"],
                ):
                    x, y = self.returnxy(
                        "teamup/synergy", region=self.metadata.regions["chat_window"]
                    )
                    # We wait 60s between each one else we can end up opening and closing the same one repeatadly
                    if (
                        x != 0
                    ):  # 0 is the 'nothing found' return value from returnxy() so skip if it's returned
                        # If green button found and it's been more than 60s since the last Synergy
                        if self.return_pixel_colour(
                            x, y + 220, 2, seconds=0
                        ) < 200 and (time.time() - self.metadata.last_synergy > 120):
                            self.logger.info("Synergy Battle found!")
                            self.click_xy(
                                x, y + 220
                            )  # 220 is the button distance from the label
                            if self.is_visible(
                                "buttons/back", region=self.metadata.regions["back"]
                            ):
                                self.click_xy(
                                    300, 900
                                )  # Second highest power hero (in case you want to save the primary or guildmates/friends)
                                self.click_xy(650, 1800)
                                self.click(
                                    "buttons/back",
                                    suppress=True,
                                    region=self.metadata.regions["back"],
                                )
                                self.logger.info("Hero lent\n")
                                self.metadata.last_synergy = time.time()
                                return
                            else:
                                self.logger.info(
                                    "Something went wrong with Synergy Battle, returning\n"
                                )
                                self.metadata.last_synergy = time.time()
                                return
                    else:
                        self.logger.info("Synergy button gone!\n")
                        return

            # Log start time and click 'Join'
            duration = time.time() - start
            self.click_last(
                "teamup/join",
                seconds=4,
                confidence=0.8,
                region=self.metadata.regions["chat_window"],
            )

            # If Ready button is not visible after clicking join then it's been disbanded/level locked etc so we restart
            if not self.is_visible(
                "teamup/ready", region=self.metadata.regions["bottom_buttons"]
            ):
                # Try a quit just in case
                self.click(
                    "teamup/quit",
                    region=self.metadata.regions["bottom_buttons"],
                    suppress=True,
                )
                self.click(
                    "buttons/confirm",
                    region=self.metadata.regions["confirm_deny"],
                    suppress=True,
                )  # to catch 'Reconnect to chat?
                return

            # Ready up
            self.click(
                "teamup/ready",
                seconds=4,
                region=self.metadata.regions["bottom_buttons"],
            )
            self.logger.info(
                "Corrupt Creature found in " + format_timespan(round(duration)) + "!"
            )  # Only message after we're in to avoid spam

            # If Quit button is visible 15 cycles after readying up then the host is afk etc so we restart
            while self.is_visible(
                "teamup/quit",
                confidence=0.8,
                region=self.metadata.regions["bottom_buttons"],
            ):
                timer += 1
                if timer > 15:
                    self.logger.info("Lobby timeout error!\n")
                    self.click(
                        "teamup/quit",
                        seconds=2,
                        region=self.metadata.regions["bottom_buttons"],
                    )
                    self.click_xy(850, 1250, seconds=4)
                    return

            # Deploy Heroes
            while self.is_visible(
                "teamup/ready_lobby",
                confidence=0.8,
                region=self.metadata.regions["bottom_buttons"],
            ):
                self.logger.info("Deploying heroes")
                self.wait(
                    2
                )  # Wait for the emulator to load new assets after moving to battle screen else first click below doesn't register
                self.click_xy(120, 1300)
                self.click_xy(270, 1300)
                self.click_xy(450, 1300)
                self.click(
                    "teamup/ready_lobby",
                    suppress=True,
                    confidence=0.8,
                    region=self.metadata.regions["bottom_buttons"],
                )
                break  # Break loop otherwise if we miss a button due to lag we loop here until battle starts

            # Wait until battle finishes
            while not self.is_visible(
                "labels/tap_to_close",
                confidence=0.8,
                region=self.metadata.regions["bottom_buttons"],
            ):
                timer += 1
                if timer > 30:
                    self.logger.info("Battle timeout error!\n")
                    self.click_location(
                        "neutral"
                    )  # Neutral taps to try and get back to main map if something went wrong
                    return
            if self.is_visible(
                "labels/tap_to_close",
                confidence=0.8,
                region=self.metadata.regions["bottom_buttons"],
                click=True,
            ):
                self.logger.info("Battle complete!\n")

            # Finish up and start the loop again
            timer = 0
            self.metadata.last_corrupt = time.time()
            return

    def start_autoprogress(self) -> None:
        """
        Starts the Auto-Progress feature in the game.

        This function opens the AFK Rewards menu, clears any pop-ups that may be present,
        and then starts the Auto-Progress feature if the WoI stage is available.

        If there is an issue starting Auto-Progress, the function will attempt to recover
        by returning to the main menu.
        """
        self.logger.info("Starting Auto-Progress")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        self.click_xy(100, 1800, seconds=4)  # Open AFK Rewards
        self.click_xy(750, 1750, seconds=4)  # Clear Pop-Up
        self.is_visible(
            "buttons/claim_afkrewards",
            region=self.metadata.regions["middle_third"],
            click=True,
        )

        if self.is_visible("labels/afk_rewards_woi", region=[0, 680, 150, 200]):
            self.click_xy(750, 1600, seconds=5)  # AFK Stage Battle
            self.click(
                "buttons/autobattle", region=self.metadata.regions["bottom_buttons"]
            )
            self.click(
                "buttons/confirm",
                region=self.metadata.regions["confirm_deny"],
                seconds=3,
            )
            self.click("buttons/auto-progress", seconds=3)
            self.click("buttons/confirm", seconds=6)
            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Auto-Progress started!\n")
        else:
            self.logger.info("Issue starting Auto-Progress!")
            self.recover()

    def claim_afk_rewards(self) -> None:
        """Claims the AFK rewards in the game.

        This method opens the AFK rewards menu, collects the available rewards,
        including daily quest completion and fast rewards, and logs the process.
        If there is an issue with collecting the rewards, it attempts to recover
        to the main menu.

        Steps:
        1. Open the AFK Rewards menu.
        2. Clear any pop-ups if present.
        3. Check for the availability of chest rewards and collect them twice to
        ensure daily quest completion.
        4. Collect fast rewards based on the configured number of times.
        5. Close the AFK Rewards menu and ensure the process is completed
        successfully.
        """
        self.logger.info("Claiming AFK Rewards")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        self.click_xy(100, 1800, seconds=4)  # Open AFK Rewards
        self.click_xy(750, 1750, seconds=4)  # Clear Pop-Up

        if self.is_visible("labels/afk_rewards_coe", region=[0, 680, 150, 200]):
            self.click_xy(550, 1400)  # Click Chest
            self.click_xy(550, 1080)  # Click Collect
            self.wait(2)  # Wait and claim again to complete daily quest
            self.click_xy(550, 1400)  # Click Chest
            self.click_xy(550, 1080)  # Click Collect

            # Fast rewards
            if self.is_visible("labels/afk_rewards_coe", region=[0, 680, 150, 200]):
                for _ in range(self.config.getint("ACTIVITIES", "fast_rewards")):
                    if self.is_visible("buttons/fast_rewards", click=True):
                        self.logger.info("Fast reward #" + str(_ + 1) + " claimed")
                        self.click("buttons/confirm", suppress=True)
                        self.click_xy(800, 1800)

                self.click_xy(100, 1800)  # Close
                if self.safe_open_and_close(
                    name=inspect.currentframe().f_code.co_name, state="close"
                ):
                    self.logger.info("AFK Rewards Claimed!\n")
        else:
            self.logger.info("Issue opening AFK Rewards!")
            self.recover()

    def friend_points_collect(self) -> None:
        """Claims the available friend points in the game.

        This method opens the friends menu, collects the available friend points,
        and logs the process. If there is an issue with collecting the friend
        points, it attempts to recover to the main menu.

        Steps:
        1. Open the Friends menu.
        2. Clear any pop-ups if present.
        3. Collect the available friend points.
        4. Close the Friends menu and ensure the process is completed
        successfully.
        """
        self.logger.info("Claiming Friend Gifts")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        self.wait(2)  # For things to load
        self.click("buttons/main_menu", region=self.metadata.regions["main_menu"])
        self.click(
            "buttons/friends",
            region=self.metadata.regions["menu_activities"],
            seconds=2,
        )

        if self.is_visible("labels/friends"):
            self.click_xy(700, 1800, seconds=2)
            self.click_xy(850, 300, seconds=2)
            self.click_location("neutral")
            self.click("buttons/back", region=self.metadata.regions["back"])
            self.click("buttons/back", region=self.metadata.regions["back"])
            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Friend Gifts Claimed!\n")
        else:
            self.logger.info("Issue claiming friends points!")
            self.recover()

    def mail_connect(self) -> None:
        """Claims the available mail in the game.

        This method navigates to the mail section, collects all available mail,
        and logs the process. If there is an issue with collecting the mail, it
        attempts to recover to the main menu.

        Steps:
        1. Open the main menu.
        2. Navigate to the Mail section.
        3. Collect all available mail items.
        4. Close the Mail section and ensure the process is completed successfully.
        """
        self.logger.info("Claiming Mail")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        self.click("buttons/main_menu", region=self.metadata.regions["main_menu"])
        self.click(
            "buttons/mail", region=self.metadata.regions["menu_activities"], seconds=2
        )

        if self.is_visible("labels/mail"):
            self.click_xy(750, 1800, seconds=2)
            self.click_xy(750, 1800, seconds=2)
            self.click("buttons/back", region=self.metadata.regions["back"])
            self.click("buttons/back", region=self.metadata.regions["back"])
            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Mail Claimed!\n")
        else:
            self.logger.info("Issue claiming Mail!")
            self.recover()

    def emporium_purchases(self) -> None:
        """Purchases the daily summon card in the emporium guild store.

        This method navigates to the guild store section of the emporium,
        checks for the daily summon card availability, and purchases it if
        available. If there is an issue with the purchase, it attempts to
        recover to the main menu.

        Steps:
        1. Open the main menu.
        2. Navigate to the Emporium section.
        3. Open the Guild Store.
        4. Check if the daily summon card is available.
        5. If available, purchase the card.
        6. Close the Guild Store and ensure the process is completed successfully.
        """
        self.logger.info("Purchasing daily summon card")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        self.click("buttons/main_menu", region=self.metadata.regions["main_menu"])
        self.click(
            "buttons/emporium",
            region=self.metadata.regions["menu_activities"],
            seconds=2,
        )
        self.click("buttons/guild_store")
        if self.is_visible(
            "labels/emporium_guild", region=self.metadata.regions["top_third"]
        ):
            if self.is_visible("emporium/guild_summoncard"):
                self.click(
                    "emporium/guild_summoncard",
                    region=self.metadata.regions["middle_third"],
                )
                self.click(
                    "buttons/purchase", region=self.metadata.regions["bottom_buttons"]
                )
                self.click(
                    "buttons/confirm",
                    region=self.metadata.regions["confirm_deny"],
                    seconds=2,
                )
                self.click_location("neutral")
            else:
                self.logger.info("Daily card already purchased!")
            self.click("buttons/back2", region=self.metadata.regions["back"], seconds=2)
            self.click("buttons/back", region=self.metadata.regions["back"])
            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Daily summon card purchased!\n")
        else:
            self.logger.info("Issue purchasing summon card!")
            self.recover()

    def arena(self, battles: int = 9) -> None:
        """
        Executes a series of battles in the Arena mode.

        This method manages the process of battling in the Arena. It ensures the
        Arena interface is open, handles any pop-ups such as weekly reports, and
        proceeds to initiate battles until the specified number of battles is
        completed. It also handles any confirmation dialogs for purchasing
        additional challenges and attempts to skip battle animations if possible.
        In case of timeouts or issues, it attempts to recover and logs all actions
        throughout the process.

        Args:
            battles (int): The number of battles to fight in the Arena. Defaults to 9.
        """
        timeout: int = 0
        counter: int = 0

        self.logger.info("Battling Arena")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        self.click_xy(450, 1825)
        if self.is_visible("labels/battle_modes"):
            self.click(
                "buttons/arena", region=self.metadata.regions["battle_modes"], seconds=2
            )
            if self.is_visible(
                "labels/arena_weekly_report", region=self.metadata.regions["top_third"]
            ):
                self.logger.info("Weekly Arena rewards found!")
                self.click_xy(550, 1800)
            self.click_location("neutral")
            self.click_location("neutral")
            while counter < battles:
                self.logger.info(
                    "Fighting Arena Battle " + str(counter + 1) + " of " + str(battles)
                )
                self.click(
                    "buttons/challenge",
                    region=self.metadata.regions["bottom_buttons"],
                    seconds=3,
                    retry=5,
                    confidence=0.8,
                )
                if self.is_visible(
                    "buttons/confirm", region=self.metadata.regions["confirm_deny"]
                ):
                    # self.logger.info('Purchase challenge pop-up detected, confirming')
                    self.click(
                        "buttons/confirm", region=self.metadata.regions["confirm_deny"]
                    )
                    self.click(
                        "buttons/challenge",
                        seconds=3,
                        region=self.metadata.regions["bottom_buttons"],
                    )
                self.click_xy(180, 1450, seconds=6)  # Leftmost opponent
                self.click(
                    "buttons/battle", region=self.metadata.regions["bottom_buttons"]
                )
                while not self.is_visible(
                    "labels/tap_to_close",
                    region=self.metadata.regions["bottom_buttons"],
                    confidence=0.8,
                ):
                    # Clear promotion screen if visible (not sure this does anything with while is_visible loop at the end covering the case)
                    if self.is_visible(
                        "labels/arena_promote",
                        region=self.metadata.regions["bottom_third"],
                    ):
                        self.click_xy(550, 1800)
                    if self.is_visible(
                        "buttons/skip_inverse",
                        seconds=0,
                        region=self.metadata.regions["x3_and_skip"],
                    ):
                        self.click(
                            "buttons/skip_inverse",
                            seconds=3,
                            region=self.metadata.regions["x3_and_skip"],
                        )
                        self.click("buttons/confirm", suppress=True)
                        self.logger.info("Skip available, skipping the fight")
                    timeout += 1
                    if (
                        timeout > 40
                    ):  # Should be about 10 seconds longer than a full fight at 2x
                        self.logger.info("Arena timeout error\n")
                        timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
                        self.save_screenshot("arena_timeout_" + timestamp)
                        self.recover()
                        return
                self.logger.info("Battle complete")
                while self.is_visible(
                    "labels/tap_to_close",
                    region=self.metadata.regions["bottom_buttons"],
                    confidence=0.8,
                ):
                    self.click(
                        "labels/tap_to_close",
                        region=self.metadata.regions["bottom_buttons"],
                        seconds=4,
                        suppress=True,
                    )
                counter += 1
            # Collect Victory Rewards
            self.click_xy(200, 550)
            self.click_xy(200, 550)
            self.click_xy(200, 550)
            self.click_location("neutral")
        else:
            self.logger.info("Issue opening Arena!")
            self.recover()

        if self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="close"
        ):
            self.logger.info("Arena battles completed!\n")

    def dream_realm(self) -> None:
        """
        Enters the Dream Realm and completes a single battle.

        Steps:
        1. Opens the Dream Realm menu.
        2. Clears any pop-ups if present.
        3. Collects the available rewards.
        4. Enters a single battle.
        5. Waits for the battle to complete.
        6. Clears the rewards.
        7. Closes the Dream Realm menu and ensures the process is completed
        successfully.
        """
        timer: int = 0

        self.logger.info("Battling Dream Realm")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        self.click_xy(450, 1825, seconds=3)
        self.click(
            "buttons/dream_realm",
            region=self.metadata.regions["battle_modes"],
            seconds=3,
        )
        self.click_xy(1000, 50)  # Clear new season info popup

        # First collect rewards
        if self.is_visible(
            "buttons/battle", region=self.metadata.regions["bottom_buttons"]
        ):
            self.logger.info("Collecting previous round rewards")
            self.click(
                "buttons/dr_rewards",
                region=self.metadata.regions["top_third"],
                seconds=4,
            )
            self.click_xy(550, 1800, seconds=2)  # Clear loot
            self.click("buttons/back2", region=self.metadata.regions["back"], seconds=3)
        else:
            self.logger.info("issue collecting rewards!")
            self.recover()
            return

        # Then attempt a single battle
        if self.is_visible(
            "buttons/battle", region=self.metadata.regions["bottom_buttons"]
        ):
            self.logger.info("Battling Dream Realm")
            self.click(
                "buttons/battle",
                region=self.metadata.regions["bottom_buttons"],
                seconds=5,
            )
            self.click(
                "buttons/battle",
                region=self.metadata.regions["bottom_buttons"],
                seconds=5,
            )
            time.sleep(60)  # wait for battle to end
            while not self.is_visible(
                "labels/tap_to_close", region=self.metadata.regions["bottom_buttons"]
            ):  # Few clicks to clear loot too
                timer += 1
                if timer > 60:
                    self.logger.info("DR Timer Exceeded!")
                    break
                if self.is_visible("labels/dr_first_kill"):
                    self.click_xy(550, 1800)  # clear rewards popup
                pass
            self.click(
                "labels/tap_to_close",
                region=self.metadata.regions["bottom_buttons"],
                seconds=5,
                suppress=True,
            )
            if self.is_visible("buttons/deny", click=True, seconds=3):
                self.logger.info("Not sharing formation..")
            self.click(
                "labels/tap_to_close",
                region=self.metadata.regions["bottom_buttons"],
                seconds=5,
                suppress=True,
            )
            self.logger.info("Battle complete!")
            self.click("buttons/back", region=self.metadata.regions["back"], seconds=2)
            self.click("buttons/back2", region=self.metadata.regions["back"])
            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Dream Realm completed!\n")
        else:
            self.logger.info("Issue collecting rewards!")
            self.recover()
            return

    def single_recruit(self) -> None:
        """Attempts a single hero recruitment in the game.

        This method navigates to the hero recruitment section, performs a single
        recruitment, and handles any pop-ups and animations associated with the
        process. If there is an issue during recruitment, it attempts to recover
        to the main menu.

        Steps:
        1. Open the main menu and navigate to the All Hero Recruitment section.
        2. Perform a single hero recruitment.
        3. Handle animations and pop-ups during the recruitment process.
        4. Return to the main menu and ensure the recruitment process is completed
        successfully.
        """
        self.logger.info("Attempting a single reruitment")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        # Navigate and open all hero recruitment
        self.click_xy(300, 1850, seconds=6)
        self.click_xy(420, 700, seconds=6)
        self.click("buttons/all_hero_recruitment", seconds=7)

        # Perform recruit, lots of long waits here as the animations are slow before we stabilise again
        if self.is_visible(
            "labels/all_hero_recruitment",
            region=self.metadata.regions["bottom_buttons"],
        ):
            self.click_xy(250, 1550)
            self.click("buttons/continue2", suppress=True)  # long wait for animation
            self.wait(15)
            self.click("buttons/back")
            self.click("buttons/back2", seconds=3)
            self.click("buttons/back2")
            self.logger.info("Single recruitment complete!\n")
        else:
            self.logger.info("Issue doing single recruitment!")
            self.recover()
            return

    def collect_quests(self) -> None:
        """
        Collects all types of quests in the game.

        This method navigates through the game's quest menus to collect rewards
        from daily, guild, season growth, and season growth trials quests. It
        logs the process and handles any pop-ups that may occur during collection.
        If there is an issue with collecting the quests, it attempts to recover
        to the main menu.

        Steps:
        1. Open the main menu and navigate to the quests section.
        2. Collect daily quests and optionally collect daily rewards.
        3. Collect guild quests rewards.
        4. Collect season growth trials rewards.
        5. Collect season growth quests rewards.
        6. Collect season growth trials rewards if available.
        7. Navigate back to the main menu and ensure the process is completed
        successfully.
        """
        self.logger.info("Collecting Quests")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        self.click("buttons/main_menu", region=self.metadata.regions["main_menu"])
        self.click(
            "buttons/quests", region=self.metadata.regions["menu_activities"], seconds=3
        )
        self.click_xy(300, 1800, seconds=2)  # Daily quests

        if self.is_visible("labels/daily_quests"):
            self.logger.info("    Collecting Daily Quests")
            self.is_visible(
                "buttons/quick_claim",
                region=self.metadata.regions["bottom_third"],
                click=True,
            )
            self.wait(3)
            if self.config.getboolean("ADVANCED", "collect_daily_rewards") is True:
                self.click_xy(900, 200, seconds=2)  # collect dailies
                self.click_location("neutral")
            else:
                self.logger.info("Skipping daily quest rewards collection")

            # Guild quests
            self.logger.info("    Collecting Guild Quests")
            self.click_xy(500, 1800, seconds=2)
            while self.is_visible("buttons/quests_claim"):
                self.click("buttons/quests_claim")

            # Season Quests
            self.logger.info("    Collecting Season Growth Trials")
            self.click_xy(950, 1825, seconds=2)

            # Season Growth Quests
            self.logger.info("    Collecting Season Growth Quests")
            self.click_xy(300, 1670, seconds=2)
            while self.is_visible("buttons/quests_claim"):
                self.click("buttons/quests_claim")

            # Season Growth Trials
            self.click_xy(800, 1670, seconds=2)
            while self.is_visible(
                "labels/reward", click=True, region=(232, 451, 700, 100)
            ):
                while self.is_visible("buttons/quests_claim"):
                    self.click("buttons/quests_claim")

            self.click("buttons/back2", region=self.metadata.regions["back"])
            self.click("buttons/back", region=self.metadata.regions["back"])

            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Quests collected!\n")
        else:
            self.logger.info("Issue collecting quests!")
            self.recover()
            return

    def level_up(self) -> None:
        """Levels up all heroes that can be levelled up. If the 'use_level_up_all' option is enabled, the 'Level Up All' button is clicked.
        Otherwise, heroes are levelled up individually.

        Steps:
        1. Opens the Heroes Hall.
        2. If 'use_level_up_all' is enabled, clicks the 'Level Up All' button.
        3. If 'use_level_up_all' is disabled, levels up each hero individually.
        4. Clicks the level up button until it is no longer visible.
        5. If the hero is at level 10, clicks the button in the centre of the screen to level up using dust.
        6. Goes back to the Heroes Hall.
        7. If all heroes have been levelled up, closes the Heroes Hall and logs the process as complete.
        """
        self.logger.info("Leveling available heroes")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        # Clicks the central button when leveling uses Dust rather than XP, then presses back to return to the selected hero screen
        def dust_level():
            if self.is_visible(
                "buttons/level_up", region=(500, 1725, 260, 100), seconds=0
            ):  # Region in the centre for the 10th level 'Level Up' button
                self.click(
                    "buttons/level_up",
                    region=self.metadata.regions["bottom_third"],
                    seconds=4,
                )

        # Open Heroes Hall
        self.click_xy(650, 1850, seconds=3)

        # Level up all if enabled
        if self.config.getboolean("ADVANCED", "use_level_up_all"):
            while self.is_visible(
                "buttons/level_up_all_active",
                region=self.metadata.regions["bottom_third"],
                confidence=0.92,
            ):
                self.click(
                    "buttons/level_up_all_active",
                    region=self.metadata.regions["bottom_third"],
                    confidence=0.92,
                )  # sligtly higher confidence as inactive is the same but greyscale
                self.logger.info("Level up all clicked!")
        # Else we level the heros individually
        else:
            # Click to open hero
            while self.is_visible(
                "buttons/levelup_double", region=self.metadata.regions["levelup"]
            ) or self.is_visible(
                "buttons/levelup_single", region=self.metadata.regions["levelup"]
            ):
                self.logger.info("Hero found!")
                self.click(
                    "buttons/levelup_double",
                    region=self.metadata.regions["levelup"],
                    suppress=True,
                    retry=1,
                )
                self.click(
                    "buttons/levelup_single",
                    region=self.metadata.regions["levelup"],
                    suppress=True,
                    retry=1,
                )
                # Keep clicking to level
                while self.is_visible(
                    "buttons/levelup_double",
                    region=self.metadata.regions["levelup_hero"],
                    seconds=0,
                ):
                    dust_level()
                    self.swipe(800, 1800, 800, 1800, 5000)  # Hacky way to hold it down
                    dust_level()
                while self.is_visible(
                    "buttons/levelup_single",
                    region=self.metadata.regions["levelup_hero"],
                    seconds=0,
                ):
                    dust_level()
                    self.swipe(800, 1800, 800, 1800, 5000)  # Hacky way to hold it down
                    dust_level()
                self.click(
                    "buttons/back",
                    region=self.metadata.regions["bottom_third"],
                    seconds=3,
                    suppress=True,
                    retry=1,
                )  # Back to Hero Box

        self.logger.info("Done!")

        if self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="close"
        ):
            self.logger.info("Heroes levelled!\n")

    def farm_affinity(self) -> None:
        """Clicks all heroes for daily +6 affinity bonus. If Chippy is spotted, adds 1 to the rare counter and repeats the click cycle.
        If the rare counter reaches 3, the function will exit the affinity menu and log the process as complete.

        Steps:
        1. Opens the Heroes Hall.
        2. Clicks the top right hero.
        3. Checks if the hero is a rare hero (Chippy). If it is, increments the rare counter and repeats the click cycle.
        4. If the rare counter reaches 3, clicks the back button to exit the affinity menu.
        5. Logs the process as complete if all heroes have been clicked.
        """
        # 100 is a failsafe in case we don't see Chippy
        self.logger.info("Clicking all heroes for daily +6 affinity bonus")
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )

        rare_counter: int = 0
        self.click_xy(650, 1850, seconds=5)  # Open heroes hall
        self.click_xy(150, 1050, seconds=3)  # Click top right hero

        if self.is_visible(
            "buttons/affinity", region=self.metadata.regions["top_third"]
        ):
            while rare_counter < 3:
                if self.is_visible("labels/rare_hero", region=[15, 5, 105, 65]):
                    self.logger.info("Hamster spotted!")
                    rare_counter += 1
                for clicks in range(3):
                    self.click_xy(550, 1000, seconds=1)
                    self.click_xy(100, 1800, seconds=1)
                self.click_xy(1000, 1100, seconds=1.5)
            self.click("buttons/back", region=self.metadata.regions["back"], seconds=2)
            self.click("buttons/back2", region=self.metadata.regions["back"])
            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Affinity farmed!\n")
        else:
            self.logger.info("Something went wrong opening hero affinity!")
            timestamp = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
            self.save_screenshot("affinity_opening_issue_" + timestamp)
            self.recover()

    def noble_path(self) -> None:
        """Collects the daily rewards from the Noble Path.

        Steps:
        1. Opens the Noble Path menu.
        2. Checks if the Fabled Road is active, if so claims rewards.
        3. Checks if the Seasonal Noble Path is active, if so claims rewards.
        4. Checks if the Standard Noble Path is active, if so claims rewards.
        5. Logs the process as complete if all rewards have been collected.
        """
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        self.logger.info("Collecting noble path")
        self.click(
            "buttons/main_menu", region=self.metadata.regions["main_menu"], seconds=2
        )
        self.click(
            "buttons/noble_path",
            region=self.metadata.regions["menu_activities"],
            seconds=5,
        )
        self.click(
            "buttons/start",
            region=self.metadata.regions["bottom_buttons"],
            suppress=True,
            seconds=3,
        )  # To clear new noble pop-up

        def claim_and_collect(italics=True) -> None:
            """TODO: Unused?"""
            # This will claim quests/collet rewards
            self.click_xy(750, 450)  # Click Quests
            if self.is_visible(
                "buttons/quick_claim",
                click=True,
                region=self.metadata.regions["bottom_third"],
                seconds=5,
            ):  # Can also be 'claim_all_italics'
                self.click_xy(1000, 1800)  # Clear Loot
            # # Travelogue
            # click_xy(350, 450) # Click Trek
            # if is_visible('buttons/claim_all_italics', click=True, region=self.metadata.regions['bottom_third']):
            #     click_xy(1000, 1800) # Clear Loot

        # # Fabled Road
        # self.logger.info('    Checking Fabled Road')
        # if is_visible('buttons/fabled_road_active', region=self.metadata.regions['bottom_third'], seconds=2, grayscale=True) or is_visible('buttons/fabled_road_inactive', region=self.metadata.regions['bottom_third'], click=True, seconds=2, grayscale=True):
        #     claim_and_collect()

        # Seasonal Noble Path
        self.logger.info("    Checking Season Noble Path")
        if self.is_visible(
            "buttons/noble_season_active",
            region=self.metadata.regions["bottom_third"],
            seconds=2,
            grayscale=True,
        ) or self.is_visible(
            "buttons/noble_season_inactive",
            region=self.metadata.regions["bottom_third"],
            click=True,
            seconds=2,
            grayscale=True,
        ):
            self.claim_and_collect()

        # # Noble Path
        # self.logger.info('    Checking Noble Path')
        # if is_visible('buttons/noble_path_active', region=self.metadata.regions['bottom_third'], seconds=2, grayscale=True) or is_visible('buttons/noble_path_inactive', region=self.metadata.regions['bottom_third'], click=True, seconds=2, grayscale=True):
        #     claim_and_collect()

        if self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="close"
        ):
            self.logger.info("Noble path collected!\n")
        else:
            self.logger.info("Something went wrong collecting Season Noble path!")
            self.recover()

    def claim_events(self) -> None:
        """Claims rewards from various in-game events.

        This method navigates through different event screens to claim rewards
        from events like Guild Supremacy. It starts by opening the events menu,
        checks for the visibility of specific event labels, and collects the
        available rewards. If any issues are encountered during the collection,
        it attempts to recover to the main menu.

        Steps:
        1. Open the events menu.
        2. Navigate to Guild Supremacy and collect rewards if available.
        3. Attempt to collect rewards from other events (e.g., Timeless Gala, All Heroes).
        4. Swipe to access additional events as needed.
        5. Close the events menu and ensure the process is completed successfully.
        """
        self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        self.logger.info("Claiming event rewards")
        # click('buttons/main_menu', region=self.metadata.regions['main_menu'], seconds=3)
        # click('buttons/event', region=self.metadata.regions['menu_activities'], seconds=3)

        # Guild Supremacy
        self.click_xy(770, 1830, seconds=4)
        if self.is_visible("labels/guild_supremacy"):
            self.click_xy(530, 1820, seconds=2)  # Tap to Close
            self.click_xy(1000, 100)
            if self.is_visible("labels/guild_medal_reward"):
                self.click_xy(530, 1820, seconds=2)  # Tap to Close
                self.logger.info("Daily Guild Supremacy rewards collected!")
            else:
                self.logger.info("Guild Supremacy rewards not found, recovering..")
                self.recover()
        else:
            self.logger.info("Guild Supremacy contribution screen not found!")

        # # Timeless Gala
        # if is_visible('events/timeless_gala_active', seconds=2) or is_visible('events/timeless_gala_inactive', click=True, seconds=2):
        #     click_xy(750, 750, seconds=2)
        #     while is_visible('events/collect_gala', region=[650, 1100, 400, 550]):
        #         click('events/collect_gala')
        #     self.logger.info('Timeless Gala claimed')
        #
        # # All Heroes
        # if is_visible('events/all_heroes', seconds=2) or is_visible('events/all_heroes_inactive', click=True, seconds=2):
        #     if is_visible('events/all_heroes_claim', click=True, confidence=0.8, retry=10, yrelative=100):
        #         self.logger.info('All Heroes claimed')
        #         click_location('neutral')
        #
        # # Swipe left for the next events
        # swipe(1000, 1800, 250, 1800, 500, seconds=2)
        #
        # # Swallows Retreat
        # if is_visible('events/swallows_retreat_inactive', click=True, seconds=2, region=self.metadata.regions['bottom_buttons']):
        #     click_xy(350, 1250) # Daily
        #     while is_visible('events/collect_sr'):
        #         click('events/collect_sr')
        #     click_xy(800, 1250) # Special
        #     while is_visible('events/collect_sr'):
        #         click('events/collect_sr')
        #     self.logger.info('Swallows Retreat claimed')
        #
        # # Fishing Diary
        # if is_visible('events/fishing_diary_inactive', click=True, seconds=3, region=self.metadata.regions['bottom_buttons']):
        #     if is_visible('buttons/collect', click=True, confidence=0.8):
        #         self.logger.info('Fishing Diary claimed')
        #
        # click('buttons/back', region=self.metadata.regions['back'])
        # click('buttons/back', region=self.metadata.regions['back'])
        if self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="close"
        ):
            self.logger.info("Events claimed!\n")

    def formation_handler(
        self, formation_number: int = 1, already_open: bool = False
    ) -> None:
        """
        Loads a specified hero formation and handles any unowned hero pop-ups.

        This function navigates to the formations menu and attempts to load the specified formation
        by its number. If any heroes or artifacts in the formation are not owned, it will try the next
        formation. If no formation succeeds, it logs the issue.

        Args:
            formation_number (int): The formation number to load. Defaults to 1.
            already_open (bool): Whether the formations menu is already open. Defaults to False.
        """
        if self.metadata.load_formations is False:
            self.logger.info("Formation loading disabled")
            return

        if self.metadata.formation > 7:
            self.logger.info(
                "Formation selected higher than 7, starting from 1 again.."
            )
            self.metadata.formation = 1

        self.logger.info(
            "Loading formation #" + str(math.trunc(self.metadata.formation))
        )
        counter = 1
        unowned_counter = 0
        self.wait()
        if already_open is False:  # Sometimes we're already in the formations menu
            self.click("buttons/records", seconds=3)
        while counter != formation_number:
            self.click_xy(1000, 1025)
            counter += 1

        self.click("buttons/copy", seconds=2)
        # Handle 'Hero not owned' popup
        if self.is_visible("labels/not_owned"):
            while self.is_visible(
                "labels/not_owned"
            ):  # Try next formation and check again
                self.logger.info("Hero/Artifact not owned, trying next formation..")
                self.click_xy(360, 1250)
                self.click_xy(1000, 1025)
                self.click("buttons/copy")
                self.metadata.formation += 1
                unowned_counter += 1
                if unowned_counter > 7:
                    self.logger.info("All formations contained an unowned hero!")
                    self.click_location(
                        "neutral"
                    )  # Close windows back to battle screen
                    self.click_location(
                        "neutral"
                    )  # Close windows back to battle screen
                    break
        self.click("buttons/confirm", suppress=True, seconds=0)

    def blind_push(
        self,
        mode: str,
        running=None,
        tower=None,
        load_formation: bool = True,
    ) -> None:
        """Pushes a specified game mode until defeat or some other condition, then automatically
        switches to the next mode. Currently supports 'daily_towers', 'push_tower', 'abyss',
        'dream_realm', and 'afkstages'.

        Args:
            mode (str): The game mode to push. Currently supports 'daily_towers', 'push_tower',
                        'abyss', 'dream_realm', and 'afkstages'.
            running (bool): A boolean indicating whether or not the script is currently running.
            tower (str): The name of the tower to push if mode is 'push_tower'.
            load_formation (bool): Whether or not to load a new hero formation before pushing.
        """
        # Opens first found tower and pushes until defeat, then exits
        if mode == "daily_towers":
            self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="open"
            )
            self.logger.info("Pushing tower until first defeat")
            self.click_xy(460, 1820, seconds=2)
            self.click("labels/legend_trial", seconds=3, retry=3)
            self.click_location("neutral")  # To clear District popup

            factions = ["Light", "Wilder", "Graveborn", "Mauler"]
            for faction in factions:
                if self.is_visible(
                    "towers/" + faction.lower(),
                    confidence=0.94,
                    click=True,
                    seconds=4,
                    y_relative=-20,
                ):
                    self.logger.info("Opening " + faction + " tower\n")
                    if self.is_visible(
                        "towers/lvl",
                        click=True,
                        region=(15, 850, 1050, 800),
                        seconds=3,
                        y_relative=-50,
                        grayscale=True,
                    ):
                        if self.is_visible("buttons/battle"):
                            self.formation_handler()
                            self.click("buttons/battle")
                            while True:
                                if self.is_visible(
                                    "buttons/next",
                                    click=True,
                                    retry=3,
                                    seconds=5,
                                    region=self.metadata.regions["bottom_buttons"],
                                ):
                                    self.logger.info(
                                        faction + " win detected, moving to next floor"
                                    )
                                    self.click("buttons/battle", retry=5)
                                elif self.is_visible(
                                    "buttons/retry",
                                    region=self.metadata.regions["bottom_buttons"],
                                ):
                                    self.logger.info(faction + " defeat!")
                                    self.click("buttons/back")
                                    self.click("buttons/back")
                                    break
                                self.wait(5)
                    else:
                        self.logger.info("Tower floor not found!")
                        break

            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Towers pushed!\n")

        # Loads a tower and keeps retrying until victory, repeating for the next stage infinitely
        if mode == "push_tower":
            self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="open"
            )

            self.logger.info("Pushing " + tower.capitalize() + " tower!\n")
            self.click_xy(460, 1820, seconds=4)
            self.click("labels/legend_trial", seconds=2)

            factions = ["graveborn", "light", "mauler", "wilder"]
            for faction in factions:
                if faction == tower:
                    if self.is_visible(
                        "towers/" + faction.lower(),
                        confidence=0.95,
                        click=True,
                        seconds=4,
                        y_relative=-20,
                    ):
                        if self.is_visible(
                            "towers/lvl",
                            click=True,
                            region=(15, 850, 1050, 800),
                            seconds=3,
                            y_relative=-50,
                            grayscale=True,
                        ):
                            self.formation_handler()
                            while True:
                                self.click(
                                    "buttons/battle",
                                    suppress=True,
                                    region=self.metadata.regions["bottom_buttons"],
                                )
                                if self.is_visible(
                                    "buttons/next",
                                    click=True,
                                    seconds=4,
                                    region=self.metadata.regions["bottom_buttons"],
                                ):
                                    self.logger.info(
                                        faction.capitalize()
                                        + " win detected, moving to next floor\n"
                                    )
                                    self.metadata.stage_defeats = 0
                                    self.formation_handler()
                                if self.is_visible(
                                    "buttons/retry",
                                    click=True,
                                    region=self.metadata.regions["bottom_buttons"],
                                ):
                                    # Increment defeats
                                    self.metadata.stage_defeats += 1
                                    # If were past the defeat cap handle formation change, else standard log output
                                    if (
                                        self.metadata.stage_defeats >= 1
                                        and self.metadata.stage_defeats
                                        % self.config.getint("PUSHING", "defeat_limit")
                                        == 0
                                    ):
                                        self.metadata.formation = (
                                            self.metadata.stage_defeats
                                            / self.config.getint(
                                                "PUSHING", "defeat_limit"
                                            )
                                        ) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                                        self.logger.info(
                                            str(self.metadata.stage_defeats)
                                            + " defeats, trying next formation"
                                        )
                                        self.wait()
                                        self.formation_handler(self.metadata.formation)
                                    else:
                                        self.logger.info(
                                            "Defeat #"
                                            + str(self.metadata.stage_defeats)
                                            + "! Retrying"
                                        )

            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Towers pushed!\n")

        # Retries Abyss stages, probably very outdated at this point
        if mode == "abyss":
            victory_counter = 0
            self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="open"
            )
            self.logger.info("Auto-retrying Trial of Abyss")
            self.click(
                "buttons/main_menu",
                region=self.metadata.regions["main_menu"],
                seconds=3,
            )
            if self.is_visible("buttons/trial_of_abyss", click=True):
                pass
            else:
                self.click(
                    "buttons/event",
                    region=self.metadata.regions["menu_activities"],
                    seconds=3,
                )
                while not self.is_visible(
                    "events/abyss", region=self.metadata.regions["bottom_third"]
                ):
                    self.swipe(700, 1800, 250, 1800, 2000)
                self.click("events/abyss", region=self.metadata.regions["bottom_third"])
                self.click(
                    "buttons/abyss_entry", region=self.metadata.regions["bottom_third"]
                )

            while self.is_visible(
                "labels/trial_of_abyss", click=True
            ):  # First click can claim loot so we loop it to make sure we're opening ToA
                while True:
                    if not running.is_set():
                        running.self.wait()  # wait until running is set
                        self.logger.info("Resuming")
                    self.click("buttons/abyss_lvl", seconds=0.2, suppress=True)
                    if self.is_visible(
                        "buttons/battle",
                        seconds=0.2,
                        click=True,
                        region=self.metadata.regions["bottom_buttons"],
                    ):
                        if victory_counter > 0 and victory_counter % 100 == 0:
                            self.logger.info(str(victory_counter) + " attempts made")
                        victory_counter += 1
                    self.click(
                        "labels/tap_to_close",
                        suppress=True,
                        seconds=0.2,
                        region=self.metadata.regions["bottom_buttons"],
                    )
                    if self.is_visible(
                        "buttons/next",
                        seconds=0.2,
                        click=True,
                        region=self.metadata.regions["bottom_buttons"],
                    ):
                        self.logger.info(
                            "Stage passed in " + str(victory_counter) + " attemps!"
                        )
                        victory_counter = 0
                    self.wait(2)
            else:
                self.logger.info("Something went wrong opening Trial of Abyss!")
                self.recover()

        # Runs all available DR attempts
        if mode == "dream_realm":
            self.logger.info("Using all Dream Realm attempts")
            self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="open"
            )
            dr_counter = 0

            self.click_xy(450, 1825, seconds=3)
            self.click(
                "buttons/dream_realm",
                region=self.metadata.regions["battle_modes"],
                seconds=3,
            )

            # 20 Attempts
            for _ in range(19):
                # Handle opening the Battle
                if self.is_visible(
                    "buttons/battle",
                    region=self.metadata.regions["bottom_buttons"],
                    click=True,
                    seconds=5,
                ):  # Enter battle screen
                    # Purchase Gold Attempts if it pops up
                    if self.is_visible(
                        "buttons/confirm",
                        click=True,
                        region=self.metadata.regions["confirm_deny"],
                    ):
                        self.click(
                            "buttons/battle",
                            region=self.metadata.regions["bottom_buttons"],
                            retry=2,
                            seconds=5,
                        )  # 2 retries or it catches the button on the next screen and breaks battle detection
                    # Start the Battle
                    self.logger.info("Starting Battle")
                    if self.is_visible(
                        "buttons/battle",
                        region=self.metadata.regions["bottom_buttons"],
                        click=True,
                        seconds=5,
                        retry=5,
                    ):
                        # If button is still visible after pressing we're out of attempts
                        if self.is_visible(
                            "buttons/battle",
                            region=self.metadata.regions["bottom_buttons"],
                        ):  # Start battle
                            self.logger.info("Out of attempts! Exiting..\n")
                            return
                        # When we haven't seen the x3 button three times in a row we can assume the battle is over
                        while dr_counter < 3:
                            if self.is_visible(
                                "buttons/skip_inverse",
                                seconds=0,
                                region=self.metadata.regions["x3_and_skip"],
                            ):
                                self.click(
                                    "buttons/skip_inverse",
                                    seconds=2,
                                    region=self.metadata.regions["x3_and_skip"],
                                )
                                self.click(
                                    "buttons/confirm",
                                    seconds=3,
                                    region=self.metadata.regions["confirm_deny"],
                                    suppress=True,
                                )
                                self.logger.info("Skip available, skipping the fight")
                                dr_counter = 0
                            else:
                                dr_counter += 1
                        self.click(
                            "labels/tap_to_close",
                            region=self.metadata.regions["bottom_buttons"],
                            seconds=5,
                            retry=10,
                            confidence=0.8,
                        )
                        if self.is_visible("buttons/deny", click=True, seconds=3):
                            self.logger.info("Skipping formation sharing..")
                            self.click(
                                "labels/tap_to_close",
                                region=self.metadata.regions["bottom_buttons"],
                                seconds=5,
                                suppress=True,
                            )
                        self.logger.info(
                            "Dream Realm Battle #" + str(_ + 1) + " complete!"
                        )
                        dr_counter = 0
                else:
                    self.logger.info("Battle button not found! (battle " + str(_) + ")")
                    self.debug_screen("dr_battle_not_found")

            if self.safe_open_and_close(
                name=inspect.currentframe().f_code.co_name, state="close"
            ):
                self.logger.info("Dream Realm attempts exhausted.\n")

        # For pushing afk stages
        if mode == "afkstages":
            timeout = 0
            if self.is_visible(
                "buttons/records",
                region=self.metadata.regions["bottom_buttons"],
                seconds=0,
                retry=20,
            ):

                # Change formation if we we beat the 2nd round or have defeat >10 times in a row
                if (
                    load_formation is True
                    or self.metadata.stage_defeats
                    >= self.config.getint("PUSHING", "defeat_limit")
                ):
                    # More than 10 defeats in a row and a multiple of 10 (i.e load new formation on 10th/20th/30th etc defeat)
                    if (
                        self.metadata.stage_defeats >= 1
                        and self.metadata.stage_defeats
                        % self.config.getint("PUSHING", "defeat_limit")
                        == 0
                    ):
                        self.metadata.formation = (
                            self.metadata.stage_defeats
                            / self.config.getint("PUSHING", "defeat_limit")
                        ) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                        self.logger.info(
                            str(self.metadata.stage_defeats)
                            + " defeats, trying next formation"
                        )
                        self.formation_handler(self.metadata.formation)
                        if (
                            self.metadata.first_stage_won is True
                        ):  # Manually select second round if we've won the first
                            self.wait()  # To stop getting stuck if this buttons not pressed
                            self.click_xy(550, 1100)
                    elif load_formation is True:
                        self.formation_handler(self.metadata.formation)

                # Season 3 single stage code

                # Start Battle
                self.click(
                    "buttons/battle",
                    retry=5,
                    region=self.metadata.regions["bottom_buttons"],
                    seconds=0,
                )
                self.click("buttons/confirm", seconds=0, suppress=True)
                self.wait(
                    5
                )  # Long wait to stop false positives from the back button on the battle selection screen

                # Wait til we see the back button in the post battle screen before running next checks
                while not self.is_visible(
                    "buttons/back",
                    region=self.metadata.regions["bottom_buttons"],
                    seconds=2,
                ):
                    timeout += 1
                    if (
                        timeout > 30
                    ):  # If nothing at 30 seconds start clicking in case battery saver mode is active
                        self.click_location("neutral")
                    if (
                        timeout > 60
                    ):  # Still nothing at 60 seconds? Quit as somethings gone wrong
                        self.logger.info("Battle timeout error!")
                        break

                # Post battle screen detection
                result = ""
                while result == "":
                    # Loop the different scenarios until we get an image match ('retry' is defeat, 'battle' is normal stage victory, 'talent_trials' is talent stage victory)
                    images = [
                        "buttons/retry",
                        "buttons/battle",
                        "buttons/talent_trials",
                    ]
                    result = self.is_visible_array(
                        images,
                        confidence=0.9,
                        seconds=0,
                        retry=1,
                        click=True,
                        region=self.metadata.regions["bottom_buttons"],
                    )

                # Retry button indicates defeat, we run the defeat logic
                if result == "buttons/retry":
                    self.metadata.stage_defeats += 1
                    self.logger.info(
                        "Defeat #" + str(self.metadata.stage_defeats) + "! Retrying"
                    )
                    self.blind_push("afkstages", load_formation=False)

                # The other two mean we have a victory
                elif result == "buttons/battle" or result == "buttons/talent_trials":
                    self.metadata.stage_defeats = 0  # Reset defeats
                    self.metadata.formation = 1  # Reset formation
                    self.logger.info("Victory! Stage passed\n")
                    self.metadata.first_stage_won = False
                    self.blind_push("afkstages", load_formation=True)
            else:
                self.logger.info("Something went wrong opening AFK Stages!")
                self.save_screenshot("afk_stage_error")
                self.recover()

    def open_afk_stages(self, afkstages: bool = True) -> None:
        """Opens the AFK or Talent Stages based on the provided flag.

        This method navigates to the AFK Stages or Talent Stages in the game. It logs the
        process of opening the stages and handles any necessary confirmation prompts. The
        method changes formations after a specified number of defeats, as configured.

        Args:
            afkstages (bool): If True, opens the standard AFK Stages. If False, opens the
                            Talent Stages.
        """
        # Open afk stage screen without prompting loot if it's >1h uncollected
        self.click_xy(450, 1825, seconds=3)
        self.click(
            "buttons/afk_stage", region=self.metadata.regions["battle_modes"], seconds=4
        )

        if afkstages is True:  # Standard Stage
            self.logger.info("Opening AFK Stages")
            self.logger.info(
                "Changing formations after "
                + str(self.config.getint("PUSHING", "defeat_limit"))
                + " defeats\n"
            )
            # 3 clicks, first can collect loot, second can prompt 'Are you sure?' popup, 3rd opens stages for sure.
            self.click_xy(715, 1600, seconds=2)  # AFK Stage button
            self.click("buttons/confirm", suppress=True)
        else:  # Talent Stage
            self.logger.info("Opening Talent Stages")
            self.logger.info(
                "Changing formations after "
                + str(self.config.getint("PUSHING", "defeat_limit"))
                + " defeats\n"
            )
            self.click_xy(370, 1600, seconds=2)  # AFK Stage button
            self.click("buttons/confirm", suppress=True)

    def afk_stage_chain_proxy(self) -> None:
        """Starts an AFK Stage chain by attempting to start the stage and then
        automatically retrying upon defeat. The method changes formations after
        a specified number of defeats, as configured.

        This method is a proxy to the `blind_push` method with the "afkstages"
        argument set to True. It is intended to be used for convenience.
        """
        self.formation_handler()
        self.click(
            "buttons/battle",
            retry=1,
            suppress=True,
            seconds=0,
            region=self.metadata.regions["bottom_third"],
        )
        self.click("buttons/confirm", retry=1, suppress=True, seconds=0)
        while True:
            # Victory Logic
            if self.is_visible("buttons/next", retry=1, click=True, seconds=3):
                self.click(
                    "buttons/battle",
                    retry=1,
                    suppress=True,
                    seconds=5,
                    region=self.metadata.regions["bottom_third"],
                )
                self.logger.info("Victory!\n")
                self.metadata.stage_defeats = 0
                self.formation_handler()
                self.click(
                    "buttons/battle",
                    retry=1,
                    suppress=True,
                    seconds=0,
                    region=self.metadata.regions["bottom_third"],
                )
                self.click("buttons/confirm", retry=1, suppress=True, seconds=0)
            # Defeat logic
            if self.is_visible(
                "buttons/retry",
                retry=1,
                click=True,
                seconds=4,
                region=(650, 1750, 200, 150),
            ):
                # Increment defeats
                self.metadata.stage_defeats += 1
                # If were past the defeat cap handle formation change, else standard log output
                if (
                    self.metadata.stage_defeats >= 1
                    and self.metadata.stage_defeats
                    % self.config.getint("PUSHING", "defeat_limit")
                    == 0
                ):
                    self.metadata.formation = (
                        self.metadata.stage_defeats
                        / self.config.getint("PUSHING", "defeat_limit")
                    ) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                    self.logger.info(
                        str(self.metadata.stage_defeats)
                        + " defeats, trying next formation"
                    )
                    self.formation_handler(self.metadata.formation)
                    self.click("buttons/battle", retry=1, suppress=True, seconds=0)
                    self.click("buttons/confirm", retry=1, suppress=True, seconds=0)
                else:
                    self.logger.info(
                        "Defeat #" + str(self.metadata.stage_defeats) + "! Retrying"
                    )
                    self.click(
                        "buttons/battle",
                        suppress=True,
                        seconds=0,
                        region=self.metadata.regions["bottom_third"],
                    )
                    self.click("buttons/confirm", suppress=True, seconds=0)

    def handle_charms(self) -> None:
        """Handles Dura's Trials by checking the top and bottom rows for
        Dawnrise and Nightmare battles. The method changes formations after
        a specified number of defeats, as configured. If a battle is found, it
        attempts to start the battle and then automatically retry upon defeat.
        The method logs the process of handling the Charm Trials and handles any
        necessary confirmation prompts.
        """

        def go_back(exit_mode: bool = False) -> None:
            """Navigates back from the Charm Trials screen.

            If exit_mode is set to True, it will also exit the Charm Trials menu.
            This is useful when handling the exit from the Charm Trials after a
            series of battles. Otherwise, it will only go back to the main Charm
            Trials menu.

            Args:
                exit_mode (bool): If True, it will also exit the Charm Trials menu.
            """
            self.click("buttons/confirm", suppress=True)
            self.click(
                "buttons/back2",
                suppress=True,
                region=self.metadata.regions["bottom_buttons"],
            )
            if exit_mode is True:
                self.click("buttons/back", suppress=True)
                self.click("buttons/back2", suppress=True)

        def handle_battle(floor_type: str = "") -> None:
            """Handles the battle process for Dura's Trials.

            This method repeatedly attempts to start a battle and processes the result.
            It checks for available attempts, handles different victory screens based on
            the floor type, and manages retries upon defeat. For each defeat, it increments
            a counter and changes the formation when a specified defeat limit is reached.

            Args:
                floor_type (str): The type of floor being battled, either "dawnrise" or
                "nightmare". This determines the specific victory screen handling and exit
                strategy.
            """
            while True:
                self.click("buttons/battle", retry=1, suppress=True, seconds=0)
                if self.is_visible("labels/multiple_attempts", seconds=0):
                    self.logger.info("Out of tries!\n")
                    self.click("buttons/confirm")
                    if (
                        floor_type == "nightmare"
                    ):  # Exit back to charm row selection screen
                        self.click("buttons/back", suppress=True, seconds=2)
                        self.click("buttons/back2", suppress=True, seconds=2)
                    else:  # Else just exit back to the Dawnrise/Nightmare screen to we can naviate to Nightmare next
                        self.click("buttons/back", suppress=True, seconds=2)
                    break
                self.click("buttons/confirm", retry=1, suppress=True, seconds=0)
                if self.is_visible(
                    "buttons/retry",
                    retry=1,
                    click=True,
                    seconds=4,
                    region=(650, 1750, 200, 150),
                ):
                    # Increment defeats
                    self.metadata.stage_defeats += 1
                    # If were past the defeat cap handle formation change, else standard log output
                    if (
                        self.metadata.stage_defeats >= 1
                        and self.metadata.stage_defeats
                        % self.config.getint("PUSHING", "defeat_limit")
                        == 0
                    ):
                        self.metadata.formation = (
                            self.metadata.stage_defeats
                            / self.config.getint("PUSHING", "defeat_limit")
                        ) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                        self.logger.info(
                            "Defeat #"
                            + str(self.metadata.stage_defeats)
                            + " trying next formation"
                        )
                        self.formation_handler(self.metadata.formation)
                    else:
                        self.logger.info(
                            "Defeat #" + str(self.metadata.stage_defeats) + " Retrying"
                        )
                # Handle different victory screens for Dawnrise/Nightmare
                if floor_type == "dawnrise":
                    if self.is_visible("buttons/next2", retry=1, click=True, seconds=5):
                        self.logger.info("Victory!\n")
                        self.metadata.stage_defeats = 0
                        self.formation_handler()
                    if self.is_visible("buttons/retry2", retry=1, seconds=5):
                        self.logger.info("Victory! Highest stage cleared!\n")
                        self.click("buttons/back", suppress=True, seconds=2)
                        break
                elif floor_type == "nightmare":
                    if self.is_visible(
                        "buttons/continue_green",
                        retry=1,
                        click=True,
                        seconds=5,
                        grayscale=False,
                        confidence=0.95,
                    ):  # High confidence so we don't catch the greyscale version
                        self.logger.info("Victory!\n")
                        self.metadata.stage_defeats = 0
                        self.formation_handler()
                    if self.is_visible(
                        "buttons/continue_green", retry=1, click=True, seconds=5
                    ):
                        self.logger.info("Victory! Highest stage cleared!\n")
                        self.click("buttons/back", suppress=True, seconds=2)
                        self.click("buttons/back2", suppress=True, seconds=2)

        # Open Trials screen
        self.logger.info("Running Dura's Trials!\n")
        self.wait(1)
        self.click_xy(450, 1825, seconds=3)
        self.click(
            "buttons/duras_trials",
            region=self.metadata.regions["battle_modes"],
            seconds=3,
            retry=5,
        )

        # Clear popups
        self.click_xy(550, 1800, seconds=2)
        self.click_xy(550, 1800, seconds=2)

        if self.is_visible(
            "buttons/featured_heroes",
            retry=5,
            region=self.metadata.regions["top_third"],
        ):

            # TODO Rewrite using self.metadata.regions for the 6 charm stages, to better handle duplicate code for top/bottom row

            # Check top row
            self.logger.info("Checking top row Charm Trials..")
            self.metadata.stage_defeats = 0
            if self.is_visible(
                "buttons/rate_up",
                grayscale=True,
                click=True,
                region=(50, 1175, 950, 150),
                confidence=0.75,
                seconds=4,
            ):

                # Handle top row Dawnrise
                self.logger.info("Checking Dawnrise")
                self.click_xy(400, 1800, seconds=7)
                if self.is_visible(
                    "buttons/sweep",
                    seconds=0,
                    retry=2,
                    region=self.metadata.regions["bottom_third"],
                ):
                    self.logger.info("Max Dawnrise floor reached!\n")
                else:
                    if self.is_visible(
                        "buttons/battle",
                        click=True,
                        seconds=6,
                        region=self.metadata.regions["bottom_third"],
                    ):
                        self.logger.info("Dawnrise battle found!\n")
                        self.formation_handler(self.metadata.formation)
                        handle_battle(floor_type="dawnrise")

                # Handle top row Nightmare
                self.logger.info("Checking Nightmare")
                self.click_xy(830, 1800, seconds=7)
                if self.is_visible(
                    "buttons/battle",
                    click=True,
                    seconds=6,
                    region=self.metadata.regions["bottom_third"],
                ):
                    self.formation_handler(self.metadata.formation)
                    handle_battle(floor_type="nightmare")
                else:
                    self.logger.info("Max Nightmare floor reached!\n")
                    self.click("buttons/back2", suppress=True, seconds=2)
            else:
                self.logger.info("Top row not found..")

            # Check bottom row
            self.logger.info("Checking bottom row Charm Dawnrise Trials..")
            self.metadata.stage_defeats = 0
            self.metadata.formation = 1  # Reset on new levels
            if self.is_visible(
                "buttons/rate_up",
                grayscale=True,
                click=True,
                region=(50, 1400, 950, 150),
                confidence=0.75,
                seconds=3,
            ):

                # Handle bottom row Dawnrise
                self.logger.info("Checking Dawnrise")
                self.click_xy(400, 1800, seconds=7)
                if self.is_visible(
                    "buttons/sweep",
                    seconds=0,
                    retry=2,
                    region=self.metadata.regions["bottom_third"],
                ):
                    self.logger.info("Max Dawnrise floor reached!\n")
                else:
                    if self.is_visible(
                        "buttons/battle",
                        click=True,
                        seconds=6,
                        region=self.metadata.regions["bottom_third"],
                    ):
                        self.logger.info("Dawnrise battle found!\n")
                        self.formation_handler(self.metadata.formation)
                        handle_battle(floor_type="dawnrise")

                # Handle bottom row Nightmare
                self.logger.info("Checking Nightmare")
                self.click_xy(830, 1800, seconds=7)
                if self.is_visible(
                    "buttons/battle",
                    click=True,
                    seconds=6,
                    region=self.metadata.regions["bottom_third"],
                ):
                    self.formation_handler(self.metadata.formation)
                    handle_battle(floor_type="nightmare")
                else:
                    self.logger.info("Max Nightmare floor reached!\n")
                    go_back(exit_mode=True)
            else:
                self.logger.info("Bottom row not found..")
        else:
            self.logger.info("Something went wrong opening Dura's Trials!")
            self.recover()

        if self.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="close"
        ):
            self.logger.info("Dura's Trials ran!\n")

    def quest_push(self) -> None:
        """Scans and pushes the various buttons needed to complete story/side quests
        Very slow, can get stuck if there is a player present at an end point and we get the magnifying glass icon instead of the action icon
        The order of checks and clicks is important to not get stuck in loops
        TODO Get chest icon for collecting quest items / First run teleport prompt
        """
        self.logger.info("Pushing Quests!\n")
        # The order of these is important
        buttons = [
            "buttons/battle",
            "buttons/skip",
            "buttons/dialogue_option",
            "buttons/confirm",
            "buttons/red_dialogue",
            "buttons/dialogue_coe",
            "buttons/blue_dialogue",
            "buttons/interact",
            "buttons/dialogue",
            "buttons/tap_and_hold",
            "buttons/enter",
            "buttons/chest",
            "buttons/battle_button",
            "labels/questrewards",
            "labels/tap_to_close",
            "buttons/track",
            "labels/coe",
        ]

        while True:
            self.click_array(buttons, suppress=True, confidence=0.91)
            if self.is_visible(
                "buttons/tap_and_hold",
                region=self.metadata.regions["chat_window"],
                seconds=0,
            ):
                self.logger.info("Holding button")
                self.swipe(550, 1250, 550, 1250, 4000)  # Hacky way to hold it down
            if self.is_visible(
                "labels/time_change",
                region=self.metadata.regions["chat_window"],
                seconds=0,
                y_relative=620,
                click=True,
            ):
                self.logger.info("Time changed!")
                self.wait(4)

    def fishing(self) -> None:
        """Farms the fishing.
        An experimental feature for AutoAFK2. Currently not completely implemented.
        
        The overall logic as follows:
        1. **Open and choose a map**
            1. click upper right corner to open map
            2. click Starter Story
            3. if found "check" button then click it. (character currently not in Starter Story maps)
            4. swipe from left to right, homing the location of submaps
            5. click the first submap
        2. **Find fishing spot**
            1. if found any available fishing spot then click it.
            2. click "goto" button
            3. wait until the "fishing_cast" button shows up. This means the character has arrived at the spot and start fishing.
        3. **Fishing activity**
            1. wait until "fishing_cast" or "fishing_pull" or "fishing_locked" buttons shows up then apply corresponding logic.
            2. (see the fishing logic in following comments, which inspired by the so called "bang-bang control")
        """

        self.logger.info("Farming fishing!\n")
        self.click_xy(880, 200, seconds=3)      # Open map
        self.click_xy(400, 1800, seconds=3)     # Select Starter Story
        self.swipe(400, 1600, 1000, 1600, 500)  # "Homing" sub-maps
        self.click_xy(170, 1600, seconds=3)     # Select first sub-map, TODO: add support for iterating through all sub-maps

        # Find fishing spot
        spot = self.is_visible_array(
            ["buttons/fishing_available_collected_spot",    # 100% collected spots
             "buttons/fishing_available_spot"],             # Available spots
            confidence=0.9,
            seconds=3,
        )

        if spot != "not_found":
            self.logger.info("Fishing spot found\n")
            self.click(spot, confidence=0.9, seconds=3)     # Click the spot
            self.click("buttons/goto", seconds=3)           # Click "goto" button
            
            # Wait until the "fishing_cast" button shows up with limited patience and click it
            for _ in range(20):
                self.wait(1)
                if self.is_visible("buttons/fishing_cast", confidence=0.9, seconds=0) or \
                   self.is_visible("buttons/fishing_pull", confidence=0.9, seconds=0):
                    break

            # Fishing activity
            while True:
                if self.is_visible("buttons/fishing_cast", confidence=0.9, seconds=0, click=True):
                    self.logger.info("Fish caught!, cast again!\n")

                elif self.is_visible("buttons/fishing_pull", confidence=0.9, seconds=0, click=True):
                    self.logger.info("Start fighting!\n")

                    # The following logic is inspired by the so called "bang-bang control"
                    while not self.is_visible("buttons/fishing_cast", confidence=0.9, seconds=0):
                        if self.is_visible("buttons/fishing_skill", confidence=0.9, seconds=0, click=True):
                            # cast the skill, this will be the major contributor under the fishing logic
                            pass
                        elif self.is_visible("buttons/fishing_in_range", confidence=0.9, seconds=0):
                            # do nothing, let the hook go left
                            pass
                        elif self.is_visible("buttons/fishing_cast", confidence=0.9, seconds=0):
                            self.logger.info("Fish caught!, cast again!\n")
                            break
                        else:
                            # TODO: press the "fishing_pull" button, move the hook righ until its in the "circle". (I'm not sure how to do "press" in the current framework)
                            pass
                        self.wait(1) # if there's any way to decrease the waiting time, it would be better (e.g. directly call `time.sleep()`)

                elif self.is_visible("buttons/fishing_locked", confidence=0.9, seconds=0):
                    self.logger.info("Spot locked!\n")

                else:
                    self.logger.info("Something went wrong!\n")
                
                self.wait(1)

        else:
            self.logger.info("No fishing spots found\n")

        self.logger.info("Fishing farmed!\n")