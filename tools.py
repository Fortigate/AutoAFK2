import os
import configparser
import time
import io
import scrcpy
import numpy as np
import logging
import sys
from pyscreeze import locate, locateAll
from PIL import Image
from subprocess import Popen, PIPE
from ppadb.client import Client
from datetime import datetime

logger = logging.getLogger('autoafk2')
cwd = os.path.dirname(__file__)  # variable for current directory of AutoAFK.exe
config = configparser.ConfigParser()
adb = Client(host="127.0.0.1", port=5037)
global device
global connect_attempts
connect_attempts = 0

def connect_and_launch(port, server):
    global device
    global connect_attempts

    if not get_connected_device():
        device = adb.device(get_adb_device(port))
    else:
        device = get_connected_device()

    # After getting device run a test echo command to make sure the device is active and catch any errors
    try:
        device.shell('test')
    except Exception as e:
        logger.info('Connection error:')
        logger.info(e)
        while connect_attempts < 3:
            connect_attempts += 1
            logger.info('Retrying ' + str(connect_attempts) + '/3')
            wait(5)
            connect_and_launch(port) # Careful here as we run concurrent connect_and_launch() which can lead to multiple sessions running at once
        if connect_attempts >= 3:
            logger.info('ADB connection error!')
            sys.exit(2)

    # Get scrcpy running, catch errors again
    try:
        scrcpyClient = scrcpy.Client(device=device.serial)
        scrcpyClient.max_fps = 5
        scrcpyClient.bitrate = 16000000
        scrcpyClient.start(daemon_threaded=True)
        setattr(device, 'srccpy', scrcpyClient)
    except Exception as e:
        logger.info('Error starting scrcpy!')
    finally:
        logger.info('Device ' + str(device.serial) + " connected successfully")

    # Sometimes the game crashes when launching so we make sure its been running for 5 seconds before continuing
    device.shell('monkey -p ' + server + ' 1')
    wait(5) # This long wait doesn't slow anything down as the game takes 60 seconds to load anyway
    while device.shell('pidof ' + server) == '':
        device.shell('monkey -p ' + server + ' 1')
        wait(5) # This long wait doesn't slow anything down as the game takes 60 seconds to load anyway

def get_adb_device(port):
    adbpath = os.path.join(cwd, 'adb.exe')  # Locate adb.exe in working directory
    if len(adb.devices()) > 0:
        for active_devices in adb.devices():
            if active_devices.serial[0] == 'e': # If it starts with 'e' (basically 'emulator-####')
                return active_devices.serial
    elif len(adb.devices()) < 1: # Else manually connect using port
        device_name = '127.0.0.1:' + port
        Popen([adbpath, 'connect', device_name], stdout=PIPE).communicate()[0]
        return device_name

# Confirms that the game has loaded by checking for the sunandstars icon next to the minimap. We press a few buttons to navigate back if needed
def waitUntilGameActive():
    logger.info('Searching for main map screen..')
    loadingcounter = 0
    timeoutcounter = 0
    loaded = 1

    while loadingcounter <= loaded:
        if isVisible('labels/sunandstars', seconds=0,  region=(770, 40, 100, 100)):
            break
        clickXY(420, 50, seconds=0)  # Neutral location for closing reward pop ups etc, should never be an in game button here
        click('buttons/back', seconds=0, suppress=True, region=(50, 1750, 150, 150))
        click('buttons/back2', seconds=0,  suppress=True, region=(50, 1750, 150, 150))
        click('buttons/claim', seconds=0,  suppress=True) # Claim Esperia monthly so it doesnt block the view
        timeoutcounter += 1
        if timeoutcounter > 30:  # This is nearly 4 minutes currently
            logger.info('Timed out while loading!')
            save_screenshot('loading_timeout')
            sys.exit()
    logger.info('Game Loaded!\n')

def resolutionCheck():
    resolution_lines = device.shell('wm size').split('\n')
    physical_resolution = resolution_lines[0].split(' ')
    override_resolution = resolution_lines[1].split(' ')

    if override_resolution[0] != '':
        if not str(override_resolution[2]).strip() == '1920x1080' and not str(
                override_resolution[2]).strip() == '1080x1920':
            logger.info('Unsupported Override Resolution! (' + str(override_resolution[2]).strip() + '). Please change your resolution to 1920x1080')
            logger.info('We will try and scale the image but non-16:9 formats will likely have issues with image detection')
    else:
        if not str(physical_resolution[2]).strip() == '1920x1080' and not str(
                physical_resolution[2]).strip() == '1080x1920':
            logger.info('Unsupported Physical Resolution! (' + str(physical_resolution[2]).strip() + '). Please change your resolution to 1920x1080')
            logger.info('We will try and scale the image but non-16:9 formats will likely have issues with image detection')

