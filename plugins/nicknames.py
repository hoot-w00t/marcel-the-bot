from random import randint
from os.path import join
from json import load as json_load

class MarcelPlugin:

    """
        Nicknames plugin for Marcel the Discord Bot
        Copyright (C) 2019  akrocynova

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
    plugin_description = "Randomize the bot's nickname."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `nickname`s me randomly.
    """
    bot_commands = [
        "nickname",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        self.nicknames = []
        self.greets = []

        self.json_res_file = join(self.marcel.resources_folder, "nicknames.json")

        try:
            with open(self.json_res_file, 'r') as h:
                json_res = json_load(h)

            self.nicknames = json_res["nicknames"]
            self.greets = json_res["greets"]

        except Exception as e:
            self.marcel.print_log(f"[{self.plugin_name}] Error loading: {self.json_res_file}: {e}")

        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    def get_nickname(self):
        return self.nicknames[randint(0, len(self.nicknames) - 1)]

    def get_greet(self):
        return self.greets[randint(0, len(self.greets) - 1)]

    async def nickname(self, message, args):
        if len(self.nicknames) == 0:
            await message.channel.send("I don't have a list of nicknames. :confused:")

        else:
            bot_member = message.guild.get_member(self.marcel.bot.user.id)
            if bot_member.guild_permissions.change_nickname:
                new_nickname = self.get_nickname()
                while bot_member.nick == new_nickname:
                    new_nickname = self.get_nickname()

                await bot_member.edit(nick=new_nickname)
                await message.channel.send(self.get_greet())

            else:
                await message.channel.send("I don't have the permission to change my own nickname. :confused:")