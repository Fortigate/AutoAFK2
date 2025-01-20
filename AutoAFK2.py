import argparse
import inspect
import math
import sys

from humanfriendly import format_timespan
from tools import * # Includes logging so we don't import here also
from consolemenu import *
from datetime import datetime, timezone
import ctypes

# Global variables
global last_synergy
last_synergy = time.time() - 300 # -300 so we don't wait 300 seconds before opening the first
global last_corrupt
last_corrupt = time.time()

# For stage pushing
global stage_defeats
stage_defeats = 0
global formation
formation = 1
global first_stage_won
first_stage_won = False

# placeholder gets replaced during build process with release tag.
version = '3.2.1'

# Current time in UTC for tracking which towers/events are open
currenttimeutc = datetime.now(timezone.utc)

# Game version to launch
global server
server = 'com.farlightgames.igame.gp'

# Enabling/Disabling formation loading
global load_formations
load_formations = True

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
parser.add_argument("-proxy", action='store_true', help="Run the Chain AFK Proxy function")
parser.add_argument("-fs", "--formation_skip", action='store_true', help="Don't load formations")
# Configurations
parser.add_argument("-s", "--server", choices=['global', 'vn'], default='global', help="Select alernative game servers")
parser.add_argument("-c", "--config", metavar="CONFIG", default="settings.ini", help="Define alternative settings file to load")
parser.add_argument('--forceprint', action='store_true', help='Force print output')
args = vars(parser.parse_args())

def get_current_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return cwd

settings = os.path.join(get_current_dir(), args['config'])
config.read(settings)

# Change server if necessary
if args['server'] == 'vn':
    globals()['server'] = 'com.farlightgames.igame.gp.vn'

# Disable formation loading if set
if args['formation_skip']:
    logger.info('Formation skip active')
    globals()['load_formations'] = False

# Make a nice name for the output log file if it's the default
if str(settings.split('\\')[-1]) == 'settings.ini':
    logname = 'autoafk2.log'
else:
    logname = settings.split('.')[0] + '.log'

from threading import Event

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
    'action_buttons': (400, 1050, 300, 500), # gives out of bounds error and I'm too tired to work out why
    'levelup': (150, 900, 950, 50),
    'levelup_hero': (1000, 1700, 80, 60),
    'x3_and_skip': (720, 1450, 350, 110)
}

# Boot up text
logger.info('Loaded settings file: ' + str(settings.split('\\')[-1]))
logger.info('Version: ' + version)

# Nice name for the window and debugging peoples screenshots
ctypes.windll.kernel32.SetConsoleTitleW("AutoAFK2 v" + version)

# Boot up activities before tasks are ran
connect_and_launch(port=config.get('ADVANCED', 'port'), server=globals()['server'])
resolutionCheck()
if not args['proxy']:
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
    if config.getboolean('ACTIVITIES', 'emporium_purchases'):
        emporium_purchases()
    if config.getboolean('ACTIVITIES', 'single_recruit'):
        single_recruit()
    if config.getint('ACTIVITIES', 'arena_battles') > 0:
        arena(config.getint('ACTIVITIES', 'arena_battles'))
    if config.getboolean('ACTIVITIES', 'dream_realm'):
        dream_realm()
    if config.getboolean('ACTIVITIES', 'push_towers'):
        blind_push("daily_towers")
    if config.getboolean('ACTIVITIES', 'collect_quests'):
        collect_quests()
    if config.getboolean('ACTIVITIES', 'claim_events'):
        claim_events()
    if config.getboolean('ACTIVITIES', 'noble_path'):
        noble_path()
    if config.getboolean('ACTIVITIES', 'level_up'):
        level_up()
    if config.getboolean('ACTIVITIES', 'push_dream_realm'):
        blind_push("dream_realm")
    if config.getboolean('ACTIVITIES', 'farm_affinity'):
        farm_affinity()
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

    if isVisible('labels/afk_rewards_coe', region=[0, 680, 150, 200]):
        clickXY(550, 1400)  # Click Chest
        clickXY(550, 1080)  # Click Collect
        wait(2) # Wait and claim again to complete daily quest
        clickXY(550, 1400)  # Click Chest
        clickXY(550, 1080)  # Click Collect

        # Fast rewards
        if isVisible('labels/afk_rewards_coe', region=[0, 680, 150, 200]):
            for _ in range(config.getint('ACTIVITIES', 'fast_rewards')):
                if isVisible('buttons/fast_rewards', click=True):
                    logger.info('Fast reward #' + str(_ + 1) + ' claimed')
                    click('buttons/confirm', suppress=True)
                    clickXY(800, 1800)

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
    click('buttons/guild_store')
    if isVisible('labels/emporium_guild', region=regions['top_third']):
        if isVisible('emporium/guild_summoncard'):
            click('emporium/guild_summoncard', region=regions['middle_third'])
            click('buttons/purchase', region=regions['bottom_buttons'])
            click('buttons/confirm', region=regions['confirm_deny'], seconds=2)
            click_location('neutral')
        else:
            logger.info('Daily card already purchased!')
        click('buttons/back2', region=regions['back'], seconds=2)
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
                if isVisible('buttons/skip_inverse', seconds=0, region=regions['x3_and_skip']):
                    click('buttons/skip_inverse', seconds=3, region=regions['x3_and_skip'])
                    click('buttons/confirm', suppress=True)
                    logger.info('Skip available, skipping the fight')
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
    clickXY(1000, 50) # Clear new season info popup

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
            if isVisible('labels/dr_first_kill'):
                clickXY(550, 1800) # clear rewards popup
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
    click('buttons/all_hero_recruitment', seconds=7)

    # Perform recruit, lots of long waits here as the animations are slow before we stabilise again
    if isVisible('labels/all_hero_recruitment', region=regions['bottom_buttons']):
        clickXY(250, 1550)
        click('buttons/continue2', suppress=True) # long wait for animation
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

        # Season Growth Quests
        logger.info('    Collecting Season Growth Quests')
        clickXY(300, 1670, seconds=2)
        while isVisible('buttons/quests_claim'):
            click('buttons/quests_claim')

        # Season Growth Trials
        clickXY(800, 1670, seconds=2)
        while isVisible('labels/reward', click=True, region=(232, 451, 700, 100)):
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

