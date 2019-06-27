import random, discord

class MarcelPlugin:

    plugin_name = "Reactions"
    plugin_description = "Random reactions from the bot."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    **The following command can only be run by an administrator.**
    `reactions` [on, off] enables/disables reacting to messages.
    """
    bot_commands = [
        "reactions",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if not self.marcel.register_event(self, "on_message", "on_message_react"):
            self.marcel.print_log("[Reactions] Could not register the 'on_message' event.")
        
        self.unicode_emojis = {
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

        if self.marcel.verbose : self.marcel.print_log("[Reactions] Plugin loaded.")

    def getUnicodeEmoji(self, character):
        if character in self.unicode_emojis:
            return self.unicode_emojis[character]
        else:
            return False

    async def on_message_react(self, message):
        if isinstance(message.channel, discord.abc.GuildChannel):
            if self.marcel.get_setting(message.guild, 'reactions_enabled', True):
                wordlist = message.content.lower().split(' ')
                if 'woah' in wordlist:
                    await message.add_reaction('\U0001F170')
                    await message.add_reaction(self.getUnicodeEmoji("m"))
                    await message.add_reaction(self.getUnicodeEmoji("a"))
                    await message.add_reaction(self.getUnicodeEmoji("z"))
                    await message.add_reaction(self.getUnicodeEmoji("i"))
                    await message.add_reaction(self.getUnicodeEmoji("n"))
                    await message.add_reaction(self.getUnicodeEmoji("g"))

                else:
                    random_react = self.marcel.get_setting(message.guild, 'reactions_random', 10)
                    random_roll = random.randint(0, 1000)
                    if random_roll <= random_react:
                        self.marcel.set_setting(message.guild, 'reactions_random', random.randint(1, random_roll + 2))
                        for word in reversed(wordlist):
                            is_double = False
                            is_missing_emoji = False

                            for letter in word:
                                emoji = self.getUnicodeEmoji(letter)
                                if emoji == None : is_missing_emoji = True
                                if word.count(letter) > 1 : is_double = True

                            if not (is_double or is_missing_emoji):
                                for letter in word:
                                    emoji = self.getUnicodeEmoji(letter)
                                    if not emoji == None:
                                        await message.add_reaction(emoji)

                                break

    async def reactions(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_value = args[0].lower()
                if new_value == 'on':
                    self.marcel.set_setting(message.guild, 'reactions_enabled', True)
                elif new_value == 'off':
                    self.marcel.set_setting(message.guild, 'reactions_enabled', False)
                else:
                    await message.channel.send("Unknown parameter.")


            state = self.marcel.get_setting(message.guild, 'reactions_enabled', True)
            if state:
                await message.channel.send("Reactions are enabled.")
            else:
                await message.channel.send("Reactions are disabled.")

        else:
            await message.channel.send("Only the server administrators have access to this command.")