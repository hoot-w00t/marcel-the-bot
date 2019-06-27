import random, os

class MarcelPlugin:

    plugin_name = 'Quotes'
    plugin_description = "All sorts of private joke quotes."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `tek` tells Epitech-sorta-related _"quotes"_, cringe warning.
    `lonely` helps you gather friends when feeling lonely.
    """
    bot_commands = [
        "tek",
        "lonely",
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.quotes_folder = os.path.join(self.marcel.resources_folder, 'quotes')
        
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
        ]


        if self.marcel.verbose : self.marcel.print_log("[Quotes] Plugin loaded.")
    
    def get_random(self, min, max):
        return random.randint(min, max)

    async def tek(self, message, args):
        await message.channel.send('_"' + self.tek_quotes[self.get_random(0, len(self.tek_quotes) - 1)] + '"_')
    
    async def lonely(self, message, args):
        await message.channel.send('_"' + self.lonely_quotes[self.get_random(0, len(self.lonely_quotes) - 1)] + '"_')