def level_up():
    logger.info('Levelling available heroes')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    # Clicks the central button when leveling uses Dust rather than XP, then presses back to return to the selected hero screen
    def dust_level():
        if isVisible('buttons/level_up', region=(500, 1725, 260, 100), seconds=0):  # Region in the centre for the 10th level 'Level Up' button
            click('buttons/level_up', region=regions['bottom_third'], seconds=4)

    # Open Heroes Hall
    clickXY(650, 1850, seconds=3)

    # Level up all if enabled
    if config.getboolean('ADVANCED', 'use_level_up_all'):
        while isVisible('buttons/level_up_all_active', region=regions['bottom_third'], confidence=0.92):
            click('buttons/level_up_all_active', region=regions['bottom_third'], confidence=0.92) # sligtly higher confidence as inactive is the same but greyscale
            logger.info('Level up all clicked!')
    # Else we level the heros individually
    else:
        # Click to open hero
        while isVisible('buttons/levelup_double', region=regions['levelup']) or isVisible('buttons/levelup_single', region=regions['levelup']):
            logger.info('Hero found!')
            click('buttons/levelup_double', region=regions['levelup'], suppress=True, retry=1)
            click('buttons/levelup_single', region=regions['levelup'], suppress=True, retry=1)
            # Keep clicking to level
            while isVisible('buttons/levelup_double', region=regions['levelup_hero'], seconds=0):
                dust_level()
                swipe(800, 1800, 800, 1800, 5000)  # Hacky way to hold it down
                dust_level()
            while isVisible('buttons/levelup_single', region=regions['levelup_hero'], seconds=0):
                dust_level()
                swipe(800, 1800, 800, 1800, 5000)  # Hacky way to hold it down
                dust_level()
            click('buttons/back', region=regions['bottom_third'], seconds=3, suppress=True, retry=1) # Back to Hero Box

    logger.info('Done!')

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Heroes levelled!\n')

