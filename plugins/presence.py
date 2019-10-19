from discord import Activity, ActivityType, Status
from asyncio import sleep

class MarcelPlugin:

    """
        Rich Presence plugin for Marcel the Discord Bot
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
                "type": ActivityType.listening,
                "duration": 15,
            },
            {
                "text": "version 2.0",
                "type": ActivityType.playing,
                "duration": 20,
            },
            {
                "text": "!!help",
                "type": ActivityType.playing,
                "duration": 50,
            },
            {
                "text": "github.com/hoot-w00t",
                "type": ActivityType.playing,
                "duration": 20,
            },
            {
                "text": "your commands.",
                "type": ActivityType.listening,
                "duration": 20,
            },
            {
                "text": "Minecraft",
                "type": ActivityType.playing,
                "duration": 20,
            },
            {
                "text": "the sunrise.",
                "type": ActivityType.watching,
                "duration": 15,
            }
        ]

        self.marcel.bot.loop.create_task(self.presence_background())
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def presence_background(self):
        await self.marcel.bot.wait_until_ready()
        self.messages.append({ "text": f"with {len(self.marcel.plugins)} plugins.", "type": 0, "duration": 20 })

        while not self.marcel.bot.is_closed():
            for message in self.messages:
                await self.marcel.bot.change_presence(status=Status.online, activity=Activity(name=message['text'], type=message['type']))
                await sleep(message['duration'])