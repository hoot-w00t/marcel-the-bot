from marcel import Marcel
from marcel.util import embed_message
import random
import discord
import json
import logging

class MarcelPlugin:
    """
        Nicknames plugin for Marcel the Discord Bot
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

    plugin_name = "Nicknames"
    plugin_description = "Randomize the bot's nickname"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}nick` or `{prefix}nickname` nicknames me randomly.
    """

    bot_commands = [
        ("nickname", "nickname_cmd"),
        ("nick", "nickname_cmd")

    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

        self.nicknames_file = self.marcel.cfg_path.joinpath("nicknames.json")

        try:
            with self.nicknames_file.open('r') as h:
                contents = json.load(h)

        except Exception as e:
            logging.error("Nicknames: {}".format(e))
            contents = dict()

        self.nicknames = contents.get("nicknames", list())
        self.greets = contents.get("greets", list())

    def get_nickname(self):
        return self.nicknames[random.randint(0, len(self.nicknames) - 1)]

    def get_greet(self):
        return self.greets[random.randint(0, len(self.greets) - 1)]

    async def nickname_cmd(self, message: discord.Message, args: list, **kwargs):
        if len(self.nicknames) == 0:
            await message.channel.send(
                embed=embed_message(
                    "There are no nicknames :(",
                    discord.Color.dark_red()
                )
            )
            return

        bot_member = message.guild.get_member(self.marcel.user.id)
        if bot_member.guild_permissions.change_nickname:
            new_nickname = self.get_nickname()
            if bot_member.nick == new_nickname:
                new_nickname = self.get_nickname()

            await bot_member.edit(nick=new_nickname)

            if len(self.greets) > 0:
                await message.channel.send(self.get_greet())

        else:
            await message.channel.send(
                embed=embed_message(
                    "I don't have the permission to change my nickname :(",
                    discord.Color.dark_red()
                )
            )