from json import dump as json_dump
from json import load as json_load
from random import randint
from os.path import join, exists
from os import makedirs, listdir
from discord import Embed

class MarcelPlugin:

    """
        Quotes plugin for Marcel the Discord Bot
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

    plugin_name = 'Quotes'
    plugin_description = "All sorts of private joke quotes."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `tek` tells Epitech-sorta-related _"quotes"_, cringe warning.
    `lonely` helps you gather friends when feeling lonely.
    `quote` displays a custom quote from the guild.
    `pin` {quote} pins a custom quote to the guild.
    """
    bot_commands = [
        "tek",
        "lonely",
        "quote",
        "pin",
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.quotes_folder = join(self.marcel.resources_folder, 'quotes')
        self.quotes = {}

        if not exists(self.quotes_folder):
            makedirs(self.quotes_folder)

        for filename in listdir(self.quotes_folder):
            if filename.endswith('.json'):
                try:
                    fullpath = join(self.quotes_folder, filename)
                    with open(fullpath, 'r') as h:
                        quotes = json_load(h)
                        self.quotes[quotes["id"]] = quotes

                except Exception as e:
                    self.marcel.print_log(f"[{self.plugin_name}] Error loading quotes file: {fullpath}: {e}")

        self.tek_quotes = [
            "It's dangerous to go alone! Take this. :coffee:",
            "Sleep? Where we're going, we don't need sleep.",
            "Do. Or do not. There is no try.",
            "Code here, I'll be back.",
            "It can't be bargained with. It can't be reasoned with. It doesn't feel pity, or remorse, or fear. And it will absolutely not stop, ever. Until you compile.",
            "Sleep can be controlled - you just disconnect it",
            "Say my name - IT'S PIKACHU!",
        ]

        self.lonely_quotes = [
            "Hey @everyone, how y'all doin'?", 
            "Shh. I heard something... is that @everyone?",
            "@everyone get in here!",
            "You have (1) missed ping from @everyone",
            "@everyone joined the battle!",
            "Hey, have a wonderful day @everyone! :smile:",
        ]


        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def tek(self, message, args):
        await message.channel.send(f'_"{self.tek_quotes[randint(0, len(self.tek_quotes) - 1)]}"_')

    async def lonely(self, message, args):
        await message.channel.send(self.lonely_quotes[randint(0, len(self.lonely_quotes) - 1)])

    def save_quotes(self, guild_id):
        filename = join(self.quotes_folder, f"{guild_id}.json")

        try:
            with open(filename, 'w') as h:
                json_dump(self.quotes[guild_id], h)

        except Exception as e:
            self.marcel.print_log(f"[{self.plugin_name}] Error saving quotes file: {filename}: {e}")

    def get_embed(self, quote):
        embed=Embed(title=quote['quote'], description="by " + quote['author'], url=None, color=0xc87600)
        return embed

    async def pin(self, message, args):
        guild_id = f"{message.guild.id}"

        if not guild_id in self.quotes:
            self.quotes[guild_id] = {
                "id": guild_id,
                "quotes": []
            }

        if args:
            quote = ' '.join(args)
            self.quotes[guild_id]["quotes"].append({'quote': quote, 'author': f"{message.author}"})
            self.save_quotes(guild_id)

            await message.channel.send(f"Your quote is in! There are now {len(self.quotes[guild_id]['quotes'])} quotes.")

        else:
            await message.channel.send(f"There are {len(self.quotes[guild_id]['quotes'])} quotes.")

    async def quote(self, message, args):
        guild_id = f"{message.guild.id}"

        if guild_id in self.quotes:
            if len(self.quotes[guild_id]["quotes"]) > 0:
                await message.channel.send(embed=self.get_embed(self.quotes[guild_id]["quotes"][randint(0, len(self.quotes[guild_id]["quotes"]) - 1)]))

            else:
                await message.channel.send("There are no quotes.")

        else:
            await message.channel.send("There are no quotes.")