def farm_affinity(): # 100 is a failsafe in case we don't see Chippy
    logger.info('Clicking all heroes for daily +6 affinity bonus')
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')

    rare_counter = 0
    clickXY(650, 1850, seconds=5) # Open heroes hall
    clickXY(150, 1050, seconds=3) # Click top right hero

    if isVisible('buttons/affinity', region=regions['top_third']):
        while rare_counter < 3:
            if isVisible('labels/rare_hero', region=[15, 5, 105, 65]):
                logger.info('Hamster spotted!')
                rare_counter += 1
            for clicks in range(3):
                clickXY(550, 1000, seconds=1)
                clickXY(100, 1800, seconds=1)
            clickXY(1000, 1100, seconds=1.5)
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
        if isVisible('buttons/quick_claim', click=True, region=regions['bottom_third'], seconds=5): # Can also be 'claim_all_italics'
            clickXY(1000, 1800) # Clear Loot
        # # Travelogue
        # clickXY(350, 450) # Click Trek
        # if isVisible('buttons/claim_all_italics', click=True, region=regions['bottom_third']):
        #     clickXY(1000, 1800) # Clear Loot

    # # Fabled Road
    # logger.info('    Checking Fabled Road')
    # if isVisible('buttons/fabled_road_active', region=regions['bottom_third'], seconds=2, grayscale=True) or isVisible('buttons/fabled_road_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
    #     claim_and_collect()

    # Seasonal Noble Path
    logger.info('    Checking Season Noble Path')
    if isVisible('buttons/noble_season_active', region=regions['bottom_third'], seconds=2, grayscale=True) or isVisible('buttons/noble_season_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
        claim_and_collect()

    # # Noble Path
    # logger.info('    Checking Noble Path')
    # if isVisible('buttons/noble_path_active', region=regions['bottom_third'], seconds=2, grayscale=True) or isVisible('buttons/noble_path_inactive', region=regions['bottom_third'], click=True, seconds=2, grayscale=True):
    #     claim_and_collect()

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Noble path collected!\n')
    else:
        logger.info('Something went wrong collecting Season Noble path!')
        recover()

def claim_events():
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    logger.info('Claiming event rewards')
    # click('buttons/main_menu', region=regions['main_menu'], seconds=3)
    # click('buttons/event', region=regions['menu_activities'], seconds=3)

    # Guild Supremacy
    clickXY(770, 1830, seconds=4)
    if isVisible('labels/guild_supremacy'):
        clickXY(530, 1820, seconds=2) # Tap to Close
        clickXY(1000, 100)
        if isVisible('labels/guild_medal_reward'):
            clickXY(530, 1820, seconds=2)  # Tap to Close
            logger.info('Daily Guild Supremacy rewards collected!')
        else:
            logger.info('Guild Supremacy rewards not found, recovering..')
            recover()
    else:
        logger.info('Guild Supremacy contribution screen not found!')

    # # Timeless Gala
    # if isVisible('events/timeless_gala_active', seconds=2) or isVisible('events/timeless_gala_inactive', click=True, seconds=2):
    #     clickXY(750, 750, seconds=2)
    #     while isVisible('events/collect_gala', region=[650, 1100, 400, 550]):
    #         click('events/collect_gala')
    #     logger.info('Timeless Gala claimed')
    #
    # # All Heroes
    # if isVisible('events/all_heroes', seconds=2) or isVisible('events/all_heroes_inactive', click=True, seconds=2):
    #     if isVisible('events/all_heroes_claim', click=True, confidence=0.8, retry=10, yrelative=100):
    #         logger.info('All Heroes claimed')
    #         click_location('neutral')
    #
    # # Swipe left for the next events
    # swipe(1000, 1800, 250, 1800, 500, seconds=2)
    #
    # # Swallows Retreat
    # if isVisible('events/swallows_retreat_inactive', click=True, seconds=2, region=regions['bottom_buttons']):
    #     clickXY(350, 1250) # Daily
    #     while isVisible('events/collect_sr'):
    #         click('events/collect_sr')
    #     clickXY(800, 1250) # Special
    #     while isVisible('events/collect_sr'):
    #         click('events/collect_sr')
    #     logger.info('Swallows Retreat claimed')
    #
    # # Fishing Diary
    # if isVisible('events/fishing_diary_inactive', click=True, seconds=3, region=regions['bottom_buttons']):
    #     if isVisible('buttons/collect', click=True, confidence=0.8):
    #         logger.info('Fishing Diary claimed')
    #
    # click('buttons/back', region=regions['back'])
    # click('buttons/back', region=regions['back'])
    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Events claimed!\n')

def formation_handler(formation_number=1, already_open=False):

    if globals()['load_formations'] is False:
        logger.info('Formation loading disabled')
        return

    if globals()['formation'] > 7:
        logger.info('Formation selected higher than 7, starting from 1 again..')
        globals()['formation'] = 1

    logger.info('Loading formation #' + str(math.trunc(globals()['formation'])))
    counter = 1
    unowned_counter = 0
    wait()
    if already_open is False: # Sometimes we're already in the formations menu
        click('buttons/records', seconds=3)
    while counter != formation_number:
        clickXY(1000, 1025)
        counter += 1
    click('buttons/copy', seconds=2)
    # Handle 'Hero not owned' popup
    if isVisible('labels/not_owned'):
        while isVisible('labels/not_owned'): # Try next formation and check again
            logger.info('Hero/Artifact not owned, trying next formation..')
            clickXY(360, 1250)
            clickXY(1000, 1025)
            click('buttons/copy')
            globals()['formation'] += 1
            unowned_counter += 1
            if unowned_counter > 7:
                logger.info('All formations contained an unowned hero!')
                click_location('neutral') # Close windows back to battle screen
                click_location('neutral') # Close windows back to battle screen
                break
    click('buttons/confirm', suppress=True)

def blind_push(mode, tower=None, load_formation=True):

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
                        formation_handler()
                        click("buttons/battle")
                        while True:
                            if isVisible("buttons/next", click=True, retry=3, seconds=5, region=regions['bottom_buttons']):
                                logger.info(faction + ' win detected, moving to next floor')
                                click("buttons/battle", retry=5)
                            elif isVisible("buttons/retry", region=regions['bottom_buttons']):
                                logger.info(faction + ' defeat!')
                                click("buttons/back")
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

        logger.info('Pushing ' + tower.capitalize() + ' tower!\n')
        clickXY(460, 1820, seconds=4)
        click("labels/legend_trial", seconds=2)

        factions = ["graveborn", "light", "mauler", "wilder"]
        for faction in factions:
            if faction == tower:
                if isVisible("towers/"+faction.lower(), confidence=0.95, click=True, seconds=4, yrelative=-20):
                    if isVisible("towers/lvl", click=True, region=(15, 850, 1050, 800), seconds=3, yrelative=-50, grayscale=True):
                        formation_handler()
                        while True:
                            click("buttons/battle", suppress=True, region=regions['bottom_buttons'])
                            if isVisible("buttons/next", click=True, seconds=4, region=regions['bottom_buttons']):
                                logger.info(faction.capitalize() + ' win detected, moving to next floor\n')
                                globals()['stage_defeats'] = 0
                                formation_handler()
                            if isVisible("buttons/retry", click=True, region=regions['bottom_buttons']):
                                # Increment defeats
                                globals()['stage_defeats'] += 1
                                # If were past the defeat cap handle formation change, else standard log output
                                if globals()['stage_defeats'] >= 1 and globals()['stage_defeats'] % config.getint('PUSHING', 'defeat_limit') == 0:
                                    globals()['formation'] = (globals()['stage_defeats'] / config.getint('PUSHING', 'defeat_limit')) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                                    logger.info(str(globals()['stage_defeats']) + ' defeats, trying next formation')
                                    wait()
                                    formation_handler(globals()['formation'])
                                else:
                                    logger.info('Defeat #' + str(globals()['stage_defeats']) + '! Retrying')


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

    # Runs all available DR attempts
    if mode == "dream_realm":
        logger.info('Using all Dream Realm attempts')
        safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
        dr_counter = 0

        clickXY(450, 1825, seconds=3)
        click('buttons/dream_realm', region=regions['battle_modes'], seconds=3)

        # 20 Attempts
        for _ in range(19):
            # Handle opening the Battle
            if isVisible('buttons/battle', region=regions['bottom_buttons'], click=True, seconds=5): # Enter battle screen
                # Purchase Gold Attempts if it pops up
                if isVisible('buttons/confirm', click=True, region=regions['confirm_deny']):
                    click('buttons/battle', region=regions['bottom_buttons'], retry=2, seconds=5) # 2 retries or it catches the button on the next screen and breaks battle detection
                # Start the Battle
                logger.info('Starting Battle')
                if isVisible('buttons/battle', region=regions['bottom_buttons'], click=True, seconds=5, retry=5):
                    # If button is still visible after pressing we're out of attempts
                    if isVisible('buttons/battle', region=regions['bottom_buttons']):  # Start battle
                        logger.info('Out of attempts! Exiting..\n')
                        return
                    # When we haven't seen the x3 button three times in a row we can assume the battle is over
                    while dr_counter < 3:
                        if isVisible('buttons/skip_inverse', seconds=0, region=regions['x3_and_skip']):
                            click('buttons/skip_inverse', seconds=2, region=regions['x3_and_skip'])
                            click('buttons/confirm', seconds=3, region=regions['confirm_deny'], suppress=True)
                            logger.info('Skip available, skipping the fight')
                            dr_counter = 0
                        else:
                            dr_counter += 1
                    click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=5, retry=10, confidence=0.8)
                    if isVisible('buttons/deny', click=True, seconds=3):
                        logger.info('Skipping formation sharing..')
                        click('labels/tap_to_close', region=regions['bottom_buttons'], seconds=5, suppress=True)
                    logger.info('Dream Realm Battle #' + str(_+1) + ' complete!')
                    dr_counter = 0
            else:
                logger.info('Battle button not found! (battle ' + str(_) + ')')
                debug_screen('dr_battle_not_found')

        if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
            logger.info('Dream Realm attempts exhausted.\n')

    # For pushing afk stages
    if mode == 'afkstages':
        timeout = 0
        timeout_warned = False
        if isVisible('buttons/records', region=regions['bottom_buttons'], seconds=0, retry=20):

            # Change formation if we we beat the 2nd round or have defeat >10 times in a row
            if load_formation is True or globals()['stage_defeats'] >= config.getint('PUSHING', 'defeat_limit'):
                # More than 10 defeats in a row and a multiple of 10 (i.e load new formation on 10th/20th/30th etc defeat)
                if globals()['stage_defeats'] >= 1 and globals()['stage_defeats'] % config.getint('PUSHING', 'defeat_limit') == 0:
                    globals()['formation'] = (globals()['stage_defeats'] / config.getint('PUSHING', 'defeat_limit')) + 1 # number of defeats / defeat_limit, plus 1 as we start on formation #1
                    logger.info(str(globals()['stage_defeats']) + ' defeats, trying next formation')
                    formation_handler(globals()['formation'])
                    if globals()['first_stage_won'] is True: # Manually select second round if we've won the first
                        wait() # To stop getting stuck if this buttons not pressed
                        clickXY(550, 1100)
                elif load_formation is True:
                    formation_handler(globals()['formation'])

            # Season 3 single stage code

            # Start Battle
            click('buttons/battle', retry=5, region=regions['bottom_buttons'], seconds=0)
            click('buttons/confirm', seconds=0, suppress=True)

            # Wait til we see the back button in the post battle screen
            while not isVisible('buttons/back', region=regions['bottom_buttons'], seconds=2):
                timeout += 1
                if timeout > 30:  # If nothing at 30 seconds start clicking in case battery saver mode is active
                    click_location('neutral')
                if timeout > 60:  # Still nothing at 60 seconds? Quit as somethings gone wrong
                    logger.info('Battle timeout error!')
                    break
            wait()
            # Retry button indicates defeat, we run the defeat logic
            if isVisible('buttons/retry', region=regions['bottom_buttons']):
                globals()['stage_defeats'] += 1
                logger.info('Defeat #' + str(globals()['stage_defeats']) + '! Retrying')
                clickXY(730, 1800, seconds=3)
                blind_push('afkstages', load_formation=False)
            # If there's no 'Retry' button post battle, we assume victory (as normal and talent stages have different buttons here to continue)
            else:
                globals()['stage_defeats'] = 0  # Reset defeats
                globals()['formation'] = 1  # Reset formation
                logger.info('Victory! Stage passed\n')
                clickXY(750, 1800, seconds=4)
                globals()['first_stage_won'] = False
                blind_push('afkstages', load_formation=True)

            # Season 2 multi battle legacy code

            # # If multis_first_victory we know we've won the first round, if not formation_swap it's not a multi so we jump to the second fight check
            # if isVisible('labels/multis_first_victory', seconds=0):
            #     globals()['first_stage_won'] = True
            # if not isVisible('buttons/formation_swap', seconds=0):
            #     globals()['first_stage_won'] = True
            #
            # # Start Battle
            # click('buttons/battle', retry=5, region=regions['bottom_buttons'], seconds=0)
            # click('buttons/confirm', seconds=0, suppress=True)
            #
            # # In a multi first stage always gives 'Continue' screen so we check for that for victory/defeat markers
            # if globals()['first_stage_won'] is False:
            #     result_value = isVisible_array(['labels/defeat', 'labels/victory'], confidence=0.9)
            #     # Loop until we see either the Victory or Defeat screen
            #     while result_value == 'not_found':
            #         timeout += 1
            #         if timeout > 100: # If nothing at 30 seconds start clicking in case battery saver mode is active
            #             if timeout_warned is False:
            #                 logger.info('Possibly stuck, attempting to continue..')
            #                 debug_screen('battle_stuck')
            #                 timeout_warned = True
            #             clickXY(550, 1100) # Second Battle
            #             clickXY(900, 1800) # Start Battle button
            #         if timeout > 200: # Still nothing at 60 seconds? Quit as somethings gone wrong and record the screen for debugging
            #             logger.info('Battle timeout error!')
            #             debug_screen('battle_timeout')
            #             sys.exit(2)
            #         result_value = isVisible_array(['labels/defeat', 'labels/victory'], confidence=0.9)
            #         wait()
            #     timeout = 0 # Reset timer after result found
            #
            #     # Take actions for victory or defeat
            #     if result_value == 'labels/defeat':
            #         globals()['stage_defeats'] += 1
            #         logger.info('Defeat #' + str(globals()['stage_defeats']) + '! Retrying')
            #         clickXY(550, 1800, seconds=3)
            #         blind_push('afkstages', load_formation=False)
            #     elif result_value == 'labels/victory':
            #         globals()['stage_defeats'] = 0
            #         logger.info('First round won!')
            #         clickXY(730, 1800, seconds=3)
            #         blind_push('afkstages', load_formation=False)
            #
            # # Handle second stage or single stage logic
            # if globals()['first_stage_won'] is True:
            #     # Wait for battle to end with either Continue button or Back button
            #     while not isVisible('buttons/continue_stages', region=regions['bottom_buttons']):
            #         timeout += 1
            #         if timeout > 30: # If nothing at 30 seconds start clicking in case battery saver mode is active
            #             click_location('neutral')
            #         if timeout > 60: # Still nothing at 60 seconds? Quit as somethings gone wrong
            #             logger.info('Battle timeout error!')
            #             break
            #         if isVisible('buttons/back', region=regions['bottom_buttons'], seconds=0):
            #             break
            #         wait()
            #     # Continue on second battle is always defeat
            #     if isVisible('buttons/continue_stages', region=regions['bottom_buttons']):
            #         globals()['stage_defeats'] += 1
            #         logger.info('Defeat #' + str(globals()['stage_defeats']) + '! Retrying')
            #         clickXY(730, 1800, seconds=3)
            #         blind_push('afkstages', load_formation=False)
            #     # If we see a Back button we're at the Stage Passed screen (or seriously lost)
            #     if isVisible('buttons/back', region=regions['bottom_buttons']):
            #         globals()['stage_defeats'] = 0 # Reset defeats
            #         globals()['formation'] = 1 # Reset formation
            #         logger.info('Victory! Stage passed\n')
            #         clickXY(750, 1800, seconds=4)
            #         globals()['first_stage_won'] = False
            #         blind_push('afkstages', load_formation=True)
        else:
            logger.info('Something went wrong opening AFK Stages!')
            recover()

