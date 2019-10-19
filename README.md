# Marcel the Bot
## What is it?
Marcel is a  plugin-based Discord bot. It uses [discord.py](https://github.com/Rapptz/discord.py/).
It comes with a good set a plugins for many uses, but you can add/remove them if you want. You can also make your own plugin, see [Make your own plugin](#make-your-own-plugin)

## Installation
This program requires [Python 3.6+](https://docs.python.org/3.6/tutorial/index.html), [discord.py](https://github.com/Rapptz/discord.py/) with voice and [youtube_dl](https://github.com/ytdl-org/youtube-dl/) for the mediaplayer.

Follow [these instructions](https://github.com/Rapptz/discord.py/#installing) to install [discord.py](https://github.com/Rapptz/discord.py/).
Voice functionnality requires `ffmpeg` to be installed.

You can also run the installation script (made for Linux) to automatically install the files and create a service.
```bash
sudo ./install.sh
```

You can manage the service using `sudo systemctl start/stop/restart marcel-the-bot.service`.
If you want to uninstall it you can simply run `sudo ./uninstall.sh`.

You can also run it as is with `./marcel.py --config config.json`.

**Note:** [youtube_dl](https://github.com/ytdl-org/youtube-dl/) gets updated often, you will regularly need to update it in order for the related voice functionnalities to keep working: `python3 -m pip install -U youtube-dl`.
**Note:** Don't forget to edit the configuration with your token!

## Configuration
The configuration file `config.json` contains the following entries:
```json
{
    "token": "your_token_goes_here",
    "folder": ".",

    "default_server_settings": {
        "prefix": "!!",
        "lang": "fr",
        "command_cleanup": false,
        "maximum_volume": 1.0
    }
}
```
-   `token` is your bot's token ([https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token)).
-   `folder` is the bot's folder containing the `resources`, `settings`, `logs`, `temp` and `plugins` folders. The `.` represents the working directory.
-   `default_server_settings` are the bot's default settings for new servers.

## Make your own plugin
The bot will load all the files with a `.py` extension inside the `plugins` folder.

Here's a template (you can find this template under the name `plugin.template`):
```python
class MarcelPlugin:

    plugin_name = "Template plugin"
    plugin_description = "Template plugin for Marcel"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `ping` pongs! :clap:
    """
    bot_commands = [
        "ping",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def ping(self, message, args):
        await message.channel.send(f"Pong! {message.author.mention}")
```

The variables at the top are used by the bot to display help and get information about the plugin.
The `bot_commands` variable is a list of all the commands to register. Basically a command is bound to a function of the same name.
For instance here we have the `ping` command which will be bound to the `ping()` function. They have to be named the same.
In the `__init__` function, the variable `marcel` is a positional argument of the `Marcel()` class, which allows to use the bot's functions and the discord.py client referenced as `bot` (`self.marcel.bot`). You can [learn how to use discord.py here](https://discordpy.readthedocs.io/en/latest/).
This is why we have the line `self.marcel = marcel`, it stores it permanently so that any functions can interact with it. You could change the name, it doesn't really matter.
`if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")` uses the `Marcel()` class to output a message indicating that the initialization of the plugin is done and that it didn't encounter any errors.
**Note**: I'll push documentation for the voice client and general functions you can use when I find the time to.