from random import randint

class MarcelPlugin:

    """
        Minigames plugin for Marcel the Discord Bot
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

    plugin_name = "Minigames"
    plugin_description = "A set of simple minigames."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `coin` flips a coin.
    `dice` or `dices` roll one or two dice.
    `rock`, `paper` or `scissors` play the eponym game.
    `bang` is the most basic Russian roulette.
    `thegame` _you lost it._
    """
    bot_commands = [
        "coin",
        "dice",
        "dices",
        "rock",
        "paper",
        "scissors",
        "bang",
        "thegame",
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.rps = ['Rock', 'Paper', 'Scissors']
        self.rps_win = ['I won!', 'You lost!']
        self.rps_lost = ['I lost.', 'You won!']

        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def coin(self, message, args):
        if randint(1, 20) > 10:
            await message.channel.send("It's heads!")

        else:
            await message.channel.send("It's tails!")

    def roll_dice(self):
        return randint(1, 6)

    async def dice(self, message, args):
        await message.channel.send(f"You rolled {self.roll_dice()}!")

    async def dices(self, message, args):
        await message.channel.send(f"You rolled {self.roll_dice()} and {self.roll_dice()} !")

    def play_rps(self, play):
        # play : 0 rock, 1 paper, 2 scissors
        r = randint(0, 2)
        tone = randint(0, 1)
        response = f"{self.rps[r]} ! "
        if r == play:
            response += "It's a draw!"
        elif r == 0 and play == 1:
            response += self.rps_lost[tone]
        elif r == 0 and play == 2:
            response += self.rps_win[tone]
        elif r == 1 and play == 0:
            response += self.rps_win[tone]
        elif r == 1 and play == 2:
            response += self.rps_lost[tone]
        elif r == 2 and play == 0:
            response += self.rps_lost[tone]
        elif r == 2 and play == 1:
            response += self.rps_win[tone]
        else:
            response += "That's a strange turn of events."

        return response

    async def rock(self, message, args):
        await message.channel.send(self.play_rps(0))

    async def paper(self, message, args):
        await message.channel.send(self.play_rps(1))

    async def scissors(self, message, args):
        await message.channel.send(self.play_rps(2))

    async def bang(self, message, args):
        r = randint(0, 100)
        if r < 10:
            await message.channel.send(f"**Bang!** {message.author.mention} was shot.")

        else:
            if not self.marcel.get_setting(message.guild, 'command_cleanup', self.marcel.default_settings['command_cleanup']):
                await message.add_reaction('\U0001F91E')

    async def thegame(self, message, args):
        await message.channel.send("You lost it. And so have I.")