def open_afk_stages(afkstages=True):

    # open afk stage screen without prompting loot if it's >1h uncollected
    clickXY(450, 1825, seconds=3)
    click('buttons/afk_stage', region=regions['battle_modes'], seconds=4)

    if afkstages is True: # Standard Stage
        logger.info('Opening AFK Stages')
        logger.info('Changing formations after ' + str(config.getint('PUSHING', 'defeat_limit')) + ' defeats\n')
        # 3 clicks, first can collect loot, second can prompt 'Are you sure?' popup, 3rd opens stages for sure.
        clickXY(715, 1600, seconds=2)  # AFK Stage button
        click('buttons/confirm', suppress=True)
    else: # Talent Stage
        logger.info('Opening Talent Stages')
        logger.info('Changing formations after ' + str(config.getint('PUSHING', 'defeat_limit')) + ' defeats\n')
        clickXY(370, 1600, seconds=2)  # AFK Stage button
        click('buttons/confirm', suppress=True)

def afk_stage_chain_proxy():
    formation_handler()
    click('buttons/battle', retry=1, suppress=True, seconds=0, region=regions['bottom_third'])
    click('buttons/confirm', retry=1, suppress=True, seconds=0)
    while True:
        # Victory Logic
        if isVisible('buttons/next', retry=1, click=True, seconds=3):
            click('buttons/battle', retry=1, suppress=True, seconds=5, region=regions['bottom_third'])
            logger.info('Victory!\n')
            globals()['stage_defeats'] = 0
            formation_handler()
            click('buttons/battle', retry=1, suppress=True, seconds=0, region=regions['bottom_third'])
            click('buttons/confirm', retry=1, suppress=True, seconds=0)
        # Defeat logic
        if isVisible('buttons/retry', retry=1, click=True, seconds=4, region=(650, 1750, 200, 150)):
            # Increment defeats
            globals()['stage_defeats'] += 1
            # If were past the defeat cap handle formation change, else standard log output
            if globals()['stage_defeats'] >= 1 and globals()['stage_defeats'] % config.getint('PUSHING', 'defeat_limit') == 0:
                globals()['formation'] = (globals()['stage_defeats'] / config.getint('PUSHING', 'defeat_limit')) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                logger.info(str(globals()['stage_defeats']) + ' defeats, trying next formation')
                formation_handler(globals()['formation'])
                click('buttons/battle', retry=1, suppress=True, seconds=0)
                click('buttons/confirm', retry=1, suppress=True, seconds=0)
            else:
                logger.info('Defeat #' + str(globals()['stage_defeats']) + '! Retrying')
                click('buttons/battle', suppress=True, seconds=0, region=regions['bottom_third'])
                click('buttons/confirm', suppress=True, seconds=0)

