import argparse
import inspect
import math

from humanfriendly import format_timespan
from tools import * # Includes logging so we don't import here also
from consolemenu import *
from datetime import datetime, timezone
import ctypes

# Global variables for tracking time passed between team-up activities
global last_synergy
last_synergy = time.time() - 300 # -300 so we don't wait 300 seconds before opening the first
global last_corrupt
last_corrupt = time.time()
# For stage pushing
global afk_stage_defeats
afk_stage_defeats = 0
global formation
formation = 0
global first_stage_won
first_stage_won = False
# Version output so I can work out which version I'm actually running for debugging
version = '0.9.11e'
# Current time in UTC for tracking which towers/events are open
currenttimeutc = datetime.now(timezone.utc)
# Game version to launch
global server
server = 'com.farlightgames.igame.gp'

# Configure launch arguments
parser = argparse.ArgumentParser()
# Modes
parser.add_argument("-a", "--abyss", action='store_true', help="Run the Trial of Abyss retry function")
parser.add_argument("-l", "--legend", action='store_true', help="Run the Legend Trials retry function")
parser.add_argument("-t", "--teamup", action='store_true', help="Run the Team-up function")
parser.add_argument("-d", "--dailies", action='store_true', help="Run the Dailies function")
parser.add_argument("-q", "--quest", action='store_true', help="Runs the Quest running function")
parser.add_argument("-dr", "--dream", action='store_true', help="Run the Dream Realm function")
parser.add_argument("-afks", action='store_true', help="Run AFK Stages")
parser.add_argument("-afkt", action='store_true', help="Run AFK Talent Stages")
parser.add_argument("-test", action='store_true', help="Used for testing functions")
parser.add_argument("-charms", action='store_true', help="Run the Dura's Trials function")
# Configurations
parser.add_argument("-s", "--server", choices=['global', 'vn'], default='global', help="Select alernative game servers")
parser.add_argument("-c", "--config", metavar="CONFIG", default="settings.ini", help="Define alternative settings file to load")
parser.add_argument('--forceprint', action='store_true', help='Force print output')
args = vars(parser.parse_args())

# Work out which config file we're reading/writing to/from
if args['config']:
    settings = os.path.join(cwd, args['config'])
else:
    settings = os.path.join(cwd, 'settings.ini')
config.read(settings)

# Change server if necessary
if args['server'] == 'vn':
    globals()['server'] = 'com.farlightgames.igame.gp.vn'

# Make a nice name for the output log file
if settings == 'settings.ini':
    logname = 'autoafk2.log'
else:
    logname = settings.split('.')[0] + '.log'

from threading import Event
import keyboard

hotkey = 'F10'

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

# Nice name for the window and debugging peoples screenshots
ctypes.windll.kernel32.SetConsoleTitleW("AutoAFK2 v" + version)

# Boot up activities before tasks are ran
connect_and_launch(port=config.get('ADVANCED', 'port'), server=globals()['server'])
resolutionCheck()
waitUntilGameActive()

# TODO single SA battle and daily GS collection
def dailies():
    # start_autoprogress()
    if config.getboolean('ACTIVITIES', 'claim_afk'):
        claim_afk_rewards()
    if config.getboolean('ACTIVITIES', 'friend_points'):
        friend_points_collect()
    if config.getboolean('ACTIVITIES', 'mail_collect'):
        mail_connect()
    if config.getint('ACTIVITIES', 'arena_battles') > 0:
        arena(config.getint('ACTIVITIES', 'arena_battles'))
    if config.getboolean('ACTIVITIES', 'emporium_purchases'):
        emporium_purchases()
    if config.getboolean('ACTIVITIES', 'single_recruit'):
        single_recruit()
    if config.getboolean('ACTIVITIES', 'dream_realm'):
        dream_realm()
    if config.getboolean('ACTIVITIES', 'collect_quests'):
        collect_quests()
    # if config.getboolean('ACTIVITIES', 'claim_events'):
    #     claim_events()
    if config.getboolean('ACTIVITIES', 'push_towers'):
        blind_push("daily_towers")
    if config.getboolean('ACTIVITIES', 'push_dream_realm'):
        blind_push("dream_realm")
    if config.getboolean('ACTIVITIES', 'noble_path'):
        noble_path()
    if config.getboolean('ACTIVITIES', 'farm_affinity'):
        farm_affinity()
        # maintenance_level()
    logger.info('Dailies done!')

