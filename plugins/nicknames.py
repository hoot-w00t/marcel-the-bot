import random, discord

class MarcelPlugin:

    plugin_name = "Nicknames"
    plugin_description = "Randomize the bot's nickname."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `nick`names me randomly.
    """
    bot_commands = [
        "nick",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        self.nicknames = [
            "Jean-Marc Morandini",
            "Canardman",
            "Coffee-o-tron",
            "Bertrand",
            "Gonzague le concquérant",
            "Pygargue",
            "Le cul de l'amérique",
            "E-Tron",
            "Baba",
            "Billy le bonhomme de neige",
            "Steve",
            "Herobrine",
            "Bryan (not in the kitchen)",
            "Harold",
            "Error 418 - I'm a teapot",
            "Kappa",
            "Eddy Malou",
            "La sainte pelle",
            "Pedro le péruvien",
            "Batman sur sa balançoire",
            "UNE BELLE QUENOUILLE",
        ]

        self.greets = [
            "Fresh from the oven!",
            "It's me, Mar!... nevermind.",
            "Who am I? ~~_John CENA._~~",
            "Time for a cup of :tea:.",
            "No, _YOU'RE_ BREATHTAKING.",
            "I can do this all day.",
            "Hasta la vista, baby.",
        ]

        if self.marcel.verbose : self.marcel.print_log("[Nicknames] Plugin loaded.")

    def get_nickname(self):
        return self.nicknames[random.randint(0, len(self.nicknames) - 1)]
    
    def get_greet(self):
        return self.greets[random.randint(0, len(self.greets) - 1)]

    async def nick(self, message, args):
        bot_member = message.guild.get_member(self.marcel.bot.user.id)
        if bot_member.guild_permissions.change_nickname:
            await bot_member.edit(nick=self.get_nickname())
            await message.channel.send(self.get_greet())

        else:
            await message.channel.send("Oh no, I don't have the permission to change my own nickname. :c")
    