def handle_charms():

    # Handles navigating the charms screen
    def go_back(exit_mode=False):
        click('buttons/confirm', suppress=True)
        click('buttons/back2', suppress=True, region=regions['bottom_buttons'])
        if exit_mode is True:
            click('buttons/back', suppress=True)
            click('buttons/back2', suppress=True)

    # Handle Battles
    def handle_battle(floor_type=''):
        while True:
            click('buttons/battle', retry=1, suppress=True, seconds=0)
            if isVisible('labels/multiple_attempts', seconds=0):
                logger.info('Out of tries!\n')
                click('buttons/confirm')
                if floor_type == 'nightmare': # Exit back to charm row selection screen
                    click('buttons/back', suppress=True, seconds=2)
                    click('buttons/back2', suppress=True, seconds=2)
                else: # Else just exit back to the Dawnrise/Nightmare screen to we can naviate to Nightmare next
                    click('buttons/back', suppress=True, seconds=2)
                break
            click('buttons/confirm', retry=1, suppress=True, seconds=0)
            if isVisible('buttons/retry', retry=1, click=True, seconds=4, region=(650, 1750, 200, 150)):
                # Increment defeats
                globals()['stage_defeats'] += 1
                # If were past the defeat cap handle formation change, else standard log output
                if globals()['stage_defeats'] >= 1 and globals()['stage_defeats'] % config.getint('PUSHING', 'defeat_limit') == 0:
                    globals()['formation'] = (globals()['stage_defeats'] / config.getint('PUSHING',
                                                                                         'defeat_limit')) + 1  # number of defeats / defeat_limit, plus 1 as we start on formation #1
                    logger.info('Defeat #' + str(globals()['stage_defeats']) + ' trying next formation')
                    formation_handler(globals()['formation'])
                else:
                    logger.info('Defeat #' + str(globals()['stage_defeats']) + ' Retrying')
            # Handle different victory screens for Dawnrise/Nightmare
            if floor_type == 'dawnrise':
                if isVisible('buttons/next2', retry=1, click=True, seconds=5):
                    logger.info('Victory!\n')
                    globals()['stage_defeats'] = 0
                    formation_handler()
                if isVisible('buttons/retry2', retry=1, seconds=5):
                    logger.info('Victory! Highest stage cleared!\n')
                    click('buttons/back', suppress=True, seconds=2)
                    break
            elif floor_type == 'nightmare':
                if isVisible('buttons/continue_green', retry=1, click=True, seconds=5, grayscale=False, confidence=0.95): # High confidence so we don't catch the greyscale version
                    logger.info('Victory!\n')
                    globals()['stage_defeats'] = 0
                    formation_handler()
                if isVisible('buttons/continue_green', retry=1, click=True, seconds=5):
                    logger.info('Victory! Highest stage cleared!\n')
                    click('buttons/back', suppress=True, seconds=2)
                    click('buttons/back2', suppress=True, seconds=2)

    top_max_floor = False
    bottom_max_floor = False

    # Open Trials screen
    logger.info('Running Dura\'s Trials!\n')
    wait(1)
    clickXY(450, 1825, seconds=3)
    click('buttons/duras_trials', region=regions['battle_modes'], seconds=3, retry=5)

    # Clear popups
    clickXY(550, 1800, seconds=2)
    clickXY(550, 1800, seconds=2)

    if isVisible('buttons/featured_heroes', retry=5, region=regions['top_third']):

    # TODO Rewrite using regions for the 6 charm stages, to better handle duplicate code for top/bottom row

        # Check top row
        logger.info('Checking top row Charm Trials..')
        globals()['stage_defeats'] = 0
        if isVisible('buttons/rate_up', grayscale=True, click=True, region=(50, 1175, 950, 150), confidence=0.75, seconds=4):

            # Handle top row Dawnrise
            logger.info('Checking Dawnrise')
            clickXY(400, 1800, seconds=7)
            if isVisible('buttons/sweep', seconds=0, retry=2, region=regions['bottom_third']):
                logger.info('Max Dawnrise floor reached!\n')
            else:
                if isVisible('buttons/battle', click=True, seconds=6, region=regions['bottom_third']):
                    logger.info('Dawnrise battle found!\n')
                    formation_handler(globals()['formation'])
                    handle_battle(floor_type='dawnrise')

            # Handle top row Nightmare
            logger.info('Checking Nightmare')
            clickXY(830, 1800, seconds=7)
            if isVisible('buttons/battle', click=True, seconds=6, region=regions['bottom_third']):
                formation_handler(globals()['formation'])
                handle_battle(floor_type='nightmare')
            else:
                logger.info('Max Nightmare floor reached!\n')
                click('buttons/back2', suppress=True, seconds=2)
        else:
            logger.info("Top row not found..")

        # Check bottom row
        logger.info('Checking bottom row Charm Dawnrise Trials..')
        globals()['stage_defeats'] = 0
        globals()['formation'] = 1 # Reset on new levels
        if isVisible('buttons/rate_up', grayscale=True, click=True, region=(50, 1400, 950, 150), confidence=0.75, seconds=3):

            # Handle bottom row Dawnrise
            logger.info('Checking Dawnrise')
            clickXY(400, 1800, seconds=7)
            if isVisible('buttons/sweep', seconds=0, retry=2, region=regions['bottom_third']):
                logger.info('Max Dawnrise floor reached!\n')
            else:
                if isVisible('buttons/battle', click=True, seconds=6, region=regions['bottom_third']):
                    logger.info('Dawnrise battle found!\n')
                    formation_handler(globals()['formation'])
                    handle_battle(floor_type='dawnrise')

            # Handle bottom row Nightmare
            logger.info('Checking Nightmare')
            clickXY(830, 1800, seconds=7)
            if isVisible('buttons/battle', click=True, seconds=6, region=regions['bottom_third']):
                formation_handler(globals()['formation'])
                handle_battle(floor_type='nightmare')
            else:
                logger.info('Max Nightmare floor reached!\n')
                go_back(exit_mode=True)
        else:
            logger.info("Bottom row not found..")
    else:
        logger.info('Something went wrong opening Dura\'s Trials!')
        recover()

    if safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='close'):
        logger.info('Dura\'s Trials ran!\n')


