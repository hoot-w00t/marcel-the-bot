from marcel import Marcel, __version__
from marcel.util import embed_message
import youtube_dl
import discord
import logging

class MarcelPlugin:
    """
        Standard commands plugin for Marcel the Discord Bot
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

    plugin_name = "Standard commands"
    plugin_description = "Standard and built-in bot commands"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}ping` pongs! :clap:
    `{prefix}version` displays the bot's version
    `{prefix}help` shows you this message
    `{prefix}invite-bot` generates an invitation to add me on your server"""

    bot_commands = [
        ("ping", "ping_cmd", "clean_command"),
        ("version", "version_cmd"),
        ("invite-bot", "invite_bot_cmd", "clean_command"),
        ("help", "help_cmd", "clean_command")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def ping_cmd(self, message: discord.Message, args: list, **kwargs):
        await message.channel.send(
            message.author.mention,
            embed=embed_message(
                "Pong!",
                discord.Color.orange(),
                message="in {}ms".format(
                    int(self.marcel.latency * 1000)
                )
            ),
            delete_after=kwargs.get("settings").get("delete_after")
        )

    async def version_cmd(self, message: discord.Message, args: list, **kwargs):
        embed = embed_message("Marcel", discord.Color.blue())
        embed.add_field(name="marcel-the-bot", value=__version__, inline=False)
        embed.add_field(name="discord.py", value=discord.__version__, inline=False)
        embed.add_field(name="youtube-dl", value=youtube_dl.version.__version__, inline=False)
        await message.channel.send(embed=embed)

    async def invite_bot_cmd(self, message: discord.Message, args: list, **kwargs):
        appinfo = await self.marcel.application_info()

        invite_url = discord.utils.oauth_url(
            appinfo.id,
            discord.Permissions.all()
        )

        embed = discord.Embed(
            title="Add me on your server",
            description="Click the link above to invite me on your server",
            url=invite_url,
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=str(self.marcel.user.avatar_url))

        await message.channel.send(
            embed=embed,
            delete_after=kwargs.get("settings").get("delete_after")
        )

    async def get_plugin_help(self, plugin_name: str, prefix: str):
        plugin = self.marcel.plugins.get(plugin_name)
        try:
            if plugin:
                description_lines = [plugin["module"].plugin_description.strip()]
                help_lines = [x.strip() for x in plugin["module"].plugin_help.format(prefix=prefix).strip().splitlines()]
                return description_lines + help_lines

        except Exception as e:
            logging.error("Cannot format help message for {}: {}".format(
                plugin_name,
                e
            ))

        return None

    async def help_cmd(self, message: discord.Message, args: list, **kwargs):
        """Help command"""

        prefix = kwargs.get("settings").get("prefix")
        help_lines = list()

        if len(args) > 0:
            if args[0] == "all":
                # Show help for all plugins
                help_lines.append("{} here's the help for all the plugins.".format(
                    message.author.mention
                ))

                for plugin in self.marcel.plugins:
                    help_lines.append("**{}**:".format(
                        plugin
                    ))

                    plugin_help_lines = await self.get_plugin_help(plugin, prefix)
                    if plugin_help_lines:
                        help_lines += plugin_help_lines
                    else:
                        help_lines.append("Could not get the help for this plugin")

                    help_lines.append("")

            else:
                request = " ".join(args).strip()

                # Try to auto-complete the plugin name
                for plugin in self.marcel.plugins:
                    if plugin.lower().startswith(request.lower()):
                        request = plugin
                        break

                plugin_help =  await self.get_plugin_help(request, prefix)

                if plugin_help == None:
                    help_lines.append("No help found for `{}`. You can get a list of the plugins with `{prefix}help`.".format(
                        request,
                        prefix=prefix
                    ))
                else:
                    help_lines.append("{} here's the help for **{}**:".format(
                        message.author.mention,
                        request
                    ))
                    help_lines += plugin_help

        else:
            help_lines.append("Use `{prefix}help [plugin]` to show a specific help, or `{prefix}help all` to get everything.".format(
                prefix=prefix
            ))
            help_lines.append("You don't have to write the plugin's full name, for instance `{prefix}help standard` would autocomplete to the `Standard commands` plugin.".format(
                prefix=prefix
            ))
            help_lines.append("Here's a list of the plugins:")

            help_lines.append("```")
            for plugin in self.marcel.plugins:
                help_lines.append(plugin)
            help_lines.append("```")

        final_msg = ""
        for line in help_lines:
            if len(final_msg) + len(line) + 1 > 2000:
                await message.channel.send(final_msg)
                final_msg = ""

            final_msg += line
            final_msg += "\n"

        if len(final_msg) > 0:
            await message.channel.send(final_msg)