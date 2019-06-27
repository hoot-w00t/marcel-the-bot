import random, os

class MarcelPlugin:

    plugin_name = "Pendu"
    plugin_description = "Le pendu, the game."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `pendu` starts a game of Pendu.
    `pendu !` force stops a game of pendu.

    **If a game is running:**
    `pendu` will display the current word.
    `pendu {one letter}` will tell you whether the letter is in the word and where it is.
    `pendu {word}` will tell you whether it is the right word to find or not.

    **Be careful:** if there are accents in the word you will need to find the accents too (it's a work in progress).
    """
    bot_commands = [
        "pendu",
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

        self.load_wordlist(os.path.join(self.marcel.resources_folder, 'wordlist.txt'))

        if self.marcel.verbose : self.marcel.print_log("[Pendu] Plugin loaded.")

    def load_wordlist(self, filename, lang="fr"):
        if self.marcel.verbose : self.marcel.print_log("[Pendu] Loading wordlist: " + filename)
        h = open(filename, 'r')
        wordlist = h.read()
        h.close()
        self.wordlists[lang] = wordlist.split(', ')

    def get_random_word(self, lang, min_length=3, max_length=20):
        word = self.wordlists["fr"][random.randint(0, len(self.wordlists[lang]))]
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
            "word": None,
            "lang": "fr",
            "mistakes": 0,
            "pendu": None,
        }
        self.games[channel.id]["is_game_active"] = True
        self.games[channel.id]["channel"] = channel
        self.games[channel.id]["word"] = self.get_random_word(lang)
        self.games[channel.id]["pendu"] = self.generate_pendu(len(self.games[channel.id]["word"]))
    
    async def stop_game(self, channel_id, silent=False):
        if self.is_game_active(channel_id):
            if not silent : await self.games[channel_id]['channel'].send("The game of pendu was stopped. The word to guess was `" + self.games[channel_id]['word'] + "`.")
            del self.games[channel_id]

    async def pendu(self, message, args):
        channel_id = message.channel.id

        if self.is_game_active(channel_id):
            if args:
                if args[0] == '!':
                    await self.stop_game(channel_id)
                elif len(args[0]) == 1:
                    # letter submitted
                    if self.discover_letter(channel_id, str(args[0]).lower()):
                        await message.channel.send("```\n" + self.games[channel_id]['pendu'] + "\n```")
                    else:
                        if self.is_game_lost(channel_id):
                            await message.channel.send("Oh no... you lost! The word you had to guess was: `" + self.games[channel_id]['word'] + "`.")
                            await self.stop_game(channel_id, silent=True)

                        else:
                            await message.channel.send("```\n" + self.pendus[self.games[channel_id]['mistakes'] - 1] + "\n```")

                else:
                    if self.discover_word(channel_id, ''.join(args).lower().strip()):
                        await message.channel.send(message.author.mention + " guessed it! The word was: `" + self.games[channel_id]['word'] + "`.")
                        await self.stop_game(channel_id, silent=True)
                    else:
                        if self.is_game_lost(channel_id):
                            await message.channel.send("Oh no... you lost! The word you had to guess was: `" + self.games[channel_id]['word'] + "`.")
                            await self.stop_game(channel_id, silent=True)

                        else:
                            await message.channel.send("```\n" + self.pendus[self.games[channel_id]['mistakes'] - 1] + "\n```")
            else:
                await message.channel.send("```\n" + self.games[channel_id]['pendu'] + "\n```")

        else:
            self.start_new_game(message.channel, self.marcel.get_setting(message.guild, "lang", self.marcel.default_settings['lang']))
            await message.channel.send("A game of Pendu has started!\nYou can submit letters/words using `" + self.marcel.get_setting(message.guild, 'prefix', self.marcel.default_settings['prefix']) + "pendu {letter/word}`\n```\n" + self.games[channel_id]['pendu'] + "\n```")