# Scans and pushes the various buttons needed to complete story/side quests
# Very slow, can get stuck if there is a player present at an end point and we get the magnifying glass icon instead of the action icon
# The order of checks and clicks is important to not get stuck in loops
#TODO Get chest icon for collecting quest items / First run teleport prompt
def quest_push():
    logger.info('Pushing Quests!\n')
    # The order of these is important
    buttons = ['buttons/battle', 'buttons/skip', 'buttons/dialogue_option', 'buttons/confirm', 'buttons/red_dialogue', 'buttons/dialogue_coe',
               'buttons/blue_dialogue', 'buttons/interact', 'buttons/dialogue', 'buttons/tap_and_hold', 'buttons/enter', 'buttons/chest',
               'buttons/battle_button', 'labels/questrewards', 'labels/tap_to_close', 'buttons/track', 'labels/coe']

    while True:
        click_array(buttons, suppress=True, confidence=0.91)
        if isVisible('buttons/tap_and_hold', region=regions['chat_window'], seconds=0):
            logger.info('Holding button')
            swipe(550, 1250, 550, 1250, 4000)  # Hacky way to hold it down
        if isVisible('labels/time_change', region=regions['chat_window'], seconds=0, yrelative=620, click=True):
            logger.info('Time changed!')
            wait(4)

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
    handle_charms()

