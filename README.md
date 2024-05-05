# AutoAFK2

## An automation tool for AFK Journey

Same as the last project except this time much much lighter.

Run AutoAFK2.exe and after connecting you should be greeted with the following:

![image](https://github.com/Fortigate/AutoAFK2/assets/46250387/e7ce8e81-8141-4053-8665-b5bf8b976fd5)

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
* Collect all:
  * Daily Quests
  * Guild Quests
  * Growth quests
  * Noble Path
  * Events (some of them anyway)
* Open daily tower and battle until defeat  
* Click all heroes for 6 affinity a day

Can also be run with the launch flag ````-d```` 

````Run Team-up farming````

Will open chat and join any active Corrupt Creature as a priority, if none are found it will send your second strongest hero to any Synergy battle Requests. Great for farming hearts for affinity items overnight, and helps your server out! You can configure a time limit to run for also.

Can also be run with the launch flag ````-t```` 

````Retry Trial of Abyss````

Will open Trial of Abyss and indefinitely retry the available stage, continuing after victory.

Can also be run with the launch flag ````-a```` 

````Retry Faction Tower````

Will open the defined tower and indefintely retry the available stage, continuing after victory.

Can also be run with the launch flag ````-l```` 

### Optional flags:

````-c config.ini````

Will load an alternative settings.ini file when launching, useful for multiple accounts


More functionality and features coming as as when we have energy to add them.

## How to use

Get the latest [release](https://github.com/Fortigate/AutoAFK2/releases), specify your ADB port in settings.ini and run AutoAFK2.exe with (or without) the appropriate launch parameter

## Issues?

Make an issue here or DM me on Discord @ ````Jc.2````
