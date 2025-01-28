"""Emulator Interactions Module."""

import io
import numpy as np
import os
import sys
from configparser import ConfigParser
from datetime import datetime
from logging import Logger
from PIL import Image
from pyscreeze import Box, locate, locateAll
from typing import (
    Any,
    Literal,
    Union,  # TODO: Update Python. Union required for Python <3.10
)

from client.emulator_client import EmulatorClient


class EmulatorInteractions(EmulatorClient):
    """Emulator Interactions Class."""

    def __init__(self, config: ConfigParser, logger: Logger) -> None:
        """Initialize the interactions.

        Args:
            config (ConfigParser): Configurations from settings.ini.
            logger (Logger): Logger.
        """
        super().__init__(config, logger)

    def wait_until_game_active(self) -> None:
        """
        Confirms that the game has loaded by checking for the 'Guild' text.
        We press a few buttons to navigate back if needed.
        """
        self.logger.info("Waiting for game to load..")
        timeoutcounter = 0

        while True:
            if self.is_visible(
                "labels/guild", seconds=0, region=(730, 1880, 80, 25), confidence=0.8
            ):
                self.logger.info("Game Loaded!\n")
                break
            self.click_xy(
                420, 50, seconds=1
            )  # Neutral location for closing reward pop ups etc, should never be an in game button here
            buttons = ["buttons/back", "buttons/back2", "buttons/claim"]
            self.click_array(buttons, suppress=True, delay=1)
            timeoutcounter += 1
            if timeoutcounter > 15:  # This is nearly 4 minutes currently
                self.logger.info(
                    "Timed out while loading! Guild button was not found so if everything looks good please check in game language is set to English."
                )
                self.save_screenshot("loading_timeout")
                sys.exit()

    def resolution_check(self) -> None:
        """
        Verify emulator resolution
        TODO: Add support for variable resolution
        """
        resolution_lines = self.device.shell("wm size").split("\n")
        physical_resolution = resolution_lines[0].split(" ")
        override_resolution = resolution_lines[1].split(" ")

        if override_resolution[0] != "":
            if (
                not str(override_resolution[2]).strip() == "1920x1080"
                and not str(override_resolution[2]).strip() == "1080x1920"
            ):
                self.logger.info(
                    "Unsupported Override Resolution! ("
                    + str(override_resolution[2]).strip()
                    + "). Please change your resolution to 1920x1080"
                )
                self.logger.info(
                    "We will try and scale the image but non-16:9 formats will likely have issues with image detection"
                )
        else:
            if (
                not str(physical_resolution[2]).strip() == "1920x1080"
                and not str(physical_resolution[2]).strip() == "1080x1920"
            ):
                self.logger.info(
                    "Unsupported Physical Resolution! ("
                    + str(physical_resolution[2]).strip()
                    + "). Please change your resolution to 1920x1080"
                )
                self.logger.info(
                    "We will try and scale the image but non-16:9 formats will likely have issues with image detection"
                )

        # This will throw an execption if we are in Landscape mode as it'll exceed the screen dimensions using the region
        try:
            self.is_visible(
                "labels/guild", seconds=0, retry=1, region=(730, 1880, 80, 25)
            )
        except Exception as e:
            self.logger.info(e)
            self.logger.info(
                "Guild button out of range, this is usually because we are in Landscape mode, only Portrait is supported! Please switch and restart the bot"
            )
            self.wait(15)
            sys.exit(2)

    def click_xy(self, x: int, y: int, seconds: int = 1) -> None:
        """Clicks at specific X, Y coordinates.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            seconds (int, optional): Wait time. Defaults to 1.
        """
        self.device.input_tap(x, y)
        self.wait(seconds)

    def click_location(self, location: str, seconds: int = 1) -> None:
        """Click a predetermined location.

        Args:
            location (str): Predetermined location.
            seconds (int, optional): Wait time. Defaults to 1.
        """
        locations: dict[str, tuple[int, int]] = {"neutral": (420, 5)}

        self.click_xy(locations[location][0], locations[location][1])
        self.wait(seconds)

    def return_xy(
        self,
        image: str,
        confidence: float = 0.9,
        grayscale: bool = False,
        region: tuple[int, int, int, int] = (0, 0, 1080, 1920),
    ) -> Union[tuple[int, int], tuple[Literal[0], Literal[0]]]:
        """Return X, Y coordinates of image.

        Args:
            image (str): Path to image to search.
            confidence (float, optional): Pyscreeze locate confidence. Defaults to 0.9.
            grayscale (bool, optional): Pyscreeze locate grayscale. Defaults to False.
            region (tuple[int, int, int, int], optional): Search region. Defaults to (0, 0, 1080, 1920).

        Returns:
            tuple[int, int] | tuple[Literal[0], Literal[0]]: X, Y coordinates.
        """
        screenshot: Image.Image = self.get_frame()
        search: Image.Image = Image.open(os.path.join(self.cwd, "img", image + ".png"))
        result: Box | None = locate(
            search,
            screenshot,
            grayscale=grayscale,
            confidence=confidence,
            region=region,
        )

        if result is not None:
            x, y, w, h = result
            return x, y
        else:
            return 0, 0  # Prevents NoneType errors when unpacking if we don't find it

    def click(
        self,
        image: str,
        confidence: float = 0.9,
        seconds: int = 1,
        retry: int = 3,
        suppress: bool = False,
        grayscale: bool = False,
        region: tuple[int, int, int, int] = (0, 0, 1080, 1920),
    ) -> None:
        """Perform a click on an image.

        Args:
            image (str): Path to image to search.
            confidence (float, optional): Pyscreeze locate confidence. Defaults to 0.9.
            seconds (int, optional): Wait time. Defaults to 1.
            retry (int, optional): Retry attempts. Defaults to 3.
            suppress (bool, optional): Suppress logging messages. Defaults to False.
            grayscale (bool, optional): Pyscreeze locate grayscale. Defaults to False.
            region (tuple[int, int, int, int], optional): Search region. Defaults to (0, 0, 1080, 1920).
        """
        counter: int = 0
        screenshot: Image.Image = self.get_frame()
        search: Image.Image = Image.open(os.path.join(self.cwd, "img", image + ".png"))
        result: Box | None = locate(
            search,
            screenshot,
            grayscale=grayscale,
            confidence=confidence,
            region=region,
        )

        if result is None and retry != 1:
            while counter < retry:
                screenshot = self.get_frame()
                result = locate(
                    search,
                    screenshot,
                    grayscale=grayscale,
                    confidence=confidence,
                    region=region,
                )
                if result is not None:
                    x, y, w, h = result
                    x_center: int = round(x + w / 2)
                    y_center: int = round(y + h / 2)
                    self.device.input_tap(x_center, y_center)
                    self.wait(seconds)
                    return
                if suppress is not True:
                    self.logger.info(
                        "Retrying "
                        + image
                        + " search: "
                        + str(counter + 1)
                        + "/"
                        + str(retry)
                    )
                counter = counter + 1
                self.wait(1)
        elif result is not None:
            x, y, w, h = result
            x_center = round(x + w / 2)
            y_center = round(y + h / 2)
            self.device.input_tap(x_center, y_center)
            self.wait(seconds)
        else:
            if suppress is not True:
                self.logger.info("Image:" + image + " not found!")
            self.wait(seconds)

    def click_last(
        self,
        image: str,
        confidence: float = 0.9,
        seconds: int = 1,
        retry: int = 3,
        suppress: bool = False,
        grayscale: bool = False,
        region: tuple[int, int, int, int] = (0, 0, 1080, 1920),
    ) -> None:
        """Pyscreeze's locate() searchs top down, sometimes we want to click the last found image (i.e. the latest join button in chat).

        Args:
            image (str): Path to image to search.
            confidence (float, optional): Pyscreeze locate confidence. Defaults to 0.9.
            seconds (int, optional): Wait time. Defaults to 1.
            retry (int, optional): Retry attempts. Defaults to 3.
            suppress (bool, optional): Suppress logging messages. Defaults to False.
            grayscale (bool, optional): Pyscreeze locate grayscale. Defaults to False.
            region (tuple[int, int, int, int], optional): Search region. Defaults to (0, 0, 1080, 1920).
        """
        counter: int = 0
        screenshot: Image.Image = self.get_frame()
        search: Image.Image = Image.open(os.path.join(self.cwd, "img", image + ".png"))
        result: np.Generator[Box, None, None] = locateAll(
            search,
            screenshot,
            grayscale=grayscale,
            confidence=confidence,
            region=region,
        )

        if result is None and retry != 1:
            while counter < retry:
                screenshot = self.get_frame()
                result = locate(
                    search,
                    screenshot,
                    grayscale=grayscale,
                    confidence=confidence,
                    region=region,
                )
                if result is not None:
                    x, y, w, h = result
                    x_center = round(x + w / 2)
                    y_center = round(y + h / 2)
                    self.device.input_tap(x_center, y_center)
                    self.wait(seconds)
                    return
                if suppress is not True:
                    self.logger.info(
                        "Retrying "
                        + image
                        + " search: "
                        + str(counter + 1)
                        + "/"
                        + str(retry)
                    )
                counter = counter + 1
                self.wait(1)
        elif result is not None:
            list_results = list(result)
            if len(list_results) > 1:
                x, y, w, h = list_results[-1]
                x_center = round(x + w / 2)
                y_center = round(y + h / 2)
                self.device.input_tap(x_center, y_center)
                self.wait(seconds)
            else:
                self.logger.info("click_last error!")
        else:
            if suppress is not True:
                self.logger.info("Image:" + image + " not found!")
            self.wait(seconds)

    def click_array(
        self,
        images: list[str],
        confidence: float = 0.9,
        seconds: int = 1,
        suppress: bool = False,
        grayscale: bool = False,
        region: tuple[int, int, int, int] = (0, 0, 1080, 1920),
        delay: int = 0,
    ) -> None:
        """Clicks an array of images.

        Args:
            images (list[str]): Paths to images to search.
            confidence (float, optional): Pyscreeze locate confidence. Defaults to 0.9.
            seconds (int, optional): Wait time. Defaults to 1.
            suppress (bool, optional): Suppress logging messages. Defaults to False.
            grayscale (bool, optional): Pyscreeze locate grayscale. Defaults to False.
            region (tuple[int, int, int, int], optional): Search region. Defaults to (0, 0, 1080, 1920).
            delay (int, optional): Pause between images else we try and click multiple at once. Defaults to 0.
        """
        screenshot: Image.Image = self.get_frame()

        for image in images:
            search: Image.Image = Image.open(
                os.path.join(self.cwd, "img", image + ".png")
            )
            result: Box | None = locate(
                search,
                screenshot,
                grayscale=grayscale,
                confidence=confidence,
                region=region,
            )

            if result is not None:
                if suppress is not False:
                    self.logger.info(image + " clicked!")
                x, y, w, h = result
                x_center: int = round(x + w / 2)
                y_center: int = round(y + h / 2)
                self.device.input_tap(x_center, y_center)
                self.wait(seconds)
                return
            else:
                if suppress is not True:
                    self.logger.info("Image:" + image + " not found!")
            self.wait(delay)

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration: int = 100, seconds: int = 1
    ) -> None:
        """Performs a swipe from X1/Y1 to X2/Y2 at the speed defined in duration (in milliseconds).

        Args:
            x1 (int): Initial X coordinate.
            y1 (int): Initial Y coordinate.
            x2 (int): End X coordinate.
            y2 (int): end Y coordinate.
            duration (int, optional): Swipe duration in milliseconds. Defaults to 100.
            seconds (int, optional): Wait time. Defaults to 1.
        """
        self.device.input_swipe(x1, y1, x2, y2, duration)
        self.wait(seconds)

    def is_visible(
        self,
        image: str,
        confidence: float = 0.9,
        seconds: int = 1,
        retry: int = 3,
        click: bool = False,
        region: tuple[int, int, int, int] = (0, 0, 1080, 1920),
        x_relative: int = 0,
        y_relative: int = 0,
        grayscale: bool = False,
    ) -> Union[None, bool]:
        """Attempt to locate an image.

        Args:
            image (str): Path to image to search.
            confidence (float, optional): Pyscreeze locate confidence. Defaults to 0.9.
            seconds (int, optional): Wait time. Defaults to 1.
            retry (int, optional): Retry attempts. Defaults to 3.
            click (bool, optional): Click the image. Defaults to False.
            region (tuple[int, int, int, int], optional): Search region. Defaults to (0, 0, 1080, 1920).
            x_relative (int, optional): X coordinate relative to resolution. Defaults to 0.
            y_relative (int, optional): Y coordinate relative to resolution. Defaults to 0.
            grayscale (bool, optional): Pyscreeze locate grayscale. Defaults to False.

        Returns:
            None | bool: Returns True if the image is found, False if not.
        """
        counter: int = 0
        screenshot: Image.Image = self.get_frame()
        search: Image.Image = Image.open(os.path.join(self.cwd, "img", image + ".png"))
        res: Box | None = locate(
            search, screenshot, grayscale=False, confidence=confidence, region=region
        )

        if res is None and retry != 1:
            while counter < retry:
                screenshot = self.get_frame()
                res = locate(
                    search,
                    screenshot,
                    grayscale=grayscale,
                    confidence=confidence,
                    region=region,
                )
                if res is not None:
                    if click is True:
                        x, y, w, h = res
                        x_center: int = round(x + w / 2) + x_relative
                        y_center: int = round(y + h / 2) + y_relative
                        self.device.input_tap(x_center, y_center)
                    self.wait(seconds)
                    return True
                self.wait()
                counter = counter + 1
        elif res is not None:
            if click is True:
                x, y, w, h = res
                x_center = round((x + x_relative) + w / 2)
                y_center = round((y + y_relative) + h / 2)
                self.device.input_tap(x_center, y_center)
            self.wait(seconds)
            return True
        else:
            return False

    def is_visible_array(
        self,
        images: list[str],
        confidence: float = 0.9,
        seconds: int = 1,
        retry: int = 3,
        click: bool = False,
        region: tuple[int, int, int, int] = (0, 0, 1080, 1920),
        x_relative: int = 0,
        y_relative: int = 0,
        grayscale: bool = False,
    ) -> Union[Any, Literal["not_found"]]:
        """Takes a array of images as input, and returns the first found image from the array. If none are found returns 'not_found'
        Useful for scanning for multiple images in one screenshot rather than making multiple is_visible calls.

        Args:
            images (list[str]): Paths to images to search.
            confidence (float, optional): Pyscreeze locate confidence. Defaults to 0.9.
            seconds (int, optional): Wait time. Defaults to 1.
            retry (int, optional): Retry attempts. Defaults to 3.
            click (bool, optional): Click the image. Defaults to False.
            region (tuple[int, int, int, int], optional): Search region. Defaults to (0, 0, 1080, 1920).
            x_relative (int, optional): X coordinate relative to resolution. Defaults to 0.
            y_relative (int, optional): Y coordinate relative to resolution. Defaults to 0.
            grayscale (bool, optional): Pyscreeze locate grayscale. Defaults to False.

        Returns:
            Any | Literal["not_found"]: First found image from the array or 'not_found'.
        """
        screenshot: Image.Image = self.get_frame()

        for image in images:
            search: Image.Image = Image.open(
                os.path.join(self.cwd, "img", image + ".png")
            )
            res: Box | None = locate(
                search,
                screenshot,
                grayscale=False,
                confidence=confidence,
                region=region,
            )
            if res is not None:
                if click is True:
                    x, y, w, h = res
                    x_center = round(x + w / 2) + x_relative
                    y_center = round(y + h / 2) + y_relative
                    self.device.input_tap(x_center, y_center)
                self.wait(seconds)
                return image
        # If nothing found return false
        return "not_found"

    def get_frame(self) -> Image.Image:
        """Returns the last frame from scrcpy, if the resolution isn't 1080 we scale it but this will only work in 16:9 resolutions.

        Returns:
            Image.Image: Last frame from scrcpy.
        """
        im: Image.Image = Image.fromarray(self.device.srccpy.last_frame[:, :, ::-1])

        if not im.size == (1080, 1920) and not im.size == (1920, 1080):
            im = im.resize((1080, 1920))

        return im

    def save_screenshot(self, name: str) -> None:
        """Saves screenshot locally.

        Args:
            name (str): Name of the screenshot.
        """
        image: Image.Image = self.get_frame()
        # Convert image back to bytearray
        byteIO = io.BytesIO()
        image.save(byteIO, format="PNG")
        image = byteIO.getvalue()
        with open(name + ".png", "wb") as f:
            f.write(image)

    def return_pixel_color(
        self,
        x: int,
        y: int,
        c: int,
        seconds: int = 1,
    ) -> Any:
        """Returns the color of a screenshot.

        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            c (int): Color channel.
            seconds (int, optional): Wait time. Defaults to 1.

        Returns:
            Any: Screenshot color.
        """
        im: Image.Image = self.get_frame()
        screenshot: Any = np.asarray(im)  # Make it an array
        self.wait(seconds)

        return screenshot[y, x, c]

    def recover(self, count: int = 3) -> bool:
        """Return to neutral location.

        Args:
            count (int, optional): Retry attempts. Defaults to 3.

        Returns:
            bool: Returns True if the image is found, False if not.
        """
        timer: int = 0

        if self.is_visible("labels/sunandstars", region=(770, 40, 100, 100)):
            return True

        while timer < count:
            self.click("buttons/back", suppress=True)
            self.click("buttons/back2", suppress=True)
            self.click_location("neutral")
            timer += 1
            if self.is_visible("labels/sunandstars", region=(770, 40, 100, 100)):
                return True

        timestamp: str = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        self.save_screenshot("recovery_timeout_" + timestamp)
        return False

    def debug_screen(self, name: str) -> None:
        """Saves debug screenshot.

        Args:
            name (str): Name of the screenshot.
        """
        timestamp: str = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
        self.save_screenshot(name + "_" + timestamp)

    def safe_open_and_close(self, name: str, state: str) -> Union[None, Literal[True]]:
        """We call this at the start and end of every activity to make sure we are back at the main map screen, if not we are lost and exit.

        Args:
            name (str): Task name.
            state (str): String "open" or "close".

        Returns:
            None | Literal[True]: True if recover was successful. None otherwise.
        """
        # We call this at the start and end of every activity to make sure we are back at the main map screen, if not we are lost and exit
        if state == "open":
            self.logger.debug("opening task " + name)
            if self.recover() is True:
                self.logger.debug(name + " opened successfully!")
            else:
                self.logger.info("Issue opening " + name)

        if state == "close":
            if self.recover() is True:
                self.logger.debug(name + " completed successfully!")
                return True
            else:
                timestamp: str = datetime.now().strftime("%d-%m-%y_%H-%M-%S")
                self.save_screenshot(name + "_close_error_" + timestamp)
                self.logger.info("Issue closing " + name + ".")