# Clicks on the given XY coordinates
def clickXY(x, y, seconds=1):
    device.input_tap(x, y)
    wait(seconds)

# Back button/neutral location etc can be called by name to make it a bit cleaner
def click_location(location, seconds=1):
    locations = {
        'neutral': (420, 5)
    }

    clickXY(locations[location][0], locations[location][1])
    wait(seconds)

def returnxy(image, confidence=0.9, grayscale=False, region=(0, 0, 1080, 1920)):
    screenshot = getFrame()

    search = Image.open(os.path.join(cwd, 'img', image + '.png'))
    result = locate(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)

    if result != None:
        x, y, w, h = result
        return x, y
    else:
        return 0, 0 # Prevents NoneType errors when unpacking if we don't find it


# Wait command, default 1 second
# Loading multiplier is defined in settings, it is a decimally notated % multiplier. E.G:
# 0.9 will run with 90% of the default wait times
# 2.0 will run with 200% of the default wait times
# This is handy for slower machines where we need to wait for sections/images to load
def wait(seconds=1):
    time.sleep(seconds * config.getfloat('ADVANCED', 'loading_multiplier'))

# If the given image is found, it will click on the center of it, if not returns "No image found"
# Confidence is how sure we are we have the right image, for animated icons we can lower the value
# Seconds is time to wait after clicking the image
# Retry will try and find the image x number of times, useful for animated or covered buttons, or to make sure the button is not skipped
# Suppress will disable warnings, sometimes we don't need to know if a button isn't found
def click(image, confidence=0.9, seconds=1, retry=3, suppress=False, grayscale=False, region=(0, 0, 1080, 1920)):
    counter = 0

    screenshot = getFrame()
    search = Image.open(os.path.join(cwd, 'img', image + '.png'))
    result = locate(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)

    if result == None and retry != 1:
        while counter < retry:
            screenshot = getFrame()
            result = locate(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)
            if result != None:
                x, y, w, h = result
                x_center = round(x + w / 2)
                y_center = round(y + h / 2)
                device.input_tap(x_center, y_center)
                wait(seconds)
                return
            if suppress is not True:
                logger.info('Retrying ' + image + ' search: ' + str(counter+1) + '/' + str(retry))
            counter = counter + 1
            wait(1)
    elif result != None:
        x, y, w, h = result
        x_center = round(x + w/2)
        y_center = round(y + h/2)
        device.input_tap(x_center, y_center)
        wait(seconds)
    else:
        if suppress is not True:
            logger.info('Image:' + image + ' not found!')
        wait(seconds)

# Pyscreeze's locate() searchs top down, sometimes we want to click the last found image (I.E the latest join button in chat)
def click_last(image, confidence=0.9, seconds=1, retry=3, suppress=False, grayscale=False, region=(0, 0, 1080, 1920)):
    counter = 0
    screenshot = getFrame()

    search = Image.open(os.path.join(cwd, 'img', image + '.png'))
    result = locateAll(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)
    if result is None and retry != 1:
        while counter < retry:
            screenshot = getFrame()
            result = locate(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)
            if result is not None:
                x, y, w, h = result
                x_center = round(x + w / 2)
                y_center = round(y + h / 2)
                device.input_tap(x_center, y_center)
                wait(seconds)
                return
            if suppress is not True:
                logger.info('Retrying ' + image + ' search: ' + str(counter+1) + '/' + str(retry))
            counter = counter + 1
            wait(1)
    elif result is not None:
        list_results = list(result)
        if len(list_results) > 1:
            x, y, w, h = list_results[-1]
            x_center = round(x + w/2)
            y_center = round(y + h/2)
            device.input_tap(x_center, y_center)
            wait(seconds)
        else:
            logger.info('click_last error!')
    else:
        if suppress is not True:
            logger.info('Image:' + image + ' not found!')
        wait(seconds)

