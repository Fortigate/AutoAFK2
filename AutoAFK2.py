import argparse
import inspect
from humanfriendly import format_timespan
from tools import * # Includes logging so we don't import here also
from consolemenu import *
from datetime import datetime, timezone

# Global variables for tracking time passed between team-up activities
global last_synergy
last_synergy = time.time() - 300 # -300 so we don't wait 300 seconds before opening the first
global last_corrupt
last_corrupt = time.time()
# Version output so I can work out which version I'm actually running for debugging
version = '0.4.2'
# Current time in UTC for tracking which towers/events are open
currenttimeutc = datetime.now(timezone.utc)

# Configure launch arguments
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--abyss", action='store_true', help = "Run the Trial of Abyss retry function")
parser.add_argument("-l", "--legend", action='store_true', help = "Run the Legend Trials retry function")
parser.add_argument("-t", "--teamup", action='store_true', help = "Run the Team-up function")
parser.add_argument("-d", "--dailies", action='store_true', help = "Run the Dailies function")
parser.add_argument("-q", "--quest", action='store_true', help = "Runs the Quest running function")
parser.add_argument("-test", "--test", action='store_true', help = "Used for testing functions")
parser.add_argument("-c", "--config", metavar="CONFIG", default = "settings.ini", help = "Define alternative settings file to load")
parser.add_argument('--forceprint', action='store_true', help='Force print output')
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

from threading import Event
import keyboard

hotkey = 'k'

running = Event()
running.set()  # at the start, it is running

def handle_key_event(event):
    if event.event_type == 'down':
        # toggle value of 'running'
        if running.is_set():
            running.clear()
            logger.info('Pausing!')
        else:
            running.set()

# make it so that handle_key_event is called when k is pressed; this will
# be in a separate thread from the main execution
#keyboard.hook_key(hotkey, handle_key_event)

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
    'top_third': (0, 0, 1080, 640),
    'middle_third': (0, 640, 1080, 640),
    'bottom_third': (0, 1280, 1080, 640),
    'bottom_buttons': (0, 1620, 1080, 300),
    'confirm_deny': (500, 1100, 500, 300),
    'battle_modes': (20, 580, 1050, 1100),
    'action_buttons': (400, 1050, 300, 500) # gives out of bounds error and I'm too tired to work out why
}

# Boot up text
logger.info('Loaded settings file: ' + str(settings.split('\\')[-1]))
logger.info('Version: ' + version)

# Boot up activities before tasks are ran
connect_and_launch(port=config.get('ADVANCED', 'port'))
resolutionCheck()
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
    if config.getboolean('ACTIVITIES', 'claim_events'):
        claim_events()
    if config.getboolean('ACTIVITIES', 'push_towers'):
        blind_push("towers")
    if config.getboolean('ACTIVITIES', 'push_dream_realm'):
        blind_push("dream_realm")
    if config.getboolean('ACTIVITIES', 'noble_path'):
        noble_path()
    if config.getboolean('ACTIVITIES', 'farm_affinity'):
        farm_affinity(45)
    logger.info('Dailies done!')

