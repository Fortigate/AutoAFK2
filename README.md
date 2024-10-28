# AutoAFK2

## An automation tool for AFK Journey

Same as the last project except this time much much lighter.

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

Get the latest [release](https://github.com/Fortigate/AutoAFK2/releases), specify your ADB port in settings.ini and run AutoAFK2.exe with (or without) the appropriate launch parameter

## Issues?

Make an issue here or DM me on Discord @ ````Jc.2````
