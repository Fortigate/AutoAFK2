import sys
import argparse
import inspect
from humanfriendly import format_timespan
from tools import * # Includes logging so we don't import here also

# Global variables for tracking time passed between team-up activities
global last_synergy
last_synergy = time.time()
global last_corrupt
last_corrupt = time.time()
# Version output so I can work out which version I'm actually running for debugging
version = '0.0.13'

# Configure launch arguments
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--teamup", action = 'store_true', help = "Run the Team-up function")
parser.add_argument("-d", "--dailies", action = 'store_true', help = "Run the Dailies function")
parser.add_argument("-c", "--config", metavar="CONFIG", default = "settings.ini", help = "Define alternative settings file to load")
args = vars(parser.parse_args())

# Work out which config file we're reading/writing to/from
if args['config']:
    settings = os.path.join(cwd, args['config'])
else:
    settings = os.path.join(cwd, 'settings.ini')
config.read(settings)

# Make a nice name for the output log file
if settings == 'settings.ini':
    logname = 'autoafk2.log'
else:
    logname = settings.split('.')[0] + '.log'

# File handler
file_log_handler = logging.FileHandler(filename=logname)
logger.addHandler(file_log_handler)
formatter = logging.Formatter('%(asctime)s %(message)s')
file_log_handler.setFormatter(formatter)
# STDERR handler so we don't lose that
logging.StreamHandler(stream=sys.stderr)
# Make timestamps etc look pretty
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
# Define logger for tools.py usage also
logger = logging.getLogger('autoafk2')

# This logs execptions via logger which is great for finding out what went wrong with unnattended sessions
# Copied word for word from: https://stackoverflow.com/questions/6234405/logging-uncaught-exceptions-in-python
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Quick storage for commonly used regions
regions = {
    #locate
    'sunandstars': (770, 40, 100, 100),
    'main_menu': (900, 1750, 150, 150),
    'menu_activities': (20, 950, 1050, 800),
    'back': (50, 1750, 150, 150),
    'chat_window': (184, 362, 850, 1300),
    'right_sidebar': (888, 744, 190, 1000),
    'chat_selection': (20, 300, 170, 900),
    'bottom_third': (720, 1280, 360, 640)
}

# Boot up text
logger.info('') # Newline for easier log file reading with new sessions
logger.info('Loaded settings file: ' + str(settings.split('\\')[-1]))
logger.info('Version: ' + version)

# Boot up activities before tasks are ran
connect_and_launch(port=config.get('ADVANCED', 'port'))
waitUntilGameActive()

def dailies():
    if config.getboolean('ACTIVITIES', 'claim_afk'):
        claim_afk_rewards()
    if config.getboolean('ACTIVITIES', 'friend_points'):
        friend_points_collect()
    if config.getboolean('ACTIVITIES', 'mail_collect'):
        mail_connect()
    if config.getboolean('ACTIVITIES', 'emporium_purchases'):
        emporium_purchases()
    if config.getboolean('ACTIVITIES', 'dream_realm'):
        dream_realm()
    if config.getint('ACTIVITIES', 'arena_battles') > 0:
        arena(config.getint('ACTIVITIES', 'arena_battles'))
    if config.getboolean('ACTIVITIES', 'collect_quests'):
        quests()
    if config.getboolean('ACTIVITIES', 'noble_path'):
        noble_path()
    if config.getboolean('ACTIVITIES', 'claim_events'):
        claim_events()
    if config.getboolean('ACTIVITIES', 'farm_affinity'):
        farm_affinty()
    logger.info('Dailies done!')

# To run the task on a loop forever and ever
# Its in two 1 == 1 loops so we can call return on the main function when it gets stuck and restart it from this function for stability
def teamup():
    while 1 == 1:
        team_up()

