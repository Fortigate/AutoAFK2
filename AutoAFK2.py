import sys

from tools import *
import argparse
from humanfriendly import format_timespan
import logging

version = '0.0.7'
parser = argparse.ArgumentParser()
parser.add_argument("-t", "--teamup", action = 'store_true', help = "Run the Team-up function")
parser.add_argument("-d", "--dailies", action = 'store_true', help = "Run the Dailies function")
parser.add_argument("-c", "--config", metavar="CONFIG", default = "settings.ini", help = "Define alternative settings file to load")
args = vars(parser.parse_args())

global last_synergy
last_synergy = time.time()
global last_corrupt
last_corrupt = time.time()

if args['config']:
    settings = os.path.join(cwd, args['config'])
else:
    settings = os.path.join(cwd, 'settings.ini')
config.read(settings)

if settings == 'settings.ini':
    logname = 'autoafk2.log'
else:
    logname = settings.split('.')[0] + '.log'

logging.StreamHandler(stream=sys.stderr)

# File handler
file_log_handler = logging.FileHandler(filename=logname)
logger.addHandler(file_log_handler)
formatter = logging.Formatter('%(asctime)s %(message)s')
file_log_handler.setFormatter(formatter)

logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

logger = logging.getLogger('autoafk2')

logger.info('\nLoaded settings file: ' + str(settings.split('\\')[-1]))
logger.info('Version: ' + version)

connect_and_launch(port=config.get('ADVANCED', 'port'))
waitUntilGameActive()

#TODO
# Settings.ini for everything
# Dream Realm collection and single run
# All heroes Affinity clicking
# Travelogue collection

def dailies():
    if config.getboolean('ACTIVITIES', 'claim_afk'):
        claim_afk_rewards()
    if config.getboolean('ACTIVITIES', 'friend_points'):
        friend_points_collect()
    if config.getboolean('ACTIVITIES', 'mail_collect'):
        mail_connect()
    if config.getboolean('ACTIVITIES', 'emporium_purchases'):
        emporium_purchases()
    if config.getint('ACTIVITIES', 'arena_battles') > 0:
        arena(config.getint('ACTIVITIES', 'arena_battles'))
    if config.getboolean('ACTIVITIES', 'dream_realm'):
        dream_realm()
    if config.getboolean('ACTIVITIES', 'claim_afk'):
        claim_afk_rewards()
    if config.getboolean('ACTIVITIES', 'collect_quests'):
        quests()
    logger.info('Dailies done!')

def teamup():
    while 1 == 1:
        team_up()

def team_up():
    timer = 0
    start = time.time()
    while 1 == 1:
        while not isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
            click('buttons/back', suppress=True)
            click_location('neutral')
            wait()
        logger.info('Opening chat')
        while not isVisible('teamup/join', seconds=1, confidence=0.8):
            click('teamup/chat', seconds=0, suppress=True)
            click('teamup/teamup', seconds=0, suppress=True)
            if isVisible('teamup/join', seconds=1):
                # Prioritise Corrupt Creatures over Synergy battles
                continue
            if isVisible('teamup/synergy', seconds=0): # So we don't open the same one twice in a row
                # logger.info(str(format_timespan(time.time() - globals()['last_synergy'])) + ' since last synergy')
                x, y = returnxy('teamup/synergy')
                if return_pixel_colour(x, y + 220, 2, seconds=0) < 200 and (time.time() - globals()['last_synergy'] > 300):
                    logger.info('Synergy Battle found!')
                    clickXY(x, y + 220)
                    if isVisible('buttons/back'):
                        clickXY(300, 900)
                        clickXY(650, 1800)
                        click('buttons/back', suppress=True)
                        logger.info('Hero lent\n')
                        globals()['last_synergy'] = time.time()
                        return
                    else:
                        logger.info('Something went wrong, returning\n')
                        globals()['last_synergy'] = time.time()
                        return
        duration = time.time() - start
        logger.info('Corrupt Creature found in ' + format_timespan(round(duration)) + '!')
        # logger.info(str(format_timespan(time.time() - globals()['last_corrupt'])) + ' since last corrupt')
        click('teamup/join', seconds=5)
        if not isVisible('teamup/ready'):
            logger.info('Something went wrong, waiting 30s before continuing\n')
            wait(30)
            return
        click('teamup/ready', seconds=6)
        # logger.info('Readying up in the lobby')
        while isVisible('teamup/quit', confidence=0.8):
            timer += 1
            if timer > 15:
                logger.info('Timeout error!\n')
                click('teamup/quit', seconds=2)
                clickXY(850, 1250, seconds=4)
                return
        while isVisible('teamup/ready_lobby', confidence=0.8):
            logger.info('Deploying heroes')
            clickXY(120, 1300)
            clickXY(270, 1300)
            clickXY(450, 1300)
            click('teamup/ready_lobby')
        while not isVisible('labels/tap_to_close', confidence=0.8):
            timer += 1
            if timer > 20:
                logger.info('Timeout error!\n')
                click_location('neutral')
                return
        click('labels/tap_to_close', confidence=0.8)
        timer = 0
        logger.info('Battle complete!\n')
        globals()['last_corrupt'] = time.time()
        wait(3)
        return
    team_up()