def click_array(images, confidence=0.9, seconds=1, suppress=False, grayscale=False, region=(0, 0, 1080, 1920)):
    counter = 0
    screenshot = getFrame()

    for image in images:
        search = Image.open(os.path.join(cwd, 'img', image + '.png'))
        result = locate(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)
        if result is not None:
            logger.info(image + ' clicked!')
            x, y, w, h = result
            x_center = round(x + w/2)
            y_center = round(y + h/2)
            device.input_tap(x_center, y_center)
            wait(seconds)
        else:
            if suppress is not True:
                logger.info('Image:' + image + ' not found!')
            # wait(seconds)


# Performs a swipe from X1/Y1 to X2/Y2 at the speed defined in duration (in milliseconds)
def swipe(x1, y1, x2, y2, duration=100, seconds=1):
    device.input_swipe(x1, y1, x2, y2, duration)
    wait(seconds)

# Returns True if the image is found, False if not
# Confidence value can be reduced for images with animations
# Retry for retrying image search
def isVisible(image, confidence=0.9, seconds=1, retry=3, click=False, region=(0, 0, 1080, 1920), xrelative=0, yrelative=0, grayscale=False):
    counter = 0
    screenshot = getFrame()
    search = Image.open(os.path.join(cwd, 'img', image + '.png'))
    res = locate(search, screenshot, grayscale=False, confidence=confidence, region=region)

    if res == None and retry != 1:
        while counter < retry:
            screenshot = getFrame()
            res = locate(search, screenshot, grayscale=grayscale, confidence=confidence, region=region)
            if res != None:
                if click is True:
                    x, y, w, h = res
                    x_center = round(x + w / 2) + xrelative
                    y_center = round(y + h / 2) + yrelative
                    device.input_tap(x_center, y_center)
                wait(seconds)
                return True
            wait()
            counter = counter + 1
    elif res != None:
        if click is True:
            x, y, w, h = res
            x_center = round((x + xrelative) + w / 2) 
            y_center = round((y + yrelative) + h / 2)
            device.input_tap(x_center, y_center)
        wait(seconds)
        return True
    else:
        # wait(seconds) # Speed up the bot by not waiting when image not found
        return False

# Returns the last frame from scrcpy, if the resolution isn't 1080 we scale it but this will only work in 16:9 resolutions
def getFrame():
    im = Image.fromarray(device.srccpy.last_frame[:, :, ::-1])

    if not im.size == (1080, 1920) and not im.size == (1920, 1080):
        im = im.resize((1080, 1920))

    return im

# Saves screenshot locally
def save_screenshot(name):
    image = getFrame()
    # Convert image back to bytearray
    byteIO = io.BytesIO()
    image.save(byteIO, format='PNG')
    image = byteIO.getvalue()
    with open(name + '.png', 'wb') as f:
        f.write(image)

def return_pixel_colour(x, y, c, seconds=1):
    im = getFrame()
    screenshot = np.asarray(im) # Make it an array

    wait(seconds)
    return screenshot[y, x, c]

def recover(count=3):
    timer = 0
    if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
        return True
    while timer < count:
        click('buttons/back', suppress=True)
        click('buttons/back2', suppress=True)
        click_location('neutral')
        timer += 1
        if timer > count:
            timestamp = datetime.now().strftime('%d-%m-%y_%H-%M-%S')
            save_screenshot('recovery_timeout_' + timestamp)
            return False
            sys.exit()
        if isVisible('labels/sunandstars', region=(770, 40, 100, 100)):
            return True

# We call this at the start and end of every activity to make sure we are back at the main map screen, if not we are lost and exit
def safe_open_and_close(name, state):
    if state == 'open':
        logger.debug('opening task ' + name)
        if recover() is True:
            logger.debug(name + ' opened successfully!')
        else:
            logger.info('Issue opening ' + name)

    if state == 'close':
        if recover() is True:
            logger.debug(name + ' completed successfully!')
            return True
        else:
            timestamp = datetime.now().strftime('%d-%m-%y_%H-%M-%S')
            save_screenshot(name + '_close_error_' + timestamp)
            logger.info('Issue closing ' + name + '.')

# Checks if there is already adb connection active so it doesnt kill it and start again (when executing this from AutoAFK)
def get_connected_device():
    adbpath = os.path.join(cwd, 'adb.exe')  # Locate adb.exe in working directory
    try: 
        devices = adb.devices()
        if devices:
            return devices[0]
    except:
        Popen([adbpath, "kill-server"], stderr=PIPE).communicate()[0]
        Popen([adbpath, "start-server"], stderr=PIPE).communicate()[0]
        wait(2)
        return None

