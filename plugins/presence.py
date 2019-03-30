import asyncio

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
                "text": "back from the dead.",
                "url": None,
                "type": 0,
                "duration": 20
            },
            {
                "text": "version 0.1.0",
                "url": None,
                "type": 0,
                "duration": 30
            },
            {
                "text": "Now with plugins!",
                "url": None,
                "type": 0,
                "duration": 15,
            },
            {
                "text": "still a beta.",
                "url": None,
                "type": 0,
                "duration": 30,
            },
            {
                "text": "your commands.",
                "url": None,
                "type": 2,
                "duration": 20,
            },
        ]

        self.marcel.bot.loop.create_task(self.presence_background())
        if self.marcel.verbose : print("Rich Presence plugin loaded.")

    async def presence_background(self):
        await self.marcel.bot.wait_until_ready()
        self.messages.append({"text": "with " + str(len(self.marcel.plugins)) + " plugins.", "url": None, "type": 0, "duration": 20 })
        while not self.marcel.bot.is_closed:
            for message in self.messages:
                await self.marcel.change_presence(message['text'], url=message['url'], ptype=message['type'])
                await asyncio.sleep(message['duration'])