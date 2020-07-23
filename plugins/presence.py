from marcel import Marcel, __version__
from discord.ext import tasks
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
            message["text"] = message.get("text", "")

            message["duration"] = message.get("duration", 10)
            if message["duration"] <= 0:
                message["duration"] = 10

            message["type"] = self.activity_types.get(
                message.get("type"),
                discord.ActivityType.playing
            )
            message["status"] = self.status_types.get(message.get("status"))

        self.index = 0
        self.count = len(self.messages)

        if self.marcel.is_ready():
            self.rich_presence_loop.start()
        else:
            self.marcel.register_event_handler(self, "on_ready", "on_ready")

    async def on_ready(self):
        """Start Rich Presence Loop when client is ready"""

        self.rich_presence_loop.start()

    def on_unload(self):
        """Stop background task when unloading plugin"""

        self.rich_presence_loop.cancel()

    @tasks.loop()
    async def rich_presence_loop(self):
        try:
            logging.debug("Rich Presence switching to message at index {}".format(
                self.index
            ))
            message = self.messages[self.index]

            await self.marcel.change_presence(
                status=message.get("status"),
                activity=discord.Activity(
                    name=message.get("text").format(
                        version=__version__,
                        plugin_count=len(self.marcel.plugins)
                    ),
                    type=message.get("type")
                )
            )

            self.rich_presence_loop.change_interval(seconds=message.get("duration", 10))

            if self.index + 1>= self.count:
                self.index = 0
            else:
                self.index += 1

        except Exception as e:
            logging.error("Rich Presence Loop: {}".format(e))