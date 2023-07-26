# Dracula

A super simple discord integration I made to help make 
managing my Bacula instance a little bit easier.


## Features

Private messages on job completion.

![image](https://github.com/KenwoodFox/Dracula/assets/31870999/4f980881-b5c3-4e5d-9037-e5532650c9c2)

(configured using `config.yaml`)
```yaml
# My Config

users:
  user1:
    user-jobs:
      - Backup-User1
    discord: 000000000000000000
```

## Automatic printing of `messages`

![image](https://github.com/KenwoodFox/Dracula/assets/31870999/3d0a4067-0b57-4ebe-adb4-f4cd89cfbcb0)


## A command to eject manual loading tape drives!

![image](https://github.com/KenwoodFox/Dracula/assets/31870999/5685141a-eb62-4e98-8060-b5c7477650f1)


# How to install

Use the example `docker-compose-prod.yml` template.

Remember that you'll need a few things like the alert channel and
alert userID from discord, as well as a discord bot token.
