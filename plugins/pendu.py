from os.path import join
from random import randint
import unicodedata

class MarcelPlugin:

    """
        Pendu plugin for Marcel the Discord Bot
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

    plugin_name = "Pendu"
    plugin_description = "Le pendu, the game."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `pendu` starts a game of Pendu.
    `pendu !` force stops a game of pendu.

    **If a game is running:**
    `pendu` will display the current word.
    `pendu {one letter}` will tell you whether the letter is in the word and where it is.
    `pendu {word}` will tell you whether it is the right word to find or not.

    You can use `p` as a shortcut for `pendu`.
    """
    bot_commands = [
        "pendu",
        "p",
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.pendus = [ """       ------       
       |    |
            |
            |
            |
            |
            |
     =========
""",
"""       ------       
       |    |
       O    |
            |
            |
            |
            |
     =========
""",
"""       ------       
       |    |
       O    |
       |    |
       |    |
            |
            |
     =========
""",
"""       ------       
       |    |
       O    |
     \_|    |
       |    |
            |
            |
     =========
""",
"""       ------       
       |    |
       O    |
     \_|_/  |
       |    |
            |
            |
     =========
""",
"""       ------       
       |    |
       O    |
     \_|_/  |
       |    |
      /     |
     /      |
     =========
""",
"""       ------       
       |    |
       O    |
     \_|_/  |
       |    |
      / \   |
     /   \  |
     =========
""" ]

        self.games = {}
        self.wordlists = {}

        self.load_wordlist(join(self.marcel.resources_folder, 'wordlist.txt'))

        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    def load_wordlist(self, filename, lang="fr"):
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Loading wordlist: {filename}")
        try:
            with open(filename, 'r') as h:
                wordlist = h.read()

            self.wordlists[lang] = wordlist.split(', ')

        except Exception as e:
            self.marcel.print_log(f"[{self.plugin_name}] Error loading wordlist: {filename}: {e}")

    def remove_accents(self, input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def get_random_word(self, lang, min_length=3, max_length=20):
        word = self.wordlists["fr"][randint(0, len(self.wordlists[lang]))]
        return word

    def is_game_active(self, channel_id):
        if channel_id in self.games:
            if self.games[channel_id]['is_game_active'] : return True

        return False

    def is_game_lost(self, channel_id):
        if self.games[channel_id]['mistakes'] > len(self.pendus):
            return True

        return False

    def generate_pendu(self, length):
        return ('_ ' * length).strip()

    def discover_letter(self, channel_id, letter):
        if self.is_game_active(channel_id):
            if letter in self.games[channel_id]['word']:
                pendu = list(self.games[channel_id]['pendu'])
                for i in range(0, len(self.games[channel_id]['word'])):
                    if letter == self.games[channel_id]['word'][i]:
                        pendu[i * 2] = letter

                self.games[channel_id]['pendu'] = ''.join(pendu)
                return True

            else:
                self.games[channel_id]['mistakes'] += 1

        return False

    def discover_word(self, channel_id, word):
        if self.is_game_active(channel_id):
            if word == self.games[channel_id]['word']:
                return True
            else:
                self.games[channel_id]['mistakes'] += 1

        return False

    def start_new_game(self, channel, lang):
        self.games[channel.id] = {
            "is_game_active": False,
            "channel": None,
            "real_word": None,
            "word": None,
            "lang": "fr",
            "mistakes": 0,
            "pendu": None,
        }
        self.games[channel.id]["is_game_active"] = True
        self.games[channel.id]["channel"] = channel
        self.games[channel.id]["real_word"] = self.get_random_word(lang)
        self.games[channel.id]["word"] = self.remove_accents(self.games[channel.id]["real_word"])
        self.games[channel.id]["pendu"] = self.generate_pendu(len(self.games[channel.id]["word"]))

    async def stop_game(self, channel_id, silent=False):
        if self.is_game_active(channel_id):
            if not silent : await self.games[channel_id]['channel'].send(f"The game of pendu was stopped. The word to guess was `{self.games[channel_id]['real_word']}`.")
            del self.games[channel_id]

    async def pendu(self, message, args):
        channel_id = message.channel.id

        if self.is_game_active(channel_id):
            if args:
                if args[0] == '!':
                    await self.stop_game(channel_id)

                elif len(args[0]) == 1:
                    # letter submitted
                    if self.discover_letter(channel_id, f"{args[0]}".lower()):
                        await message.channel.send(f"```\n{self.games[channel_id]['pendu']}\n```")

                    else:
                        if self.is_game_lost(channel_id):
                            await message.channel.send(f"Oh no... you lost! The word you had to guess was: `{self.games[channel_id]['real_word']}`.")
                            await self.stop_game(channel_id, silent=True)

                        else:
                            await message.channel.send(f"```\n{self.pendus[self.games[channel_id]['mistakes'] - 1]}\n```")

                else:
                    if self.discover_word(channel_id, ''.join(args).lower().strip()):
                        await message.channel.send(f"{message.author.mention} guessed it! The word was: `{self.games[channel_id]['real_word']}`.")
                        await self.stop_game(channel_id, silent=True)

                    else:
                        if self.is_game_lost(channel_id):
                            await message.channel.send(f"Oh no... you lost! The word you had to guess was: `{self.games[channel_id]['real_word']}`.")
                            await self.stop_game(channel_id, silent=True)

                        else:
                            await message.channel.send(f"```\n{self.pendus[self.games[channel_id]['mistakes'] - 1]}\n```")
            else:
                await message.channel.send(f"```\n{self.games[channel_id]['pendu']}\n```")

        else:
            self.start_new_game(message.channel, self.marcel.get_setting(message.guild, "lang", self.marcel.default_settings['lang']))
            prefix = self.marcel.get_setting(message.guild, 'prefix', self.marcel.default_settings['prefix'])
            await message.channel.send(f"A game of Pendu has started!\nYou can submit letters/words using `{prefix}pendu [letter/word]` or `{prefix}p` as a shortcut.\n```\n{self.games[channel_id]['pendu']}\n```")

    async def p(self, message, args):
        await self.pendu(message, args)