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
    `{prefix}reload` [plugin] reload given plugin (or try to load unloaded plugins if no name is given)
    `{prefix}unload` [plugin] unload given plugin
    `{prefix}save-settings` save server settings
    """

    bot_commands = [
        ("reload-all", "reload_all_cmd"),
        ("reload", "reload_cmd"),
        ("unload", "unload_cmd"),
        ("save-settings", "save_settings_cmd")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def send_owner_only_message(self, channel: discord.TextChannel, settings: dict):
        channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.dark_red(),
                message="Only bot owners have access to this command"
            ),
            delete_after=settings.get("delete_after")
        )

    async def send_unknown_plugin(self, channel: discord.TextChannel, settings: dict):
        await channel.send(
            embed=embed_message(
                "Unknown or unloaded plugin",
                discord.Color.dark_red()
            ),
            delete_after=settings.get("delete_after")
        )

    async def reload_all_cmd(self, message: discord.Message, args: list, **kwargs):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel, kwargs.get("settings"))
            return

        ctlembed = embed_message(
            "Reloading all plugins...",
            discord.Color.blue()
        )
        ctlmsg = await message.channel.send(embed=ctlembed)

        try:
            loaded_plugins = self.marcel.reload_plugins()
            ctlembed = embed_message(
                "Reload complete",
                discord.Color.green(),
                "{} plugins loaded".format(loaded_plugins)
            )

        except Exception as e:
            ctlembed = embed_message(
                "Reload failed",
                discord.Color.dark_red(),
                str(e)
            )

        await ctlmsg.edit(
            embed=ctlembed,
            delete_after=kwargs.get("settings").get("delete_after")
        )

    async def reload_cmd(self, message: discord.Message, args: list, **kwargs):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel, kwargs.get("settings"))
            return

        request = " ".join(args).strip()

        if len(request) == 0:
            loaded_plugins = self.marcel.load_plugins()

            if loaded_plugins > 0:
                await message.channel.send(
                    embed=embed_message(
                        "Loaded {} plugin{}".format(
                            loaded_plugins,
                            "s" if loaded_plugins != 1 else ""
                        ),
                        discord.Color.green()
                    ),
                    delete_after=kwargs.get("settings").get("delete_after")
                )
            else:
                await message.channel.send(
                    embed=embed_message(
                        "No plugin loaded",
                        discord.Color.dark_red()
                    ),
                    delete_after=kwargs.get("settings").get("delete_after")
                )

        else:
            # Try to auto-complete the plugin name
            for plugin in self.marcel.plugins:
                if plugin.lower().startswith(request.lower()):
                    ctlembed = embed_message(
                        "Reloading plugin...",
                        discord.Color.blue(),
                        message=plugin
                    )
                    ctlmsg = await message.channel.send(embed=ctlembed)

                    if self.marcel.reload_plugin(plugin):
                        ctlembed = embed_message(
                            "Plugin reloaded",
                            discord.Color.green(),
                            message=plugin
                        )

                    else:
                        ctlembed = embed_message(
                            "Failed to reload plugin",
                            discord.Color.dark_red(),
                            message=plugin
                        )

                    await ctlmsg.edit(
                        embed=ctlembed,
                        delete_after=kwargs.get("settings").get("delete_after")
                    )
                    return

            # Auto-completion failed, plugin is not loaded
            await self.send_unknown_plugin(message.channel, kwargs.get("settings"))

    async def unload_cmd(self, message: discord.Message, args: list, **kwargs):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel, kwargs.get("settings"))
            return

        request = " ".join(args).strip()

        # Try to auto-complete the plugin name
        for plugin in self.marcel.plugins:
            if plugin.lower().startswith(request.lower()):
                self.marcel.unload_plugin(plugin)
                await message.channel.send(
                    embed=embed_message(
                        "Unloaded plugin",
                        discord.Color.blue(),
                        plugin
                    ),
                    delete_after=kwargs.get("settings").get("delete_after")
                )
                return

        await self.send_unknown_plugin(message.channel, kwargs.get("settings"))

    async def save_settings_cmd(self, message: discord.Message, args: list, **kwargs):
        if not self.marcel.is_member_owner(message.author):
            await self.send_owner_only_message(message.channel, kwargs.get("settings"))
            return

        try:
            self.marcel.save_server_settings()
            await message.channel.send(
                embed=embed_message(
                    "Server settings saved",
                    discord.Color.green()
                ),
                delete_after=kwargs.get("settings").get("delete_after")
            )

        except Exception as e:
            await message.channel.send(
                embed=embed_message(
                    "Unable to save settings",
                    discord.Color.dark_red(),
                    e
                ),
                delete_after=kwargs.get("settings").get("delete_after")
            )
