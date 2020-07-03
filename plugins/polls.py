from marcel import Marcel
from marcel.util import embed_message
import discord

class MarcelPlugin:
    """
        Polls plugin for Marcel the Discord Bot
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

    plugin_name = "Polls"
    plugin_description = "Fast and easy polls using reactions"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}poll` [question] creates a simple yes/no/whatever poll using reactions. Or you can add answers (up to 20) separated by `;`.
    **Example**: `{prefix}poll Question; First answer; Second answer; Third answer`
    """

    bot_commands = [
        ("poll", "poll_cmd", "clean_command")
    ]

    unicode_letters = [
        ("A", '\U0001F1E6'),
        ("B", '\U0001F1E7'),
        ("C", '\U0001F1E8'),
        ("D", '\U0001F1E9'),
        ("E", '\U0001F1EA'),
        ("F", '\U0001F1EB'),
        ("G", '\U0001F1EC'),
        ("H", '\U0001F1ED'),
        ("I", '\U0001F1EE'),
        ("J", '\U0001F1EF'),
        ("K", '\U0001F1F0'),
        ("L", '\U0001F1F1'),
        ("M", '\U0001F1F2'),
        ("N", '\U0001F1F3'),
        ("O", '\U0001F1F4'),
        ("P", '\U0001F1F5'),
        ("Q", '\U0001F1F6'),
        ("R", '\U0001F1F7'),
        ("S", '\U0001F1F8'),
        ("T", '\U0001F1F9'),
    ]

    unicode_yesno = [
        '\U00002B06',
        '\U00002B07',
        '\U0001F937',
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def add_yesno(self, message: discord.Message):
        for e in self.unicode_yesno:
            await message.add_reaction(e)

    async def add_letters(self, message: discord.Message, count: int):
        for i in range(0, count):
            await message.add_reaction(self.unicode_letters[i][1])

    async def poll_cmd(self, message: discord.Message, args: list, **kwargs):
        poll = [x.strip() for x in " ".join(args).strip().split(";")]
        while "" in poll:
            poll.remove("")

        if len(poll) == 0:
            await message.channel.send(
                embed=embed_message(
                    "You cannot make an empty poll",
                    discord.Color.dark_red()
                ),
                delete_after=kwargs.get("settings").get("delete_after")
            )
            return

        question = poll[0]
        answers = poll[1:]

        answer_count = len(answers)

        if answer_count:
            if answer_count > len(self.unicode_letters):
                await message.channel.send("You can't have more than {} answers.".format(
                    len(self.unicode_letters)
                ))
                return

            poll_embed = discord.Embed(
                color=0xff8100,
                title=question,
                description="Poll by {}".format(
                    message.author.mention
                )
            )

            for i in range(0, answer_count):
                poll_embed.add_field(
                    name=self.unicode_letters[i][0],
                    value=answers[i],
                    inline=True
                )

        else:
            poll_embed = discord.Embed(
                color=0xff8100,
                title=question,
                description="Poll by {}".format(
                    message.author.mention
                )
            )

        poll_message = await message.channel.send(
            embed=poll_embed
        )

        if answer_count > 0:
            await self.add_letters(poll_message, answer_count)

        else:
            await self.add_yesno(poll_message)