def team_up():
    timer = 0
    start = time.time()
    while 1 == 1:
        # First ensure we're at the main map
        while not isVisible('labels/sunandstars', region=regions['sunandstars']):
            click('buttons/back', suppress=True, region=regions['back'])
            click_location('neutral')
            wait()
        # logger.info('Opening chat')
        while not isVisible('teamup/join', seconds=0, confidence=0.8, region=regions['chat_window']):
            click('buttons/back', seconds=0, suppress=True, region=regions['back']) # Somehow we open afk rewards occasionally, this will exit that
            click('teamup/chat', seconds=0, suppress=True, region=regions['right_sidebar'])
            isVisible('buttons/confirm', region=regions['confirm_deny'], click=True) # to catch 'Reconnect to chat?'
            click('teamup/teamup', seconds=0, suppress=True, region=regions['chat_selection'])
            # Sometimes autoscroll breaks after a while so we do it manually each check
            swipe(1000, 1500, 1000, 500, 500)
            # if isVisible('teamup/join', seconds=0, region=regions['chat_window']):
            #     # Prioritise Corrupt Creatures over Synergy battles
            #     continue
            # Synergy battle hero lending is handled here
            if isVisible('teamup/synergy', seconds=0, region=regions['chat_window']):
                x, y = returnxy('teamup/synergy', region=regions['chat_window'])
                # We wait 60s between each one else we end up opening and closing the same one repeatadly
                if x != 0: # 0 is the 'nothing found' return value from returnxy() so skip if it's returned
                    if return_pixel_colour(x, y + 220, 2, seconds=0) < 200 and (time.time() - globals()['last_synergy'] > 60):
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
                else:
                    logger.info('Synergy button gone!\n')
                    return
        duration = time.time() - start
        # logger.info(str(format_timespan(time.time() - globals()['last_corrupt'])) + ' since last corrupt')
        click_last('teamup/join', seconds=4, confidence=0.8, region=regions['chat_window'])
        # If ready is not visible after clicking join then it's been disbanded etc so we restart
        if not isVisible('teamup/ready', region=regions['bottom_buttons']):
            # logger.info('Something went wrong, waiting 30s before continuing\n')
            # Try a quit just in case
            click('teamup/quit', region=regions['bottom_buttons'], suppress=True)
            click('buttons/confirm', region=regions['confirm_deny'], suppress=True) # to catch 'Reconnect to chat?
            wait(30)
            return
        click('teamup/ready', seconds=4, region=regions['bottom_buttons'])
        logger.info('Corrupt Creature found in ' + format_timespan(round(duration)) + '!') # Only message after we're in to avoid spam
        # If Quit button is visible 15 cycles after readying up then the host is afk etc so we restart
        while isVisible('teamup/quit', confidence=0.8, region=regions['bottom_buttons']):
            timer += 1
            if timer > 15:
                logger.info('Timeout error!\n')
                click('teamup/quit', seconds=2, region=regions['bottom_buttons'])
                clickXY(850, 1250, seconds=4)
                return
        while isVisible('teamup/ready_lobby', confidence=0.8, region=regions['bottom_buttons']):
            logger.info('Deploying heroes')
            wait()
            clickXY(120, 1300)
            clickXY(270, 1300)
            clickXY(450, 1300)
            click('teamup/ready_lobby', suppress=True, confidence=0.8, region=regions['bottom_buttons'])
            break # Break loop otherwise if we miss a button we loop here until battle starts
        while not isVisible('labels/tap_to_close', confidence=0.8, region=regions['bottom_buttons']):
            timer += 1
            if timer > 20:
                logger.info('Timeout error!\n')
                click_location('neutral') # Neutral taps to try and get back to main map if something went wrong
                return
        click('labels/tap_to_close', confidence=0.8, region=regions['bottom_buttons'])
        timer = 0
        logger.info('Battle complete!\n')
        globals()['last_corrupt'] = time.time()
        wait(3)
        return

def claim_afk_rewards():
    logger.info('Claiming AFK Rewards')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    clickXY(100, 1800, seconds=4)  # Open AFK Rewards

    clickXY(550, 1400)  # Click Chest
    clickXY(550, 1080)  # Click Collect
    wait(2) # Wait and claim again to complete daily quest
    clickXY(550, 1400)  # Click Chest
    clickXY(550, 1080)  # Click Collect

    if isVisible('buttons/fast_rewards'):
        clickXY(550, 1400)  # Click Chest
        clickXY(550, 1080)  # Click Collect

        # Fast rewards
        for _ in range(config.getint('ACTIVITIES', 'fast_rewards')):
            if isVisible('buttons/fast_rewards', click=True):
                click('buttons/confirm', suppress=True)
                clickXY(1000, 1800)

        clickXY(100, 1800)  # Close
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('AFK Rewards Claimed!\n')
    else:
        logger.info('Issue opening AFK Rewards!')
        recover()

