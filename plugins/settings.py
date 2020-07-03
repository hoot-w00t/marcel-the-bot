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
    `{prefix}delete-after` [seconds] delete temporary messages after [seconds], if value is invalid or 0, disable it
    `{prefix}reset-settings` reset the server settings to the default values
    `{prefix}clean-commands` [yes/no] clean the commands after they are are processed
    """

    bot_commands = [
        ("prefix", "prefix_cmd", "clean_command"),
        ("delete-after", "delete_after_cmd", "clean_command"),
        ("reset-settings", "reset_settings_cmd", "clean_command"),
        ("clean-commands", "clean_commands_cmd", "clean_command")
    ]

    access_denied_admin_only = "."
    prefix_regexp = r"^[A-Za-z0-9\.\;\:\!\?\,\$]*$"
    prefix_maxlen = 24

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def send_error_message(self, message: str, channel: discord.TextChannel, settings: dict):
        await channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.dark_red(),
                message=message
            ),
            delete_after=settings.get("delete_after")
        )

    async def send_admin_only_message(self, channel: discord.TextChannel, settings: dict):
        await self.send_error_message(
            "Only the server administrators have access to this command",
            channel,
            settings
        )

    async def prefix_cmd(self, message: discord.Message, args: list, **kwargs):
        settings = kwargs.get("settings")

        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel, settings)
            return

        new_prefix = " ".join(args).strip()
        new_prefix_len = len(new_prefix)

        if new_prefix_len == 0:
            await self.send_error_message(
                "Prefix cannot be null",
                message.channel,
                settings
            )
            return

        if new_prefix_len > self.prefix_maxlen:
            await self.send_error_message(
                "Prefix cannot exceed {} characters".format(self.prefix_maxlen),
                message.channel,
                settings
            )
            return

        if not re.fullmatch(self.prefix_regexp, new_prefix):
            await self.send_error_message(
                "Invalid prefix format",
                message.channel,
                settings
            )
            return

        settings["prefix"] = new_prefix

        await message.channel.send(
            embed=embed_message(
                "The prefix is now",
                discord.Color.green(),
                settings.get("prefix")
            ),
            delete_after=settings.get("delete_after")
        )

    async def delete_after_cmd(self, message: discord.Message, args: list, **kwargs):
        settings = kwargs.get("settings")

        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel, settings)
            return

        value_str = " ".join(args).strip()

        if len(value_str) > 0:
            try:
                value = round(float(value_str), 0)
                if value <= 0:
                    raise Exception()

            except:
                value = None

            settings["delete_after"] = value

            await message.channel.send(
                embed=embed_message(
                    self.plugin_name,
                    discord.Color.green(),
                    "Temporary messages will be deleted after {}s".format(
                        settings.get("delete_after")
                    ) if settings.get("delete_after") else "Temporary messages will not be deleted"
                ),
                delete_after=settings.get("delete_after")
            )

        else:

            await message.channel.send(
                embed=embed_message(
                    self.plugin_name,
                    discord.Color.green(),
                    "Temporary messages are deleted after {}s".format(
                        settings.get("delete_after")
                    ) if settings.get("delete_after") else "Temporary messages are not deleted"
                ),
                delete_after=settings.get("delete_after")
            )

    async def reset_settings_cmd(self, message: discord.Message, args: list, **kwargs):
        settings = kwargs.get("settings")

        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel, settings)
            return

        del self.marcel.server_settings[str(message.guild.id)]
        settings = self.marcel.get_server_settings(message.guild)

        await message.channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.green(),
                "Server settings reset to default values"
            ),
            delete_after=settings.get("delete_after")
        )

    async def clean_commands_cmd(self, message: discord.Message, args: list, **kwargs):
        settings = kwargs.get("settings")

        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel, settings)
            return

        option = " ".join(args).strip().lower()

        if option == "yes":
            settings["clean_commands"] = True

        elif option == "no":
            settings["clean_commands"] = False

        await message.channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.green(),
                message="Command cleanup is {}".format(
                    "enabled" if settings.get("clean_commands") else "disabled"
                )
            ),
            delete_after=settings.get("delete_after")
        )