def claim_afk_rewards():
    logger.info('Claiming AFK Rewards')
    clickXY(100, 1800, seconds=4)  # Open AFK Rewards
    clickXY(550, 1400)  # Click Chest
    clickXY(550, 1080)  # Click Collect
    # Double FR
    clickXY(100, 1800)  # Close
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')

def claim_afk_rewards():
    logger.info('Claiming AFK Rewards')
    clickXY(100, 1800, seconds=4)  # Open AFK Rewards
    clickXY(550, 1400)  # Click Chest
    clickXY(550, 1080)  # Click Collect
    # Double FR
    clickXY(100, 1800)  # Close
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')

def friend_points_collect():
    logger.info('Claiming friend gifts')
    click('buttons/main_menu', region=(900, 1750, 150, 150))
    click('buttons/friends', region=(30, 1450, 200, 200), seconds=2)
    clickXY(700, 1800, seconds=2)
    clickXY(850, 300, seconds=2)
    clickXY(420, 50, seconds=2)  # Neutral location for closing reward pop ups etc, should never be an in game button here
    click('buttons/back', region=(50, 1750, 150, 150))
    click('buttons/back', region=(50, 1750, 150, 150))
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')

def mail_connect():
    logger.info('Claiming Mail')
    click('buttons/main_menu', region=(900, 1750, 150, 150))
    click('buttons/mail', region=(240, 1250, 200, 200), seconds=2)
    clickXY(750, 1800, seconds=2)
    clickXY(750, 1800, seconds=2)
    click('buttons/back', region=(50, 1750, 150, 150))
    click('buttons/back', region=(50, 1750, 150, 150))
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')

def emporium_purchases():
    logger.info('Purchasing daily shop bits')
    click('buttons/main_menu', region=(900, 1750, 150, 150))
    click('buttons/emporium', region=(850, 1250, 200, 200), seconds=2)
    clickXY(100, 700, seconds=2) # guild store
    clickXY(325, 900, seconds=2) # daily card
    clickXY(650, 1800, seconds=2)  # purchase
    clickXY(875, 1250, seconds=2)  # diamonds confirm
    click_location('neutral')
    click('buttons/back2', region=(50, 1750, 150, 150))
    click('buttons/back', region=(50, 1750, 150, 150))
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')

def arena(battles=9):
    if battles == 0:
        logger.info('No Battles configured, skipping')
        return
    counter = 0
    logger.info('Battling Arena')
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
        click('buttons/back', region=(50, 1750, 150, 150), seconds=2)
        click('buttons/back2', region=(50, 1750, 150, 150))
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')
        save_screenshot('something_went_wrong')

def dream_realm():
    clickXY(450, 1825)
    if isVisible('labels/battle_modes'):
        click('buttons/dream_realm', seconds=2)
        clickXY(1020, 280)
        clickXY(1020, 280)
        clickXY(550, 1800)
        click('buttons/back')
        clickXY(550, 1800, seconds=4) # Battle
        clickXY(550, 1800) # Battle begin from hero selection
        while not isVisible('labels/tap_to_close'):
            click('labels/tap_to_close', seconds=3, suppress=True)
            clickXY(100, 1800)
        logger.info('battle compelte!')
        click('buttons/back')
        click('buttons/back2')

def quests():
    logger.info('Collecting quests')
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

    click('buttons/back2', confidence=0.8, region=(40, 1750, 150, 150), seconds=2)
    click('buttons/back', region=(50, 1750, 150, 150), seconds=2)
    click('buttons/back2', confidence=0.8, region=(40, 1750, 150, 150), seconds=2)

    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return
    else:
        logger.info('Something went wrong')
        save_screenshot('something_went_wrong')


if args['dailies']:
    logger.info('Running dailies\n')
    dailies()

if args['teamup']:
    logger.info('Starting up team-up farming\n')
    teamup()