if args['proxy']:
    logger.info('\n')
    logger.info('Starting up Chain Proxy farming\n')
    afk_stage_chain_proxy()

if args['afks']:
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    open_afk_stages(afkstages=True)
    blind_push('afkstages')

if args['afkt']:
    safe_open_and_close(name=inspect.currentframe().f_code.co_name, state='open')
    open_afk_stages(afkstages=False)
    blind_push('afkstages')

# If no function launch argument we pop the UI

options = ["Run Dailies", "Push Towers", "Push AFK Stages", "Push AFK Talent Stages", "Push Dura's Trials", "Run Quests", "Use Dream Realm attempts", "Farm Team-Up Chat", "Farm Chain AFK Proxy Request"]
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
                   7: ["Push Lightbringer Tower", "Push Wilder Tower", "Push Graveborn Tower", "Push Mauler Tower"]}

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
            blind_push('push_tower', 'graveborn')

    if selection == 4:
        day = currenttimeutc.isoweekday()
        if day == 7:
            blind_push('push_tower', 'mauler')

    if selection == 5:
        SelectionMenu.get_selection(options, title='Welcome to AutoAFK2! Select an activity:', subtitle='Note that to stop a task or start a new one you have to restart the bot. Questions? Jc.2 @ Discord')
        selection += 1 # Non-zero index to make things easier to read

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
    handle_charms()

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

if selection == 9:
    logger.info('Starting up Chain Proxy farming')
    logger.info('For this function you need to open the request yourself and start this function at the stage setup screen\n')

    afk_stage_chain_proxy()
