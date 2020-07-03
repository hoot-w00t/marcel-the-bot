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