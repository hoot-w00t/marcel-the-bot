# Marcel the Bot
## What is it?
Marcel is a  plugin-based Discord bot. It uses [discord.py](https://github.com/Rapptz/discord.py/) to interact with Discord.

It comes with a good set a plugins for many uses, but you can add/remove any plugin if you want.

You can also make your own plugin, see [Make your own plugin](#make-your-own-plugin)

## Installation
This program requires [Python 3.6+](https://docs.python.org/3.3/tutorial/index.html), [discord.py](https://github.com/Rapptz/discord.py/) with voice and [youtube_dl](https://github.com/ytdl-org/youtube-dl/) for the media player.

Follow [these instructions](https://github.com/Rapptz/discord.py/#installing) to install [discord.py](https://github.com/Rapptz/discord.py/).

Voice functionnality requires `ffmpeg` or `avconv` to be installed.

You can install the bot through PyPI
```sh
python3 -m pip install --user --upgrade marcel-the-bot
```
or using the `setup.py`
```sh
python3 setup.py install
```

You can automatically install/uninstall the bot as a SystemD service on Linux using the given script
```sh
sudo ./install_linux_daemon.sh
#sudo ./uninstall_linux_daemon.sh
```
You can also run the bot manually with `python3 -m marcel -c config_folder -p plugins_folder`.

**Note:** [youtube_dl](https://github.com/ytdl-org/youtube-dl/) gets updated often, you will regularly need to update it in order for the related voice functionnalities to keep working: `python3 -m pip install --user --upgrade youtube-dl` or `su -c "python3 -m pip install --user --upgrade youtube-dl" marcel` if you installed the Linux service.

## Configuration
Here's a configuration template (which you can find in the `templates` folder):
```json
{
    "token": "your_bot_token_goes_here",
    "owners": [],
    "logging": {
        "level": "warning"
    },
    "voice_client": {
        "timeout_idle": 1800,
        "timeout_playing": 7200,
        "player_queue_limit": 20,
        "duration_limit": 1800
    },
    "server_defaults": {
        "prefix": "!!",
        "clean_commands": false,
        "delete_after": 10.0,
        "volume": 1.0,
        "volume_limit": 1.25
    }
}
```
-   `token` is your bot's token ([https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token))
-   `owners` is a list of user IDs that are bot owners, these users will have all privileges over the bot
-   `logging` defines how the bot should log information
    -   `level` is the logging level, by default it is set to `warning`
-   `voice_client` defines the voice client's behavior
    -   `timeout_idle` is the idle time (in seconds) before the voice client is automatically disconnected
    -   `timeout_playing` is the idle time while a media is playing (in seconds) before the voice client is automatically disconnected
    -   `player_queue_limit` is the maximum amount of medias that the player queue will accept
    -   `duration_limit` is the maximum duration of a media (in seconds)
-   `server_defaults` are the default settings for the Discord servers (each plugin can store its own settings too)
    -   `prefix` is the bot's prefix (by default `!!`)
    -   `clean_commands` will enable the command cleanup for commands that support it
    -   `delete_after` is the time in seconds before temporary messages are deleted (must be handled by the plugin)
    -   `volume` is the player's volume
    -   `volume_limit` is the player's maximum volume

The server settings can be changed from Discord using the commands in the `settings.py` plugin.

## Make your own plugin
The bot will load all the files with a `.py` extension in its plugins folder (can be set using `-p` or `--plugins`)

Here's a plugin template (which you can find in the `templates` folder):
```python
from marcel import Marcel
from marcel.util import embed_message
import discord
import logging

class MarcelPlugin:
    plugin_name = "Template"
    plugin_description = "Template plugin"
    plugin_author = "https://github.com/hoot-w00t"

    # The help message will be formatted to be displayed when running
    # the "help" command
    plugin_help = """`{prefix}ping` pongs! :clap:"""

    # List of tuples in the form (command, target function, ...)
    # There can be attributes after the target function:
    #    "clean_command" tells the bot to delete the command message
    # Functions are given the following arguments:
    # message: discord.Message()
    # args:    list() of the interpreted command arguments
    # **kwargs: dict() containing additionnal information like
    #                  the guild settings named "settings" (dict)
    #                  the guild media player named "mediaplayer" (MarcelMediaPlayer)
    bot_commands = [
        ("ping", "ping_cmd")
    ]

    def __init__(self, marcel: Marcel):
        # This is to give access to the bot at anytime, anywhere in the plugin
        self.marcel = marcel

        # You can log anything using the logging module
        logging.debug("Hello world!")

    async def ping_cmd(self, message: discord.Message, args: list, **kwargs):
        """Ping command"""

        await message.channel.send(
            message.author.mention,
            embed=embed_message(
                "Pong!",
                discord.Color.orange(),
                message="in {}ms".format(
                    int(self.marcel.bot.latency * 1000)
                )
            )
        )
```
[discord.py documentation](https://discordpy.readthedocs.io/en/latest/)

## Plugin configuration
### Rich Presence
The Rich Presence plugin reads its configuration from `rich_presence.json` at the root of your bot's configuration folder:
```json
[
    {
        "text": "Science is Fun",
        "type": "listening",
        "status": "dnd",
        "duration": 15
    },
    {
        "text": "version {version}",
        "status": "idle",
        "duration": 30
    },
    {
        "text": "the sunrise.",
        "type": "watching",
        "duration": 15
    }
]
```
-   `text` is the text to be displayed
-   `type` is the activity type (`playing`, `watching`, `listening`), it it `playing` by default
-   `status` is the bot's online status (`online`, `offline`, `invisible`, `do_not_disturb`, `dnd`, `idle`), it is `online` by default
-   `duration` is the duration of this status message (in seconds)

---

Some variables will be dynamically replaced by their corresponding value when displayed:
-   `{version}` will be replaced with the bot's version number (e.g. 3.2.0)
-   `{plugin_count}` will be replaced with the number of loaded plugins

### SoundBox
The SoundBox plugin will read media files from a `soundbox` folder at the root of the configuration folder.
It currently accepts the following formats: `mp3`, `ogg`, `webm` and `wav`, any of those file types in the `soundbox` folder can then be played.

### Nicknames
The Nicknames plugin reads its configuration from `nicknames.json` at the root of your bot's configuration folder:
```json
{
    "nicknames": [
        "Marcel-o-tron",
        "Herobrine"
    ],

    "greets": [
        "Fresh from the oven!",
        "It's me, Mar!... nevermind."
    ]
}
```
-   `nicknames` is a list of the different nickname the bot can choose from
-   `greets` is a list of phrases the bot will say when changing its nickname