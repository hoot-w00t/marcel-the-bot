from marcel import Marcel
from marcel.util import embed_message
import discord

class MarcelPlugin:
    """
        Bot control plugin for Marcel the Discord Bot
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

    plugin_name = "Bot control"
    plugin_description = "Owner-only commands to control the bot"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}reload-all` reload all plugins
    `{prefix}load-new` load all new plugins
    `{prefix}reload` [plugin] reload given plugin
    `{prefix}unload` [plugin] unload given plugin
    `{prefix}save-settings` save server settings
    """

    bot_commands = [
        ("reload-all", "reload_all_cmd"),
        ("load-new", "load_new_cmd"),
        ("reload", "reload_cmd"),
        ("unload", "unload_cmd"),
        ("save-settings", "save_settings_cmd")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def send_owner_only_message(self, channel: discord.TextChannel):
        channel.send(
            embed=embed_message(
                "Only bot owners have access to this command",
                discord.Color.red()
            )
        )

    async def reload_all_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel)
            return

        try:
            await message.channel.send("Reloading all plugins...")
            self.marcel.reload_plugins()
            await message.channel.send("Reload complete!")

        except Exception as e:
            await message.channel.send("Reload failed: {}".format(e))

    async def load_new_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel)
            return

        try:
            await message.channel.send("Loading new plugins...")
            self.marcel.load_plugins()
            await message.channel.send("Loading complete!")

        except Exception as e:
            await message.channel.send("Loading failed: {}".format(e))

    async def reload_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel)
            return

        request = " ".join(args).strip()

        # Try to auto-complete the plugin name
        for plugin in self.marcel.plugins:
            if plugin.lower().startswith(request.lower()):
                await message.channel.send("Reloading plugin '{}'...".format(
                    plugin
                ))
                if self.marcel.reload_plugin(plugin):
                    await message.channel.send("Reload complete!")
                else:
                    await message.channel.send("Reload failed.")
                return

        await message.channel.send("No such plugin is currently loaded")

    async def unload_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel)
            return

        request = " ".join(args).strip()

        # Try to auto-complete the plugin name
        for plugin in self.marcel.plugins:
            if plugin.lower().startswith(request.lower()):
                self.marcel.unload_plugin(plugin)
                await message.channel.send("Unloaded plugin: {}".format(
                    plugin
                ))
                return

        await message.channel.send("No such plugin is currently loaded")

    async def save_settings_cmd(self, message: discord.Message, args: list):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel)
            return

        await message.channel.send("Saving server settings...")
        try:
            self.marcel.save_server_settings()
            await message.channel.send("Server settings saved!")

        except Exception as e:
            await message.channel.send("Unable to save settings: {}".format(e))