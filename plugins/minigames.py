from marcel import Marcel
from marcel.util import embed_message
import random
import discord

class MarcelPlugin:
    """
        Minigames plugin for Marcel the Discord Bot
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

    plugin_name = "Minigames"
    plugin_description = "Simple minigames"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}coin` flips a coin.
    `{prefix}dice` or `{prefix}dices` roll one or two dice.
    `{prefix}rock`, `{prefix}paper` or `{prefix}scissors` play the eponym game.
    `{prefix}bang` is the most basic Russian roulette.
    `{prefix}thegame` _you lost it._
    """

    bot_commands = [
        ("coin", "coin_cmd"),
        ("dice", "dice_cmd"),
        ("dices", "dices_cmd"),
        ("rock", "rock_cmd"),
        ("paper", "paper_cmd"),
        ("scissors", "scissors_cmd"),
        ("bang", "bang_cmd"),
        ("thegame", "thegame_cmd")
    ]

    rps = [
        "Rock",
        "Paper",
        "Scissors"
    ]
    rps_win = [
        "I won!",
        "You lost!"
    ]
    rps_lost = [
        "I lost.",
        "You won!"
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def coin_cmd(self, message: discord.Message, args: list, **kwargs):
        if random.randint(1, 10) > 5:
            await message.channel.send(
                embed=embed_message(
                    "It's heads!",
                    discord.Color.blue()
                )
            )

        else:
            await message.channel.send(
                embed=embed_message(
                    "It's tails!",
                    discord.Color.blue()
                )
            )

    def roll_dice(self):
        return random.randint(1, 6)

    async def dice_cmd(self, message: discord.Message, args: list, **kwargs):
        await message.channel.send(
            embed=embed_message(
                "You rolled {}!".format(self.roll_dice()),
                discord.Color.blue()
            )
        )

    async def dices_cmd(self, message: discord.Message, args: list, **kwargs):
        await message.channel.send(
                embed=embed_message(
                    "You rolled {} and {}!".format(
                        self.roll_dice(),
                        self.roll_dice()
                    ),
                    discord.Color.blue()
                )
            )

    async def play_rps(self, play: int, channel: discord.TextChannel):
        # play : 0 rock, 1 paper, 2 scissors

        r = random.randint(0, 2)
        tone = random.randint(0, 1)
        if r == play:
            result = "It's a draw!"
        elif r == 0 and play == 1:
            result = self.rps_lost[tone]
        elif r == 0 and play == 2:
            result = self.rps_win[tone]
        elif r == 1 and play == 0:
            result = self.rps_win[tone]
        elif r == 1 and play == 2:
            result = self.rps_lost[tone]
        elif r == 2 and play == 0:
            result = self.rps_lost[tone]
        elif r == 2 and play == 1:
            result = self.rps_win[tone]
        else:
            result = "That's a strange turn of events."

        await channel.send(
            embed=embed_message(
                "{} ! {}".format(
                    self.rps[r],
                    result
                ),
                discord.Color.blue()
            )
        )

    async def rock_cmd(self, message: discord.Message, args: list, **kwargs):
        await self.play_rps(0, message.channel)

    async def paper_cmd(self, message: discord.Message, args: list, **kwargs):
        await self.play_rps(1, message.channel)

    async def scissors_cmd(self, message: discord.Message, args: list, **kwargs):
        await self.play_rps(2, message.channel)

    async def bang_cmd(self, message: discord.Message, args: list, **kwargs):
        if random.randint(1, 6) == 1:
            await message.channel.send(
                message.author.mention,
                embed=embed_message(
                    "Bang! You were shot!",
                    discord.Color.gold()
                )
            )

        else:
            await message.add_reaction('\U0001F91E')

    async def thegame_cmd(self, message: discord.Message, args: list, **kwargs):
        await message.channel.send(
            embed=embed_message(
                "You lost it! Oh no, and so have I.",
                discord.Color.purple()
            )
        )