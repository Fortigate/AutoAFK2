import ctypes
import inspect
import logging
import time
from argparse import Namespace
from consolemenu import SelectionMenu
from logging import Logger, StreamHandler

from automation import utility
from automation.afkj_automation import AFKJAutomation
from metadata.afkj_metadata import AFKJMetadata


def main() -> None:
    """Run AFKJ Automation."""
    args: Namespace = utility.parse_arguments()
    logger: Logger = utility.init_logging()
    config, settings = utility.read_config(args.config)

    afkj = AFKJMetadata(server=args.server)
    bot = AFKJAutomation(config=config, logger=logger, metadata=afkj)

    # Boot up text
    logger.info("Loaded settings file: " + str(settings.split("\\")[-1]))
    logger.info("Version: " + afkj.version)

    # Nice name for the window and debugging peoples screenshots
    ctypes.windll.kernel32.SetConsoleTitleW("AutoAFK2 v" + afkj.version)

    # Boot up activities before tasks are ran
    bot.connect()
    bot.resolution_check()
    if not args.proxy:
        bot.wait_until_game_active()

    # TODO single SA battle and daily GS collection
    def dailies():
        # start_autoprogress()
        if config.getboolean("ACTIVITIES", "claim_afk"):
            bot.claim_afk_rewards()
        if config.getboolean("ACTIVITIES", "friend_points"):
            bot.friend_points_collect()
        if config.getboolean("ACTIVITIES", "mail_collect"):
            bot.mail_connect()
        if config.getboolean("ACTIVITIES", "emporium_purchases"):
            bot.emporium_purchases()
        if config.getboolean("ACTIVITIES", "single_recruit"):
            bot.single_recruit()
        if config.getint("ACTIVITIES", "arena_battles") > 0:
            bot.arena(config.getint("ACTIVITIES", "arena_battles"))
        if config.getboolean("ACTIVITIES", "dream_realm"):
            bot.dream_realm()
        if config.getboolean("ACTIVITIES", "push_towers"):
            bot.blind_push("daily_towers")
        if config.getboolean("ACTIVITIES", "collect_quests"):
            bot.collect_quests()
        if config.getboolean("ACTIVITIES", "claim_events"):
            bot.claim_events()
        if config.getboolean("ACTIVITIES", "noble_path"):
            bot.noble_path()
        if config.getboolean("ACTIVITIES", "level_up"):
            bot.level_up()
        if config.getboolean("ACTIVITIES", "push_dream_realm"):
            bot.blind_push("dream_realm")
        if config.getboolean("ACTIVITIES", "farm_affinity"):
            bot.farm_affinity()
        logger.info("Dailies done!")

    # Handle launch arguments
    if args.forceprint:
        # Define a custom logging handler that duplicates log messages to stdout
        class DuplicatedStdoutHandler(StreamHandler):
            def emit(self, record):
                print(self.format(record))

        stdout_handler = DuplicatedStdoutHandler()
        stdout_handler.setLevel(logging.INFO)
        logger = logging.getLogger(__name__)
        logger.addHandler(stdout_handler)
        logger.propagate = False

    if args.dailies:
        logger.info("Running Dailies\n")
        dailies()

    if args.teamup:
        logger.info("Starting up team-up farming")
        start_time = time.time()
        limit_minutes = config.getint("ACTIVITIES", "teamup_limit")

        if limit_minutes == 0:
            limit = float("inf")
            logger.info("Time limit: Indefinite\n")
        else:
            limit = limit_minutes * 60
            logger.info(f"Time remaining: {limit_minutes} minutes")
            logger.info("Time limit can be configured in settings.ini\n")

        while time.time() - start_time < limit:
            bot.team_up()

    if args.abyss:
        logger.info("Opening Trials of Abyss")
        bot.blind_push("abyss")

    if args.legend:
        bot.blind_push("towers")

    if args.quest:
        bot.quest_push()

    if args.dream:
        bot.blind_push("dream_realm")

    if args.test:
        bot.noble_path()

    if args.charms:
        bot.handle_charms()

    if args.proxy:
        logger.info("\n")
        logger.info("Starting up Chain Proxy farming\n")
        bot.afk_stage_chain_proxy()

    if args.afks:
        bot.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        bot.open_afk_stages(afkstages=True)
        bot.blind_push("afkstages")

    if args.afkt:
        bot.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        bot.open_afk_stages(afkstages=False)
        bot.blind_push("afkstages")

    if args.fish:
        bot.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        bot.fishing()

    # If no function launch argument we pop the UI
    options = [
        "Run Dailies",
        "Push Towers",
        "Push AFK Stages",
        "Push AFK Talent Stages",
        "Push Dura's Trials",
        "Run Quests",
        "Use Dream Realm attempts",
        "Farm Team-Up Chat",
        "Farm Chain AFK Proxy Request",
    ]
    selection = SelectionMenu.get_selection(
        options,
        title="Welcome to AutoAFK2! Select an activity:",
        subtitle="Note that to stop a task or start a new one you have to restart the bot. Questions? Jc.2 @ Discord",
    )
    selection += 1  # Non-zero index to make things easier to read

    if selection == 1:
        dailies()

    if selection == 2:
        tower_menu = []
        open_towers = {
            1: ["Push Lightbringer Tower"],
            2: ["Push Mauler Tower"],
            3: ["Push Wilder Tower"],
            4: ["Push Graveborn Tower"],
            5: ["Push Lightbringer Tower", "Push Mauler Tower"],
            6: ["Push Wilder Tower", "Push Graveborn Tower"],
            7: [
                "Push Lightbringer Tower",
                "Push Wilder Tower",
                "Push Graveborn Tower",
                "Push Mauler Tower",
            ],
        }

        # Add tower to the list if it's unlocked
        for day, towers in open_towers.items():
            if afkj.current_time_utc.isoweekday() == day:
                tower_menu.extend(towers)
        selection = SelectionMenu.get_selection(tower_menu, title="Which Tower:")
        selection += 1  # Non-zero index to make things easier to read

        # SelectionMenu only returns an int so here's a hacky way to work out which tower was selected. It ain't pretty.
        if selection == 1:
            day = afkj.current_time_utc.isoweekday()
            if day == 1:
                bot.blind_push("push_tower", "light")
            if day == 2:
                bot.blind_push("push_tower", "mauler")
            if day == 3:
                bot.blind_push("push_tower", "wilder")
            if day == 4:
                bot.blind_push("push_tower", "graveborn")
            if day == 5:
                bot.blind_push("push_tower", "light")
            if day == 6:
                bot.blind_push("push_tower", "wilder")
            if day == 7:
                bot.blind_push("push_tower", "light")

        if selection == 2:
            day = afkj.current_time_utc.isoweekday()
            if day == 5:
                bot.blind_push("push_tower", "mauler")
            if day == 6:
                bot.blind_push("push_tower", "graveborn")
            if day == 7:
                bot.blind_push("push_tower", "wilder")

        if selection == 3:
            if day == 7:
                bot.blind_push("push_tower", "graveborn")

        if selection == 4:
            day = afkj.current_time_utc.isoweekday()
            if day == 7:
                bot.blind_push("push_tower", "mauler")

        if selection == 5:
            SelectionMenu.get_selection(
                options,
                title="Welcome to AutoAFK2! Select an activity:",
                subtitle="Note that to stop a task or start a new one you have to restart the bot. Questions? Jc.2 @ Discord",
            )
            selection += 1  # Non-zero index to make things easier to read

    if selection == 3:
        bot.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        logger.info("Auto-pushing AFK Stages")
        bot.open_afk_stages(afkstages=True)
        bot.blind_push("afkstages", load_formation=True)

    if selection == 4:
        bot.safe_open_and_close(
            name=inspect.currentframe().f_code.co_name, state="open"
        )
        logger.info("Auto-pushing AFK Talent Stages")
        bot.open_afk_stages(afkstages=False)
        bot.blind_push("afkstages", load_formation=True)

    if selection == 5:
        bot.handle_charms()

    if selection == 6:
        bot.quest_push()

    if selection == 7:
        bot.blind_push("dream_realm")

    if selection == 8:
        logger.info("Starting up team-up farming")
        start_time = time.time()
        limit_minutes = config.getint("ACTIVITIES", "teamup_limit")

        if limit_minutes == 0:
            limit = float("inf")
            logger.info("Time limit: Indefinite\n")
        else:
            limit = limit_minutes * 60
            logger.info(f"Time remaining: {limit_minutes} minutes")
            logger.info("Time limit can be configured in settings.ini\n")

        while time.time() - start_time < limit:
            bot.team_up()

    if selection == 9:
        logger.info("Starting up Chain Proxy farming")
        logger.info(
            "For this function you need to open the request yourself and start this function at the stage setup screen\n"
        )

        bot.afk_stage_chain_proxy()


if __name__ == "__main__":
    main()
