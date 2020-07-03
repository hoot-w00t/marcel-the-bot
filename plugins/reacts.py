from marcel import Marcel
from marcel.util import embed_message
import discord
import random

class MarcelPlugin:

    """
        Reactions plugin for Marcel the Discord Bot
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

    plugin_name = "Reactions"
    plugin_description = "Random reactions from the bot"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}woah` amazing!
    `{prefix}reactions` [yes, no] enables/disables random reactions to messages.
    """
    bot_commands = [
        ("reactions", "reactions_cmd", "clean_command"),
        ("woah", "woah_cmd")
    ]

    unicode_emojis = {
        "a": '\U0001F1E6',
        "b": '\U0001F1E7',
        "c": '\U0001F1E8',
        "d": '\U0001F1E9',
        "e": '\U0001F1EA',
        "f": '\U0001F1EB',
        "g": '\U0001F1EC',
        "h": '\U0001F1ED',
        "i": '\U0001F1EE',
        "j": '\U0001F1EF',
        "k": '\U0001F1F0',
        "l": '\U0001F1F1',
        "m": '\U0001F1F2',
        "n": '\U0001F1F3',
        "o": '\U0001F1F4',
        "p": '\U0001F1F5',
        "q": '\U0001F1F6',
        "r": '\U0001F1F7',
        "s": '\U0001F1F8',
        "t": '\U0001F1F9',
        "u": '\U0001F1FA',
        "v": '\U0001F1FB',
        "w": '\U0001F1FC',
        "x": '\U0001F1FD',
        "y": '\U0001F1FE',
        "z": '\U0001F1FF',
    }

    emojis_emotions = [
        "\U0001F602",
        "\U0001F613",
        "\U0001F628",
        "\U0001F631",
        "\U0001F621",
        "\U0001F603",
        "\U0001F609",
        "\U0001F61C",
        "\U0001F624",
        "\U0001F625",
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

        self.marcel.register_event_handler(self, "on_message", "on_message_react")

    async def on_message_react(self, message: discord.Message):
        if isinstance(message.channel, discord.abc.GuildChannel):
            guild_settings = self.marcel.get_server_settings(message.guild)

            if guild_settings.get("reactions_enabled", False):
                wordlist = message.content.lower().split(' ')

                random_react = guild_settings.get("reactions_rand", 10)
                random_roll = random.randint(0, 250)

                if random_roll <= random_react:
                    guild_settings["reactions_rand"] = random.randint(1, random_roll + 2)

                    word = wordlist[len(wordlist) - 1]
                    word_react = True

                    for letter in word:
                        if not self.unicode_emojis.get(letter) or word.count(letter) > 1:
                            word_react = False
                            break

                    if word_react:
                        for letter in word:
                            await message.add_reaction(self.unicode_emojis.get(letter))

                    else:
                        await message.add_reaction(
                            self.emojis_emotions[random.randint(
                                0,
                                len(self.emojis_emotions) - 1
                            )]
                        )

    async def send_admin_only_message(self, channel: discord.TextChannel, settings: dict):
        await channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.dark_red(),
                message="Only the server administrators have access to this command"
            ),
            delete_after=settings.get("delete_after")
        )

    async def reactions_cmd(self, message: discord.Message, args: list, **kwargs):
        settings = kwargs.get("settings")

        if not self.marcel.is_member_admin(message.author):
            await self.send_admin_only_message(message.channel, settings)
            return

        option = " ".join(args).strip().lower()

        if option == "yes":
            settings["reactions_enabled"] = True

        elif option == "no":
            settings["reactions_enabled"] = False

        await message.channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.green(),
                message="Random reactions are {}".format(
                    "enabled" if settings.get("reactions_enabled") else "disabled"
                )
            ),
            delete_after=settings.get("delete_after")
        )

    async def woah_cmd(self, message: discord.Message, args: list, **kwargs):
        if isinstance(message.channel, discord.abc.GuildChannel):
            await message.add_reaction('\U0001F170')
            await message.add_reaction(self.unicode_emojis.get("m"))
            await message.add_reaction(self.unicode_emojis.get("a"))
            await message.add_reaction(self.unicode_emojis.get("z"))
            await message.add_reaction(self.unicode_emojis.get("i"))
            await message.add_reaction(self.unicode_emojis.get("n"))
            await message.add_reaction(self.unicode_emojis.get("g"))