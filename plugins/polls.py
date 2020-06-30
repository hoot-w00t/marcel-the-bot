import discord
import marcel

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
    plugin_help = """`{prefix}poll` [question] creates a simple yes/no/whatever poll using reactions. Or you can add answers (up to 20) which range from A to T (letters added automatically, a semicolon is a new answer).
    ```
    poll [question]; First answer; Second answer; Third answer
    ```
    You can also ping everyone at the same time using `{prefix}pollall` (moderators and administrators only).
    """

    bot_commands = [
        ("poll", "poll_cmd"),
        ("pollall", "pollall_cmd"),
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

    def __init__(self, marcel: marcel.Marcel):
        self.marcel = marcel

    async def add_yesno(self, message: discord.Message):
        for e in self.unicode_yesno:
            await message.add_reaction(e)

    async def add_letters(self, message: discord.Message, count: int):
        for i in range(0, count):
            await message.add_reaction(self.unicode_letters[i][1])

            if i >= len(self.unicode_letters) - 1:
                break

    async def poll_cmd(self, message: discord.Message, args: list, everyone: bool = False):
        poll = [x.strip() for x in " ".join(args).strip().split(";")]
        while "" in poll:
            poll.remove("")

        if len(poll) == 0:
            await message.channel.send("You cannot poll with nothing.")
            return

        if message.guild.me.guild_permissions.manage_messages:
            await message.delete()

        else:
            await message.channel.send("I need the `Manage Messages` permission to clean the command.")

        question = poll[0]
        answers = poll[1:]

        answer_count = len(answers)

        if answer_count:
            if answer_count > len(self.unicode_letters):
                await message.channel.send("You can't have more than {} answers.".format(
                    len(self.unicode_letters)
                ))
                return

            embed_message = discord.Embed(
                color=0xff8100,
                title=question,
                description="Poll by {}".format(
                    message.author.mention
                )
            )

            for i in range(0, answer_count):
                embed_message.add_field(
                    name=self.unicode_letters[i][0],
                    value=answers[i],
                    inline=True
                )

        else:
            embed_message = discord.Embed(
                color=0xff8100,
                title=question,
                description="Poll by {}".format(
                    message.author.mention
                )
            )

        poll_message = await message.channel.send(
            content="" if not everyone else "@everyone" if self.marcel.is_member_admin(message.author) else "Only moderators and administrators can ping everyone.",
            embed=embed_message
        )

        if answer_count > 0:
            await self.add_letters(poll_message, answer_count)

        else:
            await self.add_yesno(poll_message)

    async def pollall_cmd(self, message: discord.Message, args: list):
        await self.poll_cmd(message, args, everyone=True)