# Bit of an ugly function, we open the Team-Up chat and scan for the orange Join button and the Synergy Battle label for synergy battles
def team_up():
    timer = 0
    start = time.time()
    while True: # Naughty perma-loop, nested inside another when we call this with startup flags so calling 'return' will start from the top

        # First ensure we're at the main map
        while not isVisible('labels/sunandstars', region=regions['sunandstars'], seconds=0):
            click('buttons/back', suppress=True, region=regions['back'])
            click_location('neutral')

        # Then open team-up chat
        while not isVisible('teamup/teamup', click=True, region=regions['chat_selection']):  # Open the Team-Up section
            click('teamup/chat', seconds=2, suppress=True, region=regions['right_sidebar'])  # Open Chat window
            click('teamup/chat_yellow', retry=5, seconds=2, suppress=True, confidence=0.7, region=regions['right_sidebar'])  # Open Chat window

        # Loop while searching for 'Join' button
        while not isVisible('teamup/join', seconds=0, confidence=0.8, region=regions['chat_window']):

            # If it's been more than 300s we might be stuck so we try these to get back to the chat window
            if (time.time() - globals()['last_corrupt']) > 300 and (time.time() - globals()['last_synergy']) > 300:
                click('teamup/chat', seconds=0, suppress=True, region=regions['right_sidebar'])  # Ensure we actually have chat open
                click('teamup/teamup', seconds=0, suppress=True, region=regions['chat_selection'])  # Ensure we're in the right section
                click('buttons/back', seconds=0, suppress=True, region=regions['back'])  # Somehow we open afk rewards occasionally, this will exit that
                isVisible('buttons/confirm', region=regions['confirm_deny'], click=True)  # to catch 'Reconnect to chat?'
                swipe(1000, 1500, 1000, 500, 500)

            # Synergy battle hero lending is handled here for reasons
            if isVisible('teamup/synergy', seconds=0, region=regions['chat_window']):
                x, y = returnxy('teamup/synergy', region=regions['chat_window'])
                # We wait 60s between each one else we can end up opening and closing the same one repeatadly
                if x != 0: # 0 is the 'nothing found' return value from returnxy() so skip if it's returned
                    # If green button found and it's been more than 60s since the last Synergy
                    if return_pixel_colour(x, y + 220, 2, seconds=0) < 200 and (time.time() - globals()['last_synergy'] > 120):
                        logger.info('Synergy Battle found!')
                        clickXY(x, y + 220) # 220 is the button distance from the label
                        if isVisible('buttons/back', region=regions['back']):
                            clickXY(300, 900) # Second highest power hero (in case you want to save the primary or guildmates/friends)
                            clickXY(650, 1800)
                            click('buttons/back', suppress=True, region=regions['back'])
                            logger.info('Hero lent\n')
                            globals()['last_synergy'] = time.time()
                            return
                        else:
                            logger.info('Something went wrong with Synergy Battle, returning\n')
                            globals()['last_synergy'] = time.time()
                            return
                else:
                    logger.info('Synergy button gone!\n')
                    return

        # Log start time and click 'Join'
        duration = time.time() - start
        click_last('teamup/join', seconds=4, confidence=0.8, region=regions['chat_window'])

        # If Ready button is not visible after clicking join then it's been disbanded/level locked etc so we restart
        if not isVisible('teamup/ready', region=regions['bottom_buttons']):
            # Try a quit just in case
            click('teamup/quit', region=regions['bottom_buttons'], suppress=True)
            click('buttons/confirm', region=regions['confirm_deny'], suppress=True) # to catch 'Reconnect to chat?
            return

        # Ready up
        click('teamup/ready', seconds=4, region=regions['bottom_buttons'])
        logger.info('Corrupt Creature found in ' + format_timespan(round(duration)) + '!') # Only message after we're in to avoid spam

        # If Quit button is visible 15 cycles after readying up then the host is afk etc so we restart
        while isVisible('teamup/quit', confidence=0.8, region=regions['bottom_buttons']):
            timer += 1
            if timer > 15:
                logger.info('Lobby timeout error!\n')
                click('teamup/quit', seconds=2, region=regions['bottom_buttons'])
                clickXY(850, 1250, seconds=4)
                return

        # Deploy Heroes
        while isVisible('teamup/ready_lobby', confidence=0.8, region=regions['bottom_buttons']):
            logger.info('Deploying heroes')
            wait(2) # Wait for the emulator to load new assets after moving to battle screen else first click below doesn't register
            clickXY(120, 1300)
            clickXY(270, 1300)
            clickXY(450, 1300)
            click('teamup/ready_lobby', suppress=True, confidence=0.8, region=regions['bottom_buttons'])
            break # Break loop otherwise if we miss a button due to lag we loop here until battle starts

        # Wait until battle finishes
        while not isVisible('labels/tap_to_close', confidence=0.8, region=regions['bottom_buttons']):
            timer += 1
            if timer > 30:
                logger.info('Battle timeout error!\n')
                click_location('neutral') # Neutral taps to try and get back to main map if something went wrong
                return
        if isVisible('labels/tap_to_close', confidence=0.8, region=regions['bottom_buttons'], click=True):
            logger.info('Battle complete!\n')

        # Finish up and start the loop again
        timer = 0
        globals()['last_corrupt'] = time.time()
        return

