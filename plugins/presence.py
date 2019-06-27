import asyncio, discord

class MarcelPlugin:

    plugin_name = "Rich Presence"
    plugin_description = "Adds custom Rich Presence to the bot."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = "    This plugin has no commands, its purpose is to update the Rich Presence status.\n"
    bot_commands = []

    def __init__(self, marcel):
        self.marcel = marcel

        self.messages = [
            {
                "text": "Science is Fun.",
                "type": discord.ActivityType.listening,
                "duration": 10,
            },
            {
                "text": "version 1.0.0",
                "type": discord.ActivityType.playing,
                "duration": 20,
            },
            {
                "text": "type !!help",
                "type": discord.ActivityType.playing,
                "duration": 50,
            },
            {
                "text": "no longer in beta!",
                "type": discord.ActivityType.playing,
                "duration": 30,
            },
            {
                "text": "your commands.",
                "type": discord.ActivityType.listening,
                "duration": 20,
            },
            {
                "text": "Fortnite",
                "type": discord.ActivityType.playing,
                "duration": 80,
            },
            {
                "text": "the sunrise.",
                "type": discord.ActivityType.watching,
                "duration": 10,
            }
        ]

        self.marcel.bot.loop.create_task(self.presence_background())
        if self.marcel.verbose : self.marcel.print_log("[Rich Presence] Plugin loaded.")

    async def presence_background(self):
        await self.marcel.bot.wait_until_ready()
        self.messages.append({ "text": "with " + str(len(self.marcel.plugins)) + " plugins.", "type": 0, "duration": 20 })
        while not self.marcel.bot.is_closed():
            for message in self.messages:
                await self.marcel.bot.change_presence(status=discord.Status.online, activity=discord.Activity(name=message['text'], type=message['type']))
                await asyncio.sleep(message['duration'])