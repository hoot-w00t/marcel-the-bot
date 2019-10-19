from discord import Message, Embed

class MarcelPlugin:

    """
        Polls plugin for Marcel the Discord Bot
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

    plugin_name = "Polls"
    plugin_description = "Fast and simple polls."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `poll` {question} creates a simple yes/no/whatever poll using reactions. Or you can add answers (up to 20) which have range from A to T (letters added automatically, a new line is a new answer).
```
poll {question}
First answer
Second answer
Third answer
```
You can also ping everyone using `pollall` (moderators and administrators only).
    """
    bot_commands = [
        "poll",
        "pollall",
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.unicode_letters = [
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

        self.unicode_yesno = [
            '\U00002B06',
            '\U00002B07',
            '\U0001F937',
        ]

        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def add_yesno(self, message):
        for e in self.unicode_yesno:
            await message.add_reaction(e)

    async def add_letters(self, message, count):
        for i in range(0, count):
            await message.add_reaction(self.unicode_letters[i][1])

            if i >= len(self.unicode_letters) - 1:
                break

    async def poll(self, message, args, everyone=False):
        if len(args) > 0:
            if not self.marcel.get_setting(message.guild, 'command_cleanup', self.marcel.default_settings['command_cleanup']):
                if message.guild.me.guild_permissions.manage_messages:
                    await message.delete()

                else:
                    await message.channel.send("I need the `Manage Messages` permission to clean the command.")

            poll_question = ' '.join(args).strip()

            if '\n' in poll_question:
                poll_lines = poll_question.split('\n')
                answer_count = len(poll_lines) - 1
                if answer_count > len(self.unicode_letters):
                    await message.channel.send(f"You can't have more than {len(self.unicode_letters)} answers.")

                embed_message = Embed(color=0xff8100, title=poll_lines[0], description=f"Poll by {message.author.mention}")

                for i in range(1, len(poll_lines)):
                    embed_message.add_field(name=self.unicode_letters[i - 1][0], value=poll_lines[i], inline=True)

                    if i >= len(self.unicode_letters):
                        break

            else:
                embed_message = Embed(color=0xff8100, title=poll_question, description=f"Poll by {message.author.mention}")

            if everyone:
                if self.marcel.is_moderator(message) or self.marcel.is_admin(message):
                    poll_message = await message.channel.send(content="@everyone", embed=embed_message)

                else:
                    await message.channel.send("Only moderators and administrators can ping everyone.")
                    poll_message = await message.channel.send(embed=embed_message)

            else:
                poll_message = await message.channel.send(embed=embed_message)

            if '\n' in poll_question:
                await self.add_letters(poll_message, answer_count)

            else:
                await self.add_yesno(poll_message)

        else:
            await message.channel.send("You cannot poll with nothing.")

    async def pollall(self, message, args):
        await self.poll(message, args, everyone=True)