def start_autoprogress():
    logger.info('Starting Auto-Progress')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    clickXY(100, 1800, seconds=4)  # Open AFK Rewards
    clickXY(750, 1750, seconds=4)  # Clear Pop-Up
    isVisible('buttons/claim_afkrewards', region=regions['middle_third'], click=True)

    if isVisible('labels/afk_rewards_woi', region=[0, 680, 150, 200]):
        clickXY(750, 1600, seconds=5)  # AFK Stage Battle
        click('buttons/autobattle', region=regions['bottom_buttons'])
        click('buttons/confirm', region=regions['confirm_deny'], seconds=3)
        click('buttons/auto-progress', seconds=3)
        click('buttons/confirm', seconds=6)
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Auto-Progress started!\n')
    else:
        logger.info('Issue starting Auto-Progress!')
        recover()


def claim_afk_rewards():
    logger.info('Claiming AFK Rewards')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    clickXY(100, 1800, seconds=4)  # Open AFK Rewards
    clickXY(750, 1750, seconds=4)  # Clear Pop-Up

    if isVisible('labels/afk_rewards_woi', region=[0, 680, 150, 200]):
        clickXY(550, 1400)  # Click Chest
        clickXY(550, 1080)  # Click Collect
        wait(2) # Wait and claim again to complete daily quest
        clickXY(550, 1400)  # Click Chest
        clickXY(550, 1080)  # Click Collect

        # Fast rewards
        if isVisible('labels/afk_rewards_woi', region=[0, 680, 150, 200]):
            for _ in range(config.getint('ACTIVITIES', 'fast_rewards')):
                if isVisible('buttons/fast_rewards', click=True):
                    logger.info('Fast reward #' + str(_ + 1) + ' claimed')
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

    wait(2) # For things to load
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
        if isVisible('labels/arena_weekly_report', region=regions['top_third']):
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
                if timeout > 40: # Should be about 10 seconds longer than a full fight at 2x
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
        click('buttons/dr_rewards', region=regions['top_third'], seconds=4)
        clickXY(550, 1800, seconds=2) # Clear loot
        click('buttons/back2', region=regions['back'], seconds=3)
    else:
        logger.info('issue collecting rewards!')
        recover()
        return

    # Then attempt a single battle
    if isVisible('buttons/battle', region=regions['bottom_buttons']):
        logger.info('Battling Dream Realm')
        click('buttons/battle', region=regions['bottom_buttons'], seconds=5)
        click('buttons/battle', region=regions['bottom_buttons'], seconds=5)
        time.sleep(60)  # wait for battle to end
        while not isVisible('labels/tap_to_close', region=regions['bottom_buttons']): # Few clicks to clear loot too
            timer += 1
            if timer > 60:
                logger.info('DR Timer Exceeded!')
                break
            pass
        click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=5, suppress=True)
        if isVisible('buttons/deny', click=True, seconds=3):
            logger.info('Not sharing formation..')
        click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=5, suppress=True)
        logger.info('Battle complete!')
        click('buttons/back', region=regions['back'], seconds=2)
        click('buttons/back2', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Dream Realm completed!\n')
    else:
        logger.info('Issue collecting rewards!')
        recover()
        return

def single_recruit():
    logger.info('Attempting a single reruitment')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    # Navigate and open all hero recruitment
    clickXY(300, 1850, seconds=6)
    clickXY(420, 700, seconds=6)
    click('buttons/all_hero_recruitment', seconds=6)

    # Perform recruit, lots of long waits here as the animations are slow before we stabilise again
    if isVisible('labels/all_hero_recruitment', region=regions['bottom_buttons']):
        clickXY(250, 1550)
        click('buttons/continue2') # long wait for animation
        wait(15)
        click('buttons/back')
        click('buttons/back2', seconds=3)
        click('buttons/back2')
        logger.info('Single recruitment complete!\n')
    else:
        logger.info('Issue doing single recruitment!')
        recover()
        return


def collect_quests():
    logger.info('Collecting Quests')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    click('buttons/main_menu', region=regions['main_menu'])
    click('buttons/quests', region=regions['menu_activities'],  seconds=3)
    clickXY(300, 1800, seconds=2)# Daily quests

    if isVisible('labels/daily_quests'):
        logger.info('    Collecting Daily Quests')
        isVisible('buttons/quick_claim', region=regions['bottom_third'], click=True)
        wait(3)
        if config.getboolean('ADVANCED', 'collect_daily_rewards') is True:
            clickXY(900, 200, seconds=2)  # collect dailies
            click_location('neutral')
        else:
            logger.info('Skipping daily quest rewards collection')

        # Guild quests
        logger.info('    Collecting Guild Quests')
        clickXY(500, 1800, seconds=2)
        while isVisible('buttons/quests_claim'):
            click('buttons/quests_claim')

        # Season Quests
        logger.info('    Collecting Season Growth Trials')
        clickXY(950, 1825, seconds=2)
        # Season Growth Trials
        while isVisible('labels/reward', click=True, region=(232, 451, 700, 100)):
            while isVisible('buttons/quests_claim'):
                click('buttons/quests_claim')
        # Season Growth Quests
        logger.info('    Collecting Season Growth Quests')
        clickXY(300, 1670, seconds=2)
        while isVisible('buttons/quests_claim'):
            click('buttons/quests_claim')

        click('buttons/back2', region=regions['back'])
        click('buttons/back', region=regions['back'])

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Quests collected!\n')
    else:
        logger.info('Issue collecting quests!')
        recover()
        return

def level_up_hero(times=10):
    for _ in range(times):
        wait(1)
        if _ < 9:
            clickXY(800, 1800, seconds=1)  # Click level up button
        else:
            clickXY(800, 1800, seconds=4)  # Click level up button

def equip_gear():
    clickXY(286, 1610, seconds=3)  # Open equipment selection
    clickXY(800, 1800, seconds=3)  # Equip the gear
    clickXY(90, 1785, seconds=3)   # Return to hero screen

def select_next_hero():
    clickXY(993, 1070, seconds=3)  # Select next hero

def maintenance_level(heroes=5, level_up_times=11):
    """
    Level up and equip gear for a specified number of Resonance Heroes in sequential order.

    Args:
        heroes (int): Number of heroes to level up and equip. Default is 5.
        level_up_times (int): Number of times to level up each hero. Default is 10.
    """
    logger.info(f'Leveling up and equipping {heroes} Resonance Heroes')

    try:
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

        # Open Heroes Hall
        clickXY(650, 1850, seconds=3)

        # Select first hero
        clickXY(115, 839, seconds=3.5)
        wait(1.5)

        for hero in range(heroes):
            logger.debug(f'Processing hero {hero + 1}/{heroes}')

            # Level up hero
            level_up_hero(level_up_times)

            # Equip new gear
            equip_gear()

            # Move to next hero if not the last one
            if hero < heroes - 1:
                select_next_hero()

    except Exception as e:
        logger.error(f'An error occurred: {e}')
        recover()
        return

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Hero leveling and equipment complete')
    else:
        logger.error('Failed to close Heroes Hall')
        recover()

def farm_affinity(heroes=60): # 60 heros in game as of Tasi
    logger.info('Clicking ' + str(heroes) + ' heroes for daily affinity bonus')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    counter = 1
    clickXY(650, 1850, seconds=5) # Open heroes hall
    clickXY(150, 1050, seconds=3) # Click top right hero

    if isVisible('buttons/affinity', region=regions['top_third']):
        while counter < heroes:
            if counter % 10 == 0:
                logger.info('Tapping ' + str(counter) + 'th hero')
            clickXY(550, 1000, seconds=1)
            clickXY(550, 1000, seconds=1)
            clickXY(550, 1000, seconds=1)
            clickXY(620, 1800, seconds=0.5)
            clickXY(1000, 1100, seconds=1.5)
            counter += 1
        click('buttons/back', region=regions['back'], seconds=2)
        click('buttons/back2', region=regions['back'])
        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Affinity farmed!\n')
    else:
        logger.info('Something went wrong opening hero affinity!')
        timestamp = datetime.now().strftime('%d-%m-%y_%H-%M-%S')
        save_screenshot('affinity_opening_issue_' + timestamp)
        recover()

def noble_path():
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Collecting noble path')
    click('buttons/main_menu', region=regions['main_menu'], seconds=2)
    click('buttons/noble_path', region=regions['menu_activities'], seconds=5)
    click('buttons/start', region=regions['bottom_buttons'], suppress=True, seconds=3) # To clear new noble pop-up

    def claim_and_collect(italics=True):
        # This will claim quests/collet rewards
        clickXY(750, 450) # Click Quests
        if isVisible('buttons/claim_all_italics', click=True, region=regions['bottom_third']):
            clickXY(1000, 1800) # Clear Loot
        # Travelogue
        clickXY(350, 450) # Click Trek
        if isVisible('buttons/claim_all_italics', click=True, region=regions['bottom_third']):
            clickXY(1000, 1800) # Clear Loot

    # Fabled Road
    logger.info('    Checking Fabled Road')
    if isVisible('buttons/fabled_road_active', region=regions['bottom_third'], seconds=2, grayscale=True) or isVisible('buttons/fabled_road_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
        claim_and_collect()

    # Seasonal Noble Path
    logger.info('    Checking Season Noble Path')
    if isVisible('buttons/noble_season_active', region=regions['bottom_third'], seconds=2, grayscale=True) or isVisible('buttons/noble_season_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
        claim_and_collect()

    # Noble Path
    logger.info('    Checking Noble Path')
    if isVisible('buttons/noble_path_active', region=regions['bottom_third'], seconds=2, grayscale=True) or isVisible('buttons/noble_path_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
        claim_and_collect()

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

    # Timeless Gala
    if isVisible('events/timeless_gala_active', seconds=2) or isVisible('events/timeless_gala_inactive', click=True, seconds=2):
        clickXY(750, 750, seconds=2)
        while isVisible('events/collect_gala', region=[650, 1100, 400, 550]):
            click('events/collect_gala')
        logger.info('Timeless Gala claimed')

    # All Heroes
    if isVisible('events/all_heroes', seconds=2) or isVisible('events/all_heroes_inactive', click=True, seconds=2):
        if isVisible('events/all_heroes_claim', click=True, confidence=0.8, retry=10, yrelative=100):
            logger.info('All Heroes claimed')
            click_location('neutral')

    # Swipe left for the next events
    swipe(1000, 1800, 250, 1800, 500, seconds=2)

    # Swallows Retreat
    if isVisible('events/swallows_retreat_inactive', click=True, seconds=2, region=regions['bottom_buttons']):
        clickXY(350, 1250) # Daily
        while isVisible('events/collect_sr'):
            click('events/collect_sr')
        clickXY(800, 1250) # Special
        while isVisible('events/collect_sr'):
            click('events/collect_sr')
        logger.info('Swallows Retreat claimed')

    # Fishing Diary
    if isVisible('events/fishing_diary_inactive', click=True, seconds=3, region=regions['bottom_buttons']):
        if isVisible('buttons/collect', click=True, confidence=0.8):
            logger.info('Fishing Diary claimed')

    click('buttons/back', region=regions['back'])
    click('buttons/back', region=regions['back'])
    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Events claimed!\n')

def blind_push(mode, tower=None, load_formation=True):

    def auto_load_formation():
        logger.info('Loading formation..')
        wait()
        click('buttons/records', seconds=2)
        click('buttons/copy', seconds=2)
        click('buttons/confirm', seconds=3, suppress=True)
        click("buttons/battle", seconds=3)

    # Opens first found tower and pushes until defeat, then exits
    if mode == "daily_towers":
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
        logger.info('Pushing tower until first defeat')
        clickXY(460, 1820, seconds=2)
        click("labels/legend_trial", seconds=3, retry=3)
        click_location('neutral') # To clear District popup

        factions = ["Light", "Wilder", "Graveborn", "Mauler"]
        for faction in factions:
            if isVisible("towers/"+faction.lower(), confidence=0.94, click=True, seconds=4, yrelative=-20):
                logger.info('Opening ' + faction + ' tower\n')
                if isVisible("towers/lvl", click=True, region=(15, 850, 1050, 800), seconds=3, yrelative=-50, grayscale=True):
                    if isVisible("buttons/battle"):
                        auto_load_formation()
                        back_occurence = 0 # Somehow this handles defeats and I'm not sure why
                        while True:
                            if isVisible("labels/tap_to_close", click=True, seconds=2):
                                click("buttons/back")
                                break
                            elif isVisible("buttons/next", click=True, retry=3, region=regions['bottom_buttons']):
                                logger.info(faction + ' win detected, moving to next floor')
                                wait(5)
                                back_occurence = 0
                                auto_load_formation()
                            elif isVisible("buttons/back"):
                                if back_occurence == 0:
                                    back_occurence = 1
                                else: # Exit if this counter reaches 1
                                    click("buttons/back")
                                    break
                            wait(5)
                else:
                    logger.info('Tower floor not found!')
                    break

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Towers pushed!\n')

    # Loads a tower and keeps retrying until victory, repeating for the next stage infinitely
    if mode == "push_tower":
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

        first_run = True
        logger.info('Pushing ' + tower.capitalize() + ' tower!\n')
        clickXY(460, 1820, seconds=4)
        click("labels/legend_trial", seconds=2)

        factions = ["graveborn", "light", "mauler", "wilder"]
        for faction in factions:
            if faction == tower:
                if isVisible("towers/"+faction.lower(), confidence=0.95, click=True, seconds=4, yrelative=-20):
                    if isVisible("towers/lvl", click=True, region=(15, 850, 1050, 800), seconds=3, yrelative=-50, grayscale=True):
                        auto_load_formation()
                        while True:
                            # click("buttons/abyss_lvl", seconds=5, suppress=True, grayscale=True, confidence=0.8)
                            # if first_run is True:
                            #     auto_load_formation()
                            #     first_run = False
                            click("buttons/battle", suppress=True, region=regions['bottom_buttons'])
                            click("buttons/retry", suppress=True, region=regions['bottom_buttons'])
                            if isVisible("buttons/next", click=True, seconds=4, region=regions['bottom_buttons']):
                                logger.info(faction.capitalize() + ' win detected, moving to next floor\n')
                                auto_load_formation()
                                click("buttons/battle", seconds=3, suppress=True)

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Towers pushed!\n')

    # Retries Abyss stages, probably very outdated at this point
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

    # Not completely sure what this does (apart from the obvious)
    if mode == "dream_realm":
        logger.info('Auto-retrying Dream Realm')
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

        clickXY(450, 1825, seconds=3)
        click('buttons/dream_realm', region=regions['battle_modes'], seconds=3)
        
        for _ in range(19):
            if isVisible('buttons/battle', region=regions['bottom_buttons'], click=True, seconds=5): # Enter battle screen
                logger.info('Starting battle')
                if isVisible('buttons/confirm', click=True, region=regions['confirm_deny']): # Purchase Gold Attempts
                    click('buttons/battle', region=regions['bottom_buttons'], retry=2, seconds=5) # 2 retries or it catches the button on the next screen and breaks battle detection
                if isVisible('buttons/battle', region=regions['bottom_buttons'], click=True, seconds=5): # Start battle
                    logger.info('Starting encounter')
                    if isVisible('buttons/battle', region=regions['bottom_buttons']):  # Start battle
                        logger.info('Out of attempts! Exiting..\n')
                        return
                    time.sleep(60) # wait for battle to end
                    logger.info('Encounter ended')
                    while not isVisible('labels/tap_to_close', region=regions['bottom_buttons']):
                        logger.info('waiting for tap to close')
                        pass
                    click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=5)
                    if isVisible('buttons/deny', click=True, seconds=3):
                        logger.info('Skipping formation sharing..')
                    click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=5, suppress=True)
                    logger.info('Dream Realm Battle #' + str(_+1) + ' complete!')
            else:
                logger.info('Battle button not found! (battle ' + str(_) + ' )')

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Dream Realm attempts exhausted.\n')

    # For pushing afk stages
    if mode == 'afkstages':
        timeout = 0
        if isVisible('buttons/records', region=regions['bottom_buttons'], seconds=0, retry=10):

            # Change formation if we we beat the 2nd round or have defeat >10 times in a row
            if load_formation is True or globals()['afk_stage_defeats'] >= config.getint('PUSHING', 'defeat_limit'):
                # More than 10 defeats in a row and a multiple of 10 (i.e load new formation on 10th/20th/30th etc defeat)
                if globals()['afk_stage_defeats'] >= 1 and globals()['afk_stage_defeats'] % config.getint('PUSHING', 'defeat_limit') == 0:
                    click('buttons/records', seconds=2)
                    counter = 0
                    clicks = (globals()['afk_stage_defeats'] / config.getint('PUSHING', 'defeat_limit')) + 1 # number of defeats / defeat_limit, plus 1 as we start on formation #1
                    logger.info(str(globals()['afk_stage_defeats']) + ' defeats, trying formation ' + str(math.trunc(clicks)))
                    while counter != clicks:
                        clickXY(1000, 1025)
                        counter += 1
                    click('buttons/copy', seconds=2)
                    click('buttons/confirm', seconds=2, suppress=True)
                    if globals()['first_stage_won'] is True:
                        clickXY(550, 1100)
                elif load_formation is True:
                    logger.info('Loading formation')
                    click('buttons/records', seconds=2)
                    click('buttons/copy', seconds=1)
                    click('buttons/confirm', seconds=0, suppress=True)

            # Stage check, different actions are taken depending on first or second stage in a multi
            if isVisible('labels/multis_first_victory', seconds=0):
                globals()['first_stage_won'] = True

            # Start Battle
            click('buttons/battle', retry=5, region=regions['bottom_buttons'], seconds=0)
            # TODO un-owned hero popup has 'confirm' text button
            click('buttons/confirm', seconds=0, suppress=True)

            if globals()['first_stage_won'] is False:
                # Wait until we see the 'Continue' after tha battle
                while not isVisible('buttons/continue_stages', region=regions['bottom_buttons'], grayscale=True, confidence=0.85):
                    timeout += 1
                    if timeout > 30: # If nothing at 30 seconds start clicking in case battery saver mode is active
                        logger.info('Possibly stuck, checking if it\'s the energysaver screen..')
                        click_location('neutral')
                    if timeout > 60: # Still nothing at 60 seconds? Quit as somethings gone wrong
                        logger.info('Battle timeout error!')
                        break
                    wait()

                # Then check for Victory or Defeat
                timeout = 0 # Reset timer on victory and or defeat
                result_value = isVisible_array(['labels/defeat', 'labels/victory'], confidence=0.9)
                # logger.info(result_value) # debug line
                if result_value == 'labels/defeat': # Blue above 120 is defeat screen
                    globals()['afk_stage_defeats'] += 1
                    logger.info('Defeat #' + str(globals()['afk_stage_defeats']) + '! Retrying')
                    clickXY(550, 1800, seconds=3)
                    blind_push('afkstages', load_formation=False)
                elif result_value == 'labels/victory': # Blue under 90 is orange-y, so the victory screen
                    globals()['afk_stage_defeats'] = 0
                    logger.info('First round won!')
                    clickXY(730, 1800, seconds=3)
                    blind_push('afkstages', load_formation=False)
                else:
                    logger.info('Unknown stage result.')
                    sys.exit(0)

            if globals()['first_stage_won'] is True:
                # Wait for battle to end with either Continue button or Back button
                while not isVisible('buttons/continue_stages', region=regions['bottom_buttons']):
                    timeout += 1
                    if timeout > 30: # If nothing at 30 seconds start clicking in case battery saver mode is active
                        click_location('neutral')
                    if timeout > 60: # Still nothing at 60 seconds? Quit as somethings gone wrong
                        logger.info('Battle timeout error!')
                        break
                    if isVisible('buttons/back', region=regions['bottom_buttons'], seconds=0):
                        break
                    wait()
                # Continue on second battle is always defeat
                if isVisible('buttons/continue_stages', region=regions['bottom_buttons']):
                    globals()['afk_stage_defeats'] += 1
                    logger.info('Defeat #' + str(globals()['afk_stage_defeats']) + '! Retrying')
                    clickXY(730, 1800, seconds=3)
                    blind_push('afkstages', load_formation=False)
                # If we see a Back button we're at the Stage Passed screen (or seriously lost)
                if isVisible('buttons/back', region=regions['bottom_buttons']):
                    globals()['afk_stage_defeats'] = 0
                    logger.info('Second round won! Stage passed!\n')
                    clickXY(750, 1800, seconds=4)
                    globals()['first_stage_won'] = False
                    blind_push('afkstages', load_formation=True)

        else:
            logger.info('Something went wrong opening AFK Stages!')
            recover()

def open_afk_stages(afkstages=True):
    clickXY(100, 1800, seconds=4)  # Open AFK Rewards
    if afkstages is True:
        logger.info('Opening AFK Stages')
        logger.info('Changing formations after ' + str(config.getint('PUSHING', 'defeat_limit')) + ' defeats\n')
        clickXY(715, 1600, seconds=2)  # Battle
        clickXY(715, 1600, seconds=2)  # Battle (again since first can claim afk rewards when its >1h)
    else:
        logger.info('Opening Talent Stages\n')
        clickXY(370, 1600, seconds=2)  # Battle
        clickXY(370, 1600, seconds=2)  # Battle (again since first can claim afk rewards when its >1h)

def charms():
    def load_formation():
        logger.info('Loading formation')
        click('buttons/records', seconds=2)
        click('buttons/copy', seconds=2, suppress=True)
        click('buttons/confirm', seconds=3, suppress=True)

    def go_back(exit_mode=False):
        click('buttons/confirm', suppress=True)
        click('buttons/back', suppress=True)
        click('buttons/back', suppress=True)
        if exit_mode is True:
            click('buttons/back', suppress=True)
            click('buttons/back2', suppress=True)

    top_max_floor = False
    bottom_max_floor = False

    # Open Trials screen
    logger.info('Running Dura\'s Trials!\n')
    clickXY(450, 1825, seconds=3)
    clickXY(200, 1000, seconds=3)

    # Check top row
    logger.info('Checking top row Charm Trials..')
    if isVisible('buttons/rate_up', grayscale=True, click=True, region=(50, 1175, 950, 150), confidence=0.75, seconds=3):
        clickXY(750, 1800, seconds=6)
        if isVisible('buttons/sweep', seconds=0):
            logger.info('Max floor reached! Checking bottom row..\n')
            top_max_floor = True
            go_back()
        if top_max_floor is False:
            load_formation()
            while 1 == 1:
                click('buttons/battle', retry=1, suppress=True, seconds=0)
                if isVisible('labels/multiple_attempts', seconds=0):
                    logger.info('Out of tries! Checking bottom row..\n')
                    go_back()
                    break
                click('buttons/confirm', retry=1, suppress=True, seconds=0)
                if isVisible('buttons/retry', retry=1, click=True, seconds=3, region=(650, 1750, 200, 150)):
                    logger.info('Defeat..')
                if isVisible('buttons/next2', retry=1, click=True, seconds=5):
                    logger.info('Victory!')
                    load_formation()
    else:
        logger.info("Top row not found..")

    logger.info('Checking bottom row Charm Trials..')
    if isVisible('buttons/rate_up', grayscale=True, click=True, region=(50, 1400, 950, 150), confidence=0.75, seconds=3):
        clickXY(750, 1800, seconds=6)
        if isVisible('buttons/sweep', seconds=0):
            logger.info('Max floor reached! Checking bottom row..\n')
            bottom_max_floor = True
            go_back()
        if bottom_max_floor is False:
            load_formation()
            while 1 == 1:
                click('buttons/battle', retry=1, suppress=True, seconds=0)
                if isVisible('labels/multiple_attempts', seconds=0):
                    logger.info('Out of tries! Exiting..\n')
                    go_back(exit_mode=True)
                    break
                click('buttons/confirm', retry=1, suppress=True, seconds=0)
                if isVisible('buttons/retry', retry=1, click=True, seconds=3, region=(650, 1750, 200, 150)):
                    logger.info('Defeat..')
                if isVisible('buttons/next2', retry=1, click=True, seconds=5):
                    logger.info('Victory!')
                    load_formation()
    else:
        logger.info("Bottom row not found..")


# Scans and pushes the various buttons needed to complete story/side quests
# Very slow, can get stuck if there is a player present at an end point and we get the magnifying glass icon instead of the action icon
# The order of checks and clicks is important to not get stuck in loops
#TODO Get chest icon for collecting quest items / First run teleport prompt
def quest_push():
    logger.info('Pushing Quests!\n')
    buttons = ['buttons/battle', 'buttons/skip', 'buttons/dialogue_option', 'buttons/confirm', 'buttons/red_dialogue', 'buttons/interact',
               'buttons/dialogue', 'buttons/tap_and_hold', 'buttons/enter', 'buttons/chest', 'buttons/battle_button', 'labels/questrewards',
               'buttons/woi_ship', 'labels/tap_to_close', 'buttons/track']
    while True:

        click_array(buttons, suppress=True)
        if isVisible('buttons/tap_and_hold', region=regions['chat_window'], seconds=0):
            logger.info('Holding button')
            swipe(550, 1250, 550, 1250, 4000)  # Hacky way to hold it down

# Placeholder for when I get round to it
#def run_lab():
#    if lab is not completed:
#        run_lab()


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
    blind_push('towers')

if args['quest']:
    quest_push()

if args['dream']:
    blind_push('dream_realm')

if args['test']:
    noble_path()

if args['charms']:
    charms()

if args['afks']:
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    open_afk_stages(afkstages=True)
    blind_push('afkstages')

if args['afkt']:
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    open_afk_stages(afkstages=False)
    blind_push('afkstages')

# If no function launch argument we pop the UI

options = ["Run Dailies", "Push Towers", "Push AFK Stages", "Push AFK Talent Stages", "Push Dura's Trials", "Run Quests", "Use Dream Realm attempts", "Farm Team-Up Chat"]
selection = SelectionMenu.get_selection(options, title='Welcome to AutoAFK2! Select an activity:', subtitle='Note that to stop a task or start a new one you have to restart the bot. Questions? Jc.2 @ Discord')
selection += 1 # Non-zero index to make things easier to read

if selection == 1:
    dailies()

if selection == 2:
    tower_menu = []
    open_towers = {1: ["Push Lightbringer Tower"],
                   2: ["Push Mauler Tower"],
                   3: ["Push Wilder Tower"],
                   4: ["Push Graveborn Tower"],
                   5: ["Push Lightbringer Tower", "Push Mauler Tower"],
                   6: ["Push Wilder Tower", "Push Graveborn Tower"],
                   7: ["Push Lightbringer Tower", "Push Wilder Tower", "Push Mauler Tower", "Push Graveborn Tower"]}

    # Add tower to the list if it's unlocked
    for day, towers in open_towers.items():
        if currenttimeutc.isoweekday() == day:
            tower_menu.extend(towers)
    selection = SelectionMenu.get_selection(tower_menu, title='Which Tower:')
    selection += 1  # Non-zero index to make things easier to read

    # SelectionMenu only returns an int so here's a hacky way to work out which tower was selected. It ain't pretty.

    if selection == 1:
        day = currenttimeutc.isoweekday()
        if day == 1:
            blind_push('push_tower', 'light')
        if day == 2:
            blind_push('push_tower', 'mauler')
        if day == 3:
            blind_push('push_tower', 'wilder')
        if day == 4:
            blind_push('push_tower', 'graveborn')
        if day == 5:
            blind_push('push_tower', 'light')
        if day == 6:
            blind_push('push_tower', 'wilder')
        if day == 7:
            blind_push('push_tower', 'light')

    if selection == 2:
        day = currenttimeutc.isoweekday()
        if day == 5:
            blind_push('push_tower', 'mauler')
        if day == 6:
            blind_push('push_tower', 'graveborn')
        if day == 7:
            blind_push('push_tower', 'wilder')

    if selection == 3:
        if day == 7:
            blind_push('push_tower', 'wilder')

    if selection == 4:
        day = currenttimeutc.isoweekday()
        if day == 7:
            blind_push('push_tower', 'mauler')

if selection == 3:
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Auto-pushing AFK Stages')
    open_afk_stages(afkstages=True)
    blind_push('afkstages', load_formation=True)

if selection == 4:
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Auto-pushing AFK Talent Stages')
    open_afk_stages(afkstages=False)
    blind_push('afkstages', load_formation=True)

if selection == 5:
    charms()

if selection == 6:
    quest_push()

if selection == 7:
    blind_push('dream_realm')

if selection == 8:
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


