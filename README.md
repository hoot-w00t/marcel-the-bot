# Marcel the Bot
It uses [discord.py](https://github.com/Rapptz/discord.py/) and provides a plugin-based interface for flexibility.

# Installation
This program requires [Python 3](https://docs.python.org/3/using/index.html), [discord.py](https://github.com/Rapptz/discord.py/) with voice and [youtube_dl](https://github.com/ytdl-org/youtube-dl/) to work.

You can install the modules through PyPI : `pip3 install discord.py[voice] youtube_dl`. Depending on the plugins you will need additionnal modules like `gtts` for the `google-tts.py` plugin.

For this repository's set of plugins, you need to `pip3 install discord.py[voice] youtube_dl gtts` to have it all working.

**Note:** [youtube_dl](https://github.com/ytdl-org/youtube-dl/) gets updated regularly, you will sometimes need to update it in order for the related voice functionnalities to keep working : `pip3 install -U youtube-dl`.

Then you need to edit the configuration file with your bot's token, and then you can run it with `python3 main.py --config=/path/to/config`.

# Usage and configuration

Here the available parameters for the bot:
```
--verbose                   Show additionnal information about Marcel's state (for debugging / verbose nerds).
--config=[path]             Specify the path to the configuration file (by default looks for 'config.json' in the working directory).
```

The configuration file `config.json` which by default looks like this:
```json
{
    "bot_token": "", // your bot's token, https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token
    "bot_folder": ".", // the folder containing the 'temp', 'settings', 'plugins' and 'resources' folders.
    "logging": true // whether the bot should log in a file (not implemented yet, will come in the future)
}
```