def team_up():
    timer = 0
    start = time.time()
    while 1 == 1:
        # First ensure
        while not isVisible('labels/sunandstars', region=regions['sunandstars']):
            click('buttons/back', suppress=True, region=regions['back'])
            click_location('neutral')
            wait()
        logger.info('Opening chat')
        while not isVisible('teamup/join', seconds=0, confidence=0.8, region=regions['chat_window']):
            click('teamup/chat', seconds=0, suppress=True, region=regions['right_sidebar'])
            click('teamup/teamup', seconds=0, suppress=True, region=regions['chat_selection'])
            if isVisible('teamup/join', seconds=0, region=regions['chat_window']):
                # Prioritise Corrupt Creatures over Synergy battles
                continue
            # Synergy battle hero lending is handled here
            if isVisible('teamup/synergy', seconds=0, region=regions['chat_window']):
                x, y = returnxy('teamup/synergy', region=regions['chat_window'])
                # We wait 3mins between each one else we end up opening and closing the same one repeatadly
                if return_pixel_colour(x, y + 220, 2, seconds=0) < 200 and (time.time() - globals()['last_synergy'] > 180):
                    logger.info('Synergy Battle found!')
                    clickXY(x, y + 220)
                    if isVisible('buttons/back', region=regions['back']):
                        clickXY(300, 900)
                        clickXY(650, 1800)
                        click('buttons/back', suppress=True, region=regions['back'])
                        logger.info('Hero lent\n')
                        globals()['last_synergy'] = time.time()
                        return
                    else:
                        logger.info('Something went wrong, returning\n')
                        globals()['last_synergy'] = time.time()
                        return
            # If we've not seen any corrupt group for 5 minutes sometimes autoscroll has stopped working so we do it manually
            if (time.time() - globals()['last_corrupt'] > 300):
                logger.info('Nothing seen for a while, trying to scroll')
                swipe(1000, 1500, 1000, 500, 1000, seconds=2)
        duration = time.time() - start
        logger.info('Corrupt Creature found in ' + format_timespan(round(duration)) + '!')
        # logger.info(str(format_timespan(time.time() - globals()['last_corrupt'])) + ' since last corrupt')
        click('teamup/join', seconds=5, region=regions['chat_window'])
        if not isVisible('teamup/ready', region=regions['bottom_third']):
            logger.info('Something went wrong, waiting 30s before continuing\n')
            wait(30)
            return
        click('teamup/ready', seconds=6, region=regions['bottom_third'])
        # logger.info('Readying up in the lobby')
        while isVisible('teamup/quit', confidence=0.8, region=regions['bottom_third']):
            timer += 1
            if timer > 15:
                logger.info('Timeout error!\n')
                click('teamup/quit', seconds=2, region=regions['bottom_third'])
                clickXY(850, 1250, seconds=4)
                return
        while isVisible('teamup/ready_lobby', confidence=0.8, region=regions['bottom_third']):
            logger.info('Deploying heroes')
            clickXY(120, 1300)
            clickXY(270, 1300)
            clickXY(450, 1300)
            click('teamup/ready_lobby', confidence=0.8, region=regions['bottom_third'])
        while not isVisible('labels/tap_to_close', confidence=0.8, region=regions['bottom_third']):
            timer += 1
            if timer > 20:
                logger.info('Timeout error!\n')
                click_location('neutral')
                return
        click('labels/tap_to_close', confidence=0.8, region=regions['bottom_third'])
        timer = 0
        logger.info('Battle complete!\n')
        globals()['last_corrupt'] = time.time()
        wait(3)
        return
    team_up()

def claim_afk_rewards():
    logger.info('Claiming AFK Rewards')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    clickXY(100, 1800, seconds=4)  # Open AFK Rewards
    clickXY(550, 1400)  # Click Chest
    clickXY(550, 1080)  # Click Collect

    # Fast rewards
    for _ in range(config.getint('ACTIVITIES', 'fast_rewards')):
        if isVisible('buttons/fast_rewards', click=True):
            click('buttons/confirm')
            clickXY(1000, 1800)

    clickXY(100, 1800)  # Close

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('AFK Rewards Claimed!\n')

def friend_points_collect():
    logger.info('Claiming Friend Gifts')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/friends', region=regions['menu_activities'], seconds=2)
    clickXY(700, 1800, seconds=2)
    clickXY(850, 300, seconds=2)
    clickXY(420, 50, seconds=2)  # Neutral location for closing reward pop ups etc, should never be an in game button here

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Friend Gifts Claimed!\n')

def mail_connect():
    logger.info('Claiming Mail')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/mail', region=regions['menu_activities'], seconds=2)
    clickXY(750, 1800, seconds=2)
    clickXY(750, 1800, seconds=2)

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Mail Claimed!\n')

def emporium_purchases():
    logger.info('Purchasing daily summon card')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/emporium', region=regions['menu_activities'], seconds=2)
    clickXY(100, 700, seconds=2) # guild store
    clickXY(325, 900, seconds=2) # daily card
    clickXY(650, 1800, seconds=2)  # purchase
    clickXY(875, 1250, seconds=2)  # diamonds confirm
    click_location('neutral')

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Daily summon card purchased!\n')

def arena(battles=9):
    counter = 0
    logger.info('Battling Arena')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    clickXY(450, 1825)
    if isVisible('labels/battle_modes'):
        click('buttons/arena', seconds=2)
        click_location('neutral')
        click_location('neutral')
        while counter < battles:
            logger.info('Fighting Arena Battle ' + str(counter+1) + ' of ' + str(battles))
            click('buttons/challenge', seconds=3, retry=5, confidence=0.8)
            if isVisible('buttons/confirm'):
                logger.info('Purchase challenge pop-up detected, confirming')
                click('buttons/confirm')
                click('buttons/challenge', seconds=3)
            clickXY(180, 1450, seconds=5)
            click('buttons/battle')
            while not isVisible('labels/tap_to_close', confidence=0.8):
                wait()
                # Clear promotion screen if visible
                if isVisible('labels/arena_promote'):
                    clickXY(550, 1800)
            logger.info('Battle complete')
            while isVisible('labels/tap_to_close', confidence=0.8):
                click('labels/tap_to_close', seconds=4, suppress=True)
            counter += 1

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Arena battles completed!\n')

def dream_realm():
    logger.info('Battling Dream Realm')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    clickXY(450, 1825)
    if isVisible('labels/battle_modes'):
        click('buttons/dream_realm', seconds=2)
        clickXY(1020, 280, seconds=2)
        clickXY(1020, 280, seconds=2)
        clickXY(550, 1800)
        click('buttons/back', seconds=3)
        clickXY(550, 1800, seconds=4) # Battle
        clickXY(550, 1800) # Battle begin from hero selection
        while not isVisible('labels/tap_to_close'):
            wait()
            click_location('neutral')
        while isVisible('labels/tap_to_close'): # Few clicks to clear loot too
            click('labels/tap_to_close', seconds=3, suppress=True)
        logger.info('battle complete!')

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Dream Realm completed!\n')

def quests():
    logger.info('Collecting Quests')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=(900, 1750, 150, 150))
    click('buttons/quests', seconds=3)

    # Daily quests
    clickXY(300, 1800, seconds=2)
    if isVisible('buttons/quick_collect'):
        click('buttons/quick_collect', seconds=2)
        clickXY(900, 200, seconds=2)  # collect dailies
        click_location('neutral')

    # Guild quests
    clickXY(500, 1800, seconds=2)
    while isVisible('buttons/collect'):
        click('buttons/collect')

    # Growth Trials
    clickXY(950, 1800, seconds=2)
    while isVisible('buttons/collect'):
        click('buttons/collect')

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Quests collected!\n')

def farm_affinty(heroes=40):
    logger.info('Clicking every hero 3 times for +6 affinity')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    counter = 1
    clickXY(650, 1850, seconds=3) # Open heroes hall
    clickXY(150, 850, seconds=3) # Click top right hero
    while counter < heroes:
        clickXY(550, 1000)
        clickXY(550, 1000)
        clickXY(550, 1000)
        clickXY(620, 1800)
        clickXY(1000, 1100)
        counter += 1
        click('buttons/back')
        click('buttons/back2')

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Affinity farmed!\n')

def noble_path():
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Collecting noble path')
    click('buttons/main_menu', region=(900, 1750, 150, 150))
    click('buttons/noble_path', seconds=2)
    click('buttons/noble_quests_inactive', seconds=2)

    # Daily
    if isVisible('buttons/claim_all', click=True):
        clickXY(1000, 1800)

    # Weekly - TODO next week, idk how it looks when there is something to collect
    click('buttons/noble_quests_weekly')

    # Epic - TODO, idk how it looks when there is something to collect
    click('buttons/noble_quests_epic')

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Noble path collected!\n')

def claim_events():
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Claiming event rewards')
    click('buttons/main_menu', region=(900, 1750, 150, 150))
    click('buttons/event', seconds=2)

    # All Heroes
    if isVisible('events/all_heroes', click=True):
        if isVisible('events/all_heroes_claim', click=True, confidence=0.8, retry=10, yrelative=100):
            logger.info('All Heroes claimed')
            click_location('neutral')

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Events claimed!\n')

if args['dailies']:
    logger.info('Running Dailies\n')
    dailies()

if args['teamup']:
    logger.info('Starting up team-up farming\n')
    teamup()