def friend_points_collect():
    logger.info('Claiming Friend Gifts')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/friends', region=regions['menu_activities'], seconds=2)

    if isVisible('labels/friends'):
        clickXY(700, 1800, seconds=2)
        clickXY(850, 300, seconds=2)
        click_location('neutral')
        click('buttons/back', region=regions['back'])
        click('buttons/back', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Friend Gifts Claimed!\n')
    else:
        logger.info('Issue claiming friends points!')
        recover()

def mail_connect():
    logger.info('Claiming Mail')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/mail', region=regions['menu_activities'], seconds=2)

    if isVisible('labels/mail'):
        clickXY(750, 1800, seconds=2)
        clickXY(750, 1800, seconds=2)
        click('buttons/back', region=regions['back'])
        click('buttons/back', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Mail Claimed!\n')
    else:
        logger.info('Issue claiming Mail!')
        recover()

def emporium_purchases():
    logger.info('Purchasing daily summon card')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/emporium', region=regions['menu_activities'], seconds=2)
    clickXY(100, 700, seconds=2) # guild store
    if isVisible('labels/emporium_guild', region=regions['top_third']):
        if isVisible('emporium/guild_summoncard'):
            click('emporium/guild_summoncard', region=regions['middle_third'])
            click('buttons/purchase', region=regions['bottom_buttons'])
            click('buttons/confirm', region=regions['confirm_deny'], seconds=2)
            click_location('neutral')
        else:
            logger.info('Daily card already purchased!')
        click('buttons/back2', region=regions['back'])
        click('buttons/back', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Daily summon card purchased!\n')
    else:
        logger.info('Issue purchasing summon card!')
        recover()

def arena(battles=9):
    timeout = 0
    counter = 0
    logger.info('Battling Arena')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    clickXY(450, 1825)
    if isVisible('labels/battle_modes'):
        click('buttons/arena', region=regions['battle_modes'], seconds=2)
        if isVisible('labels/weekly_arena_rewards', region=regions['middle_third']):
            logger.info('Weekly Arena rewards found!')
            clickXY(550, 1800)
        click_location('neutral')
        click_location('neutral')
        while counter < battles:
            logger.info('Fighting Arena Battle ' + str(counter+1) + ' of ' + str(battles))
            click('buttons/challenge', region=regions['bottom_buttons'], seconds=3, retry=5, confidence=0.8)
            if isVisible('buttons/confirm', region=regions['confirm_deny']):
                # logger.info('Purchase challenge pop-up detected, confirming')
                click('buttons/confirm', region=regions['confirm_deny'])
                click('buttons/challenge', seconds=3, region=regions['bottom_buttons'])
            clickXY(180, 1450, seconds=6) # Leftmost opponent
            click('buttons/battle', region=regions['bottom_buttons'])
            while not isVisible('labels/tap_to_close', region=regions['bottom_buttons'], confidence=0.8):
                # Clear promotion screen if visible (not sure this does anything with while isVisible loop at the end covering the case)
                if isVisible('labels/arena_promote', region=regions['bottom_third']):
                    clickXY(550, 1800)
                timeout += 1
                if timeout > 50: # Should be about 10 seconds longer than a full fight at 2x
                    logger.info('Arena timeout error\n')
                    timestamp = datetime.now().strftime('%d-%m-%y_%H-%M-%S')
                    save_screenshot('arena_timeout_' + timestamp)
                    recover()
                    return
            logger.info('Battle complete')
            while isVisible('labels/tap_to_close', region=regions['bottom_buttons'], confidence=0.8):
                click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=4, suppress=True)
            counter += 1
            timer = 0
        # Collect Victory Rewards
        clickXY(200, 550)
        clickXY(200, 550)
        clickXY(200, 550)
        click_location('neutral')
    else:
        logger.info('Issue opening Arena!')
        recover()

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Arena battles completed!\n')

def dream_realm():
    timer = 0
    logger.info('Battling Dream Realm')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    clickXY(450, 1825, seconds=3)
    click('buttons/dream_realm', region=regions['battle_modes'], seconds=3)
    # First collect rewards
    if isVisible('buttons/battle', region=regions['bottom_buttons']):
        logger.info('Collecting previous round rewards')
        clickXY(1020, 280, seconds=5)
        clickXY(1020, 280, seconds=2)
        clickXY(550, 1800, seconds=2)
        click('buttons/back2', region=regions['back'], seconds=3)
    else:
        logger.info('issue collecting rewards!')
        recover()
        return
    # Then attempt a single battle
    if isVisible('buttons/battle', region=regions['bottom_buttons']):
        logger.info('Battling Dream Realm')
        click('buttons/battle', region=regions['bottom_buttons'], seconds=5)
        click('buttons/battle', region=regions['bottom_buttons'], seconds=3)
        while not isVisible('labels/tap_to_close'):
            wait()
            click_location('neutral')
            timer += 1
            if timer > 40:
                logger.info('Dream Realm timeout!')
                recover()
                return
        while isVisible('labels/tap_to_close', region=regions['bottom_buttons']): # Few clicks to clear loot too
            click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=4, suppress=True)
        logger.info('Battle complete!')
        click('buttons/back', region=regions['back'])
        click('buttons/back2', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Dream Realm completed!\n')
    else:
        logger.info('Issue collecting rewards!')
        recover()
        return

def quests():
    logger.info('Collecting Quests')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/quests', region=regions['menu_activities'],  seconds=3)
    clickXY(300, 1800, seconds=2)# Daily quests

    if isVisible('labels/daily_quests'):
        if isVisible('buttons/quick_collect', region=regions['bottom_third']):
            click('buttons/quick_collect', region=regions['bottom_third'], seconds=2)
        if config.getboolean('ADVANCED', 'collect_daily_rewards') is True:
            clickXY(900, 200, seconds=2)  # collect dailies
            click_location('neutral')
        else:
            logger.info('Skipping daily quest rewards collection')

        # Guild quests
        clickXY(500, 1800, seconds=2)
        while isVisible('buttons/collect'):
            click('buttons/collect')

        # Growth Trials
        clickXY(950, 1800, seconds=2)
        while isVisible('buttons/collect'):
            click('buttons/collect')

        click('buttons/back2', region=regions['back'])
        click('buttons/back', region=regions['back'])

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Quests collected!\n')
    else:
        logger.info('Issue collecting quests!')
        recover()
        return

def farm_affinity(heroes=40):
    logger.info('Clicking every hero 3 times for +6 affinity')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    counter = 1
    clickXY(650, 1850, seconds=3) # Open heroes hall
    clickXY(150, 850, seconds=3) # Click top right hero

    if isVisible('buttons/affinity', region=regions['top_third']):
        while counter < heroes:
            if counter % 10 == 0:
                logger.info('Tapping ' + str(counter) + 'th hero')
            clickXY(550, 1000)
            clickXY(550, 1000)
            clickXY(550, 1000)
            clickXY(620, 1800)
            clickXY(1000, 1100)
            counter += 1
        click('buttons/back', region=regions['back'], seconds=2)
        click('buttons/back2', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Affinity farmed!\n')
    else:
        logger.info('Something went wrong opening hero affinity!')
        recover()

def noble_path():
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Collecting noble path')
    click('buttons/main_menu', region=regions['main_menu'], seconds=2)
    click('buttons/noble_path', region=regions['menu_activities'], seconds=2)

    # Noble Path
    if isVisible('buttons/noble_path_active', region=regions['bottom_third'], click=True, seconds=2, grayscale=True) or isVisible('buttons/noble_path_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
        # This will claim quests in all tabs
        click('buttons/noble_quests_inactive', grayscale=True, seconds=2)
        if isVisible('buttons/claim_all', click=True):
            clickXY(1000, 1800)

        # Travelogue
        click('buttons/noble_travelogue_inactive', grayscale=True)
        if isVisible('buttons/claim_all', click=True):
            clickXY(1000, 1800)

    # Seasonal Noble Path
    if isVisible('buttons/noble_season_active', region=regions['bottom_third'], click=True, seconds=2, grayscale=True) or isVisible('buttons/noble_season_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
        # This will claim quests in all tabs
        click('buttons/noble_quests_inactive', grayscale=True, seconds=2)
        if isVisible('buttons/claim_all', click=True):
            clickXY(1000, 1800)
        # Travelogue
        click('buttons/noble_travelogue_inactive', grayscale=True)
        if isVisible('buttons/claim_all', click=True):
            clickXY(1000, 1800)

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Noble path collected!\n')
    else:
        logger.info('Something went wrong collecting Season Noble path!')
        recover()

def claim_events():
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Claiming event rewards')
    click('buttons/main_menu', region=regions['main_menu'], seconds=3)
    click('buttons/event', region=regions['menu_activities'], seconds=3)

    # All Heroes
    if isVisible('events/all_heroes', click=True, seconds=2) or isVisible('events/all_heroes_inactive', click=True, seconds=2):
        if isVisible('events/all_heroes_claim', click=True, confidence=0.8, retry=10, yrelative=100):
            logger.info('All Heroes claimed')
            click_location('neutral')
    click('buttons/back', region=regions['back'])
    click('buttons/back', region=regions['back'])
    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Events claimed!\n')

def blind_push(mode, tower=None):
    if mode == "towers":
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
        logger.info('Blind-pushing towers')
        clickXY(460, 1820, seconds=2)
        click("labels/legend_trial", seconds=2, retry=3)

        factions = ["Light", "Wilder", "Graveborn", "Mauler"]
        for faction in factions:
            if isVisible("towers/"+faction.lower(), confidence=0.94, click=True, seconds=4, yrelative=-20):
                if isVisible("towers/floor_info", click=True, region=(15, 750, 1050, 1000), seconds=3, yrelative=-50):
                    wait(3)
                    if isVisible("buttons/battle", click=True):
                        back_occurence = 0
                        while True:
                            if isVisible("labels/tap_to_close", click=True, seconds=2):
                                click("buttons/back")
                                break
                            elif isVisible("buttons/next", click=True, retry=3):
                                logger.info(faction + ' win detected, moving to next floor')
                                wait(3)
                                back_occurence=0
                                click("buttons/battle", seconds=3)
                            elif isVisible("buttons/back"):
                                if back_occurence == 0:
                                    back_occurence = 1
                                else:
                                    click("buttons/back")
                                    break
                            wait(5)
                else:
                    break

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Towers pushed!\n')

    if mode == "retry_tower":
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
        logger.info('Pushing ' + tower.capitalize() + ' tower!')
        clickXY(460, 1820, seconds=2)
        click("labels/legend_trial", seconds=2)

        factions = ["graveborn", "light", "mauler", "wilder"]
        for faction in factions:
            if faction == tower:
                if isVisible("towers/"+faction.lower(), confidence=0.95, click=True, seconds=4, yrelative=-20):
                    while True:
                        if not running.is_set():
                            running.wait()  # wait until running is set
                            logger.info('Resuming')
                        click("buttons/abyss_lvl", suppress=True, grayscale=True, confidence=0.8)
                        click("buttons/battle", suppress=True, region=regions['bottom_buttons'])
                        click("labels/tap_to_close", suppress=True, region=regions['bottom_buttons'])
                        if isVisible("buttons/next", click=True, region=regions['bottom_buttons']):
                            logger.info(faction.capitalize() + ' win detected, moving to next floor')
                            click("buttons/battle", seconds=3, suppress=True)

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Towers pushed!\n')

    if mode == 'abyss':
        victory_counter = 0
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
        logger.info('Auto-retrying Trial of Abyss')
        click('buttons/main_menu', region=regions['main_menu'], seconds=3)
        if isVisible('buttons/trial_of_abyss', click=True):
            pass
        else:
            click('buttons/event', region=regions['menu_activities'], seconds=3)
            while not isVisible('events/abyss', region=regions['bottom_third']):
                swipe(700, 1800, 250, 1800, 2000)
            click('events/abyss', region=regions['bottom_third'])
            click('buttons/abyss_entry', region=regions['bottom_third'])

        while isVisible('labels/trial_of_abyss', click=True): # First click can claim loot so we loop it to make sure we're opening ToA
            while True:
                if not running.is_set():
                    running.wait()  # wait until running is set
                    logger.info('Resuming')
                click("buttons/abyss_lvl", seconds=0.2, suppress=True)
                if isVisible("buttons/battle", seconds=0.2, click=True, region=regions['bottom_buttons']):
                    if victory_counter > 0 and victory_counter % 100 == 0:
                        logger.info(str(victory_counter) + ' attempts made')
                    victory_counter += 1
                click("labels/tap_to_close", suppress=True, seconds=0.2, region=regions['bottom_buttons'])
                if isVisible("buttons/next", seconds=0.2, click=True, region=regions['bottom_buttons']):
                    logger.info('Stage passed in ' + str(victory_counter) + ' attemps!')
                    victory_counter = 0
                wait(2)
        else:
            logger.info('Something went wrong opening Trial of Abyss!')
            recover()

    if mode == "dream_realm":
        logger.info('Auto-retrying Dream Realm')
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

        clickXY(450, 1825, seconds=3)
        click('buttons/dream_realm', region=regions['battle_modes'], seconds=3)
        
        for _ in range(10):
            if isVisible('buttons/battle', region=regions['bottom_buttons'], click=True, seconds=5):
                if isVisible('buttons/battle', region=regions['bottom_buttons'], click=True, seconds=3):
                    while not isVisible('labels/tap_to_close'):
                        wait()
                    while isVisible('labels/tap_to_close', region=regions['bottom_buttons']): # Few clicks to clear loot too
                        click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=4, suppress=True)
                    logger.info('Battle complete!')
                else: 
                    break

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Dream Realm attempts exhausted.\n')    

# Scans and pushes the various buttons needed to complete story/side quests
# Very slow, can get stuck if there is a player present at an end point and we get the magnifying glass icon instead of the action icon
# The order of checks and clicks is important to not get stuck in loops
#TODO Get chest icon for collecting quest items
def quest_push():
    logger.info('Pushing Quests!\n')
    while True:
        clickXY(870, 400, seconds=2)
        clickXY(870, 400)
        if isVisible('buttons/battle', click=True, seconds=0.2):
            logger.info('Battling')
        if isVisible('buttons/skip', click=True, region=regions['bottom_buttons'], seconds=0.2):
            logger.info('Skipping')
        if isVisible('buttons/dialogue_option', click=True, region=regions['chat_window'], seconds=0.2):
            logger.info('Advancing dialogue')
        if isVisible('buttons/red_dialogue', click=True, seconds=0.2):
            logger.info('Advancing dialogue')
        if isVisible('buttons/confirm', click=True, seconds=0.2):
            logger.info('Clicking Confirm')
        if isVisible('buttons/interact', click=True, region=regions['chat_window'], seconds=0.2):
            logger.info('Interacting')
        if isVisible('buttons/dialogue', confidence=0.8, click=True, region=regions['chat_window'], seconds=0.2):
            logger.info('Initiating dialogue')
        if isVisible('buttons/tap_and_hold', region=regions['chat_window'], seconds=0.2):
            logger.info('Holding button')
            swipe(550, 1250, 550, 1250, 4000)  # Hacky way to hold it down
        if isVisible('buttons/enter', seconds=0.2):
            logger.info('Entering location')
        if isVisible('buttons/battle_button', click=True, region=regions['chat_window'], confidence=0.8, seconds=0.2):
            logger.info('Initiating battle')
        swipe(550, 1500, 560, 1510, 250) # Hypofiends battle button won't trigger unless we move a few pixels

def run_lab():
    if lab is not completed:
        run_lab()


# Handle launch arguments

if args['forceprint']: # Define a custom logging handler that duplicates log messages to stdout
    class DuplicatedStdoutHandler(logging.StreamHandler):
        def emit(self, record):
            print(self.format(record))

    stdout_handler = DuplicatedStdoutHandler()
    stdout_handler.setLevel(logging.INFO)
    logger = logging.getLogger(__name__)
    logger.addHandler(stdout_handler)
    logger.propagate = False

if args['dailies']:
    logger.info('Running Dailies\n')
    dailies()

if args['teamup']:
    logger.info('Starting up team-up farming')
    start_time = time.time()
    limit_minutes = config.getint('ACTIVITIES', 'teamup_limit')

    if limit_minutes == 0:
        limit = float('inf')
        logger.info("Time limit: Indefinite\n")
    else:
        limit = limit_minutes * 60
        logger.info(f"Time remaining: {limit_minutes} minutes")
        logger.info(f'Time limit can be configured in settings.ini\n')

    while time.time() - start_time < limit:
        team_up()

if args['abyss']:
    logger.info('Opening Trials of Abyss')
    blind_push('abyss')

if args['legend']:
    blind_push('tower')

if args['quest']:
    quest_push()

if args['test']:
    quest_push()

# If no function launch argument we pop the UI

primary_menu = ["Run Dailies", "Run Team-up farming", "Retry Trial of Abyss"]
open_towers = {1: ["Retry Lightbringer Tower"],
        2: ["Retry Mauler Tower"],
        3: ["Retry Wilder Tower"],
        4: ["Retry Graveborn Tower"],
        5: ["Retry Lightbringer Tower", "Retry Mauler Tower"],
        6: ["Retry Wilder Tower", "Retry Graveborn Tower"],
        7: ["Retry Lightbringer Tower", "Retry Wilder Tower", "Retry Mauler Tower", "Retry Graveborn Tower"]}
for day, towers in open_towers.items():
    if currenttimeutc.isoweekday() == day:
        primary_menu.extend(towers)

selection = SelectionMenu.get_selection(primary_menu, title='Welcome to AutoAFK2! Select an activity:')
selection += 1 # Non-zero index to make things easier to read

if selection == 1:
    dailies()

if selection == 2:
    logger.info('Starting up team-up farming')
    start_time = time.time()
    limit_minutes = config.getint('ACTIVITIES', 'teamup_limit')

    if limit_minutes == 0:
        limit = float('inf')
        logger.info("Time limit: Indefinite\n")
    else:
        limit = limit_minutes * 60
        logger.info(f"Time remaining: {limit_minutes} minutes")
        logger.info(f'Time limit can be configured in settings.ini\n')

    while time.time() - start_time < limit:
        team_up()

if selection == 3:
    blind_push('abyss')

# SelectionMenu only returns an int so here's a hacky way to work out which tower was selected. It ain't pretty.

if selection == 4:
    day = currenttimeutc.isoweekday()
    if day == 1:
        blind_push('retry_tower', 'light')
    if day == 2:
        blind_push('retry_tower', 'mauler')
    if day == 3:
        blind_push('retry_tower', 'wilder')
    if day == 4:
        blind_push('retry_tower', 'graveborn')
    if day == 5:
        blind_push('retry_tower', 'light')
    if day == 6:
        blind_push('retry_tower', 'wilder')
    if day == 7:
        blind_push('retry_tower', 'light')

if selection == 5:
    day = currenttimeutc.isoweekday()
    if day == 5:
        blind_push('retry_tower', 'mauler')
    if day == 6:
        blind_push('retry_tower', 'wilder')
    if day == 7:
        blind_push('retry_tower', 'wilder')

if selection == 6:
    day = currenttimeutc.isoweekday()
    if day == 5:
        blind_push('retry_tower', 'mauler')
    if day == 6:
        blind_push('retry_tower', 'graveborn')
    if day == 7:
        blind_push('retry_tower', 'mauler')

if selection == 7:
    if day == 7:
        blind_push('retry_tower', 'graveborn')
    blind_push('towers')

