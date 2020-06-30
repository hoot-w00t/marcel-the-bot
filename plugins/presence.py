from marcel import Marcel, __version__
import discord
import asyncio
import json
import logging

class MarcelPlugin:
    """
        Rich Presence plugin for Marcel the Discord Bot
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

    plugin_name = "Rich Presence"
    plugin_description = "Adds custom Rich Presence to the bot"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = ""

    bot_commands = []

    activity_types = {
        "listening": discord.ActivityType.listening,
        "watching": discord.ActivityType.watching,
        "playing": discord.ActivityType.playing
    }

    status_types = {
        "online": discord.Status.online,
        "offline": discord.Status.invisible,
        "invisible": discord.Status.invisible,
        "do_not_disturb": discord.Status.dnd,
        "dnd": discord.Status.dnd,
        "idle": discord.Status.idle
    }

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

        messages_file = self.marcel.cfg_path.joinpath("rich_presence.json")
        if messages_file.exists():
            with messages_file.open("r") as h:
                self.messages = json.load(h)
        else:
            self.messages = list()

        for message in self.messages:
            message["text"] = message.get("text", "").format(
                version=__version__
            )

            message["duration"] = message.get("duration", 10)
            if message["duration"] <= 0:
                message["duration"] = 10

            message["type"] = self.activity_types.get(
                message.get("type"),
                discord.ActivityType.playing
            )
            message["status"] = self.status_types.get(message.get("status"))

        self.stop = False
        self.marcel.bot.loop.create_task(self.presence_background())

    def unload(self):
        """Stop background task when unloading plugin"""

        self.stop = True

    def stop_background_task(self):
        return self.stop or self.marcel.bot.is_closed() or len(self.messages) == 0

    async def presence_background(self):
        try:
            if not self.marcel.bot.is_ready():
                logging.debug("Rich Presence: Waiting to be ready...")
                await self.marcel.bot.wait_until_ready()

            logging.debug("Rich Presence: Starting")
            while not self.stop_background_task():
                for message in self.messages:
                    await self.marcel.bot.change_presence(
                        status=message.get("status"),
                        activity=discord.Activity(
                            name=message.get("text"),
                            type=message.get("type")
                        )
                    )

                    for i in range(0, message["duration"]):
                        if self.stop_background_task():
                            raise Exception("Force stopped")

                        await asyncio.sleep(1)

        except Exception as e:
            logging.error("Rich Presence: {}".format(e))

        logging.error("Rich Presence background task exitted")