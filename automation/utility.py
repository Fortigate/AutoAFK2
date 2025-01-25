"""Utility functions."""

import argparse
import configparser
import logging
import os
import sys
import time


def parse_arguments() -> argparse.Namespace:
    """Parse automation arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    # Configure launch arguments
    parser = argparse.ArgumentParser()
    # Modes
    parser.add_argument(
        "-a",
        "--abyss",
        action="store_true",
        help="Run the Trial of Abyss retry function",
    )
    parser.add_argument(
        "-l",
        "--legend",
        action="store_true",
        help="Run the Legend Trials retry function",
    )
    parser.add_argument(
        "-t", "--teamup", action="store_true", help="Run the Team-up function"
    )
    parser.add_argument(
        "-d", "--dailies", action="store_true", help="Run the Dailies function"
    )
    parser.add_argument(
        "-q", "--quest", action="store_true", help="Runs the Quest running function"
    )
    parser.add_argument(
        "-dr", "--dream", action="store_true", help="Run the Dream Realm function"
    )
    parser.add_argument("-afks", action="store_true", help="Run AFK Stages")
    parser.add_argument("-afkt", action="store_true", help="Run AFK Talent Stages")
    parser.add_argument("-test", action="store_true", help="Used for testing functions")
    parser.add_argument(
        "-charms", action="store_true", help="Run the Dura's Trials function"
    )
    parser.add_argument(
        "-proxy", action="store_true", help="Run the Chain AFK Proxy function"
    )
    parser.add_argument(
        "-fs", "--formation_skip", action="store_true", help="Don't load formations"
    )
    # Configurations
    parser.add_argument(
        "-s",
        "--server",
        choices=["global", "vn"],
        default="global",
        help="Select alternative game servers",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="CONFIG",
        default="settings.ini",
        help="Define alternative settings file to load",
    )
    parser.add_argument("--forceprint", action="store_true", help="Force print output")

    return parser.parse_args()


def read_config(config_arg: str) -> tuple[configparser.ConfigParser, str]:
    """Read config file.

    Args:
        config_arg (str): Config file name.

    Returns:
        tuple[configparser.ConfigParser, str]: Configurations and settings.
    """
    # Get current directory
    config = configparser.ConfigParser()
    curr_dir: str = os.path.dirname(os.path.dirname(__file__))

    if getattr(sys, "frozen", False):
        curr_dir = os.path.dirname(sys.executable)

    settings = os.path.join(curr_dir, config_arg)
    config.read(settings)

    return (config, settings)


def init_logging() -> logging.Logger:
    """Initialize the logger.

    Returns:
        logging.Logger: Bot log.
    """
    logger = logging.getLogger("autoafk2")
    # File handler
    file_log_handler = logging.FileHandler(filename="autoafk2.log")
    logger.addHandler(file_log_handler)
    formatter = logging.Formatter("%(asctime)s %(message)s")
    file_log_handler.setFormatter(formatter)
    # STDERR handler so we don't lose that
    logging.StreamHandler(stream=sys.stderr)
    # Make timestamps etc look pretty
    logging.basicConfig(
        format="%(asctime)s %(message)s", datefmt="%H:%M:%S", level=logging.INFO
    )
    # Define logger for tools.py usage also

    # This logs execptions via logger which is great for finding out what went wrong with unnattended sessions
    # Copied word for word from: https://stackoverflow.com/questions/6234405/logging-uncaught-exceptions-in-python
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception

    return logger


def _wait(seconds: int = 1, multiplier: int = 1) -> None:
    """Helper wait function. TODO: Overkill - emulator_client.py:27
    Loading multiplier is defined in settings, it is a decimally notated % multiplier. E.G:
    0.9 will run with 90% of the default wait times
    2.0 will run with 200% of the default wait times
    This is handy for slower machines where we need to wait for sections/images to load

    Args:
        seconds (int, optional): Wait time. Defaults to 1.
        multiplier (int, optional): Loading multiplier is defined in settings, it is a decimally notated % multiplier. E.G:
                                    0.9 will run with 90% of the default wait times
                                    2.0 will run with 200% of the default wait times
                                    This is handy for slower machines where we need to wait for sections/images to load. Defaults to 1.
    """
    time.sleep(seconds * multiplier)
