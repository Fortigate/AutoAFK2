# AutoAFK2

## An automation tool for AFK Journey

Same as the last project except this time much much lighter.

> [!IMPORTANT]
> _Note that the bot only supports Emulators and devices with ADB, <ins>not the official desktop client</ins>_.

Run AutoAFK2.exe and after connecting you should be greeted with the following:

![image](https://github.com/user-attachments/assets/456b4c37-3687-4f89-a726-55b1b1fd49bb)

Alternatively the bot is available for [AutoAFK as a plugin](https://github.com/Hammanek/AutoAFK?tab=readme-ov-file#afk-journey-automation-integration).

### Operation modes:

````Run Dailies````

Will run these tasks to complete your daily quests (as configured in ````settings.ini````):

* Claim AFK Rewards
* Collect fast rewards (amount configurable)
* Collect Friendship Points
* Collect Mail
* Purchase a 210 gem summon card from the Guild Store in the Emporium
* Battle Arena (number of battles configurable)
* Battle Dream Realm and collect rewards
* Open Tower and push stages until defeat
* Collect all:
  * Daily Quests
  * Guild Quests
  * Growth quests
  * Noble Path
* Click all heroes for 6 affinity a day

Can also be run with the launch flag ````-d```` 

````Push Towers````

Will open the chosen tower, load formation and indefinitely retry the available stage, repeating after victory.

Can also be run with the launch flag ````-l```` 

````Push AFK Stage````

Will open AFK Stage load formation and indefinitely retry the available stage, repeating after victory.

Can also be run with the launch flag ````-afks```` 

````Push AFK Talent Stage````

Will open AFK Talent Stage, load formation and indefinitely retry the available stage, repeating after victory.

Can also be run with the launch flag ````-afkt```` 

````Push Dura's Trials````

Will open Dura's Trials, load formation and use all paid tries to try and beat it, repeating for upper and lower trials.

Can also be run with the launch flag ````-charms```` 

````Push Quests````

A bit experimental but it will clear dialogue, click items, autopath, fight battles etc to clear the active quest. It will not herd rats.

Can also be run with the launch flag ````-quest```` 

````Push Dream Realm````

Runs the last configured formation in Dream Realm for all tries including paid.

Can also be run with the launch flag ````-dr```` 

````Run Team-up farming````

Will open chat and join any active Corrupt Creature as a priority, if none are found it will send your second strongest hero to any Synergy battle Requests. Great for farming hearts for affinity items overnight, and helps your server out! You can configure a time limit to run for also.

Can also be run with the launch flag ````-t```` 

### Optional flags:

````-c config.ini````

Will load an alternative settings.ini file when launching, useful for multiple accounts

````-s global/vn````

Support for the VN server if you are playing on that.


More functionality and features coming as as when we have energy to add them.


## How to use

The bot will attempt to autoamtically conect to the first found ADB device but it is not always sucessful. You may need to manually enter the port in `settings.ini`

* Bluestacks: Go to Settings - Advanced - Enable ADB, the port is the numbers after the `:`

* LDPlayer: Settings - Other Settings - ADB Debugging - Open Local connection, the port should be `5555` by default

* MumuPlayer: Seems ADB is enabled by default on port 7555

* Connected device: Enable ADB on the device and connect to your computer using a USB cable, if your phone doesn't display a diferent port try the default `5555`

Get the latest [release](https://github.com/Fortigate/AutoAFK2/releases), specify your ADB port in settings.ini and run AutoAFK2.exe with (or without) the appropriate launch parameter

## Windows Native Development Setup

> ⚠️ **Important:** Ensure the port in `settings.ini` is correctly configured before proceeding.

1. **Set up Python Environment**  
Use `pyenv` to install the Python version specified in `.python-version`.
```bash
choco install pyenv-win
pyenv install $(cat .python-version)
pyenv local $(cat .python-version)      
 ```

2. **Create a venv and activate it**
```bash
pyenv exec python -m venv venv
.\venv\Scripts\activate.ps1
 ```

3. **Install Dependencies**  
Inside the activated virtual environment, install the required dependencies:
```bash
pip install -r requirements.txt
```

4. **Run the Application**  
The script `AutoAFK2.py` should now be runnable:
```bash
python AutoAFK2.py
```

## Issues?

Make an issue here or DM me on Discord @ ````Jc.2````
