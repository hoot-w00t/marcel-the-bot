from marcel import Marcel
from marcel.util import embed_message
import discord
import re

class MarcelPlugin:

    """
        Settings plugin for Marcel the Discord Bot
        Copyright (C) 2019-2020  akrocynova

        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.

        This program is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        GNU General Public License for more details.

        You should have received a copy of the GNU General Public License
        along with this program.  If not, see <http://www.gnu.org/licenses/>.
    """

    plugin_name = "Settings"
    plugin_description = "Settings and tools to tweak the bot"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}prefix` [new prefix] changes the prefix used by the bot.
    `{prefix}ack-commands` [yes/no] if it is set to yes, the bot will add reactions on the commands to acknowledge that they were processed
    `{prefix}reset-settings` reset the server settings to the default values
    """

    bot_commands = [
        ("prefix", "prefix_cmd"),
        ("ack-commands", "ack_commands_cmd"),
        ("reset-settings", "reset_settings_cmd")
    ]

    access_denied_admin_only = "."
    prefix_regexp = r"^[A-Za-z0-9\.\;\:\!\?\,]*$"
    prefix_maxlen = 24

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def send_admin_only_message(self, channel: discord.TextChannel):
        await channel.send(
            embed=embed_message(
                "Only the server administrators have access to this command",
                discord.Color.red()
            )
        )

    async def prefix_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel)
            return

        new_prefix = " ".join(args)
        new_prefix_len = len(new_prefix)

        if new_prefix_len == 0:
            await message.channel.send("Prefix cannot be null")
            return

        if new_prefix_len > self.prefix_maxlen:
            await message.channel.send("Prefix cannot exceed {} characters".format(
                self.prefix_maxlen
            ))
            return

        if not re.fullmatch(self.prefix_regexp, new_prefix):
            await message.channel.send("Invalid prefix format")
            return

        guild_settings = self.marcel.get_server_settings(message.guild)
        guild_settings["prefix"] = new_prefix

        await message.channel.send("The prefix is now: `{}`".format(
            new_prefix
        ))

    async def ack_commands_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel)
            return

        request = " ".join(args).strip().lower()
        guild_settings = self.marcel.get_server_settings(message.guild)

        if request == "yes":
            guild_settings["ack_commands"] = True
            await message.channel.send("Commands will be acknowledged")

        elif request == "no":
            guild_settings["ack_commands"] = False
            await message.channel.send("Commands will not be acknowledged")

        else:
            await message.channel.send("Invalid option")

    async def reset_settings_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel)
            return

        del self.marcel.server_settings[str(message.guild.id)]
        await message.channel.send("Server settings reset to default")
