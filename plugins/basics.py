class MarcelPlugin:

    """
        Basic commands plugin for Marcel the Discord Bot
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

    plugin_name = "Basic commands"
    plugin_description = "Basic bot commands."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `ping` pongs! :clap:
    `help` shows you this message.
    """
    bot_commands = [
        "ping",
        "help",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def ping(self, message, args):
        await message.channel.send(f"Pong! _(in {int(self.marcel.bot.latency * 1000)}ms)_ {message.author.mention}")

    async def help(self, message, args):
        prefix = self.marcel.get_setting(message.guild, 'prefix', self.marcel.default_settings['prefix'])

        if len(args) > 0:
            if args[0] == "all":
                plugin_helps = []

                for plugin in self.marcel.plugins:
                    plugin_helps.append(f"**{self.marcel.plugins[plugin].plugin_name}**:\n{self.marcel.plugins[plugin].plugin_help}")

                help_message = f"{message.author.mention} here's the help for all the plugins.\n"

                for plugin_help in plugin_helps:
                    new_help = f"{plugin_help.strip()}\n\n"

                    if len(new_help) + len(help_message) >= 2000:
                        await message.channel.send(help_message)
                        help_message = "\n"

                    help_message += new_help

                if len(help_message) > 0:
                    await message.channel.send(help_message)

            else:
                request = ' '.join(args).strip()

                for plugin in self.marcel.plugins:
                    if plugin.lower().startswith(request.lower()):
                        request = plugin
                        break

                if request in self.marcel.plugins:
                    await message.channel.send(f"{message.author.mention} here's the help for **{self.marcel.plugins[request].plugin_name}**:\n{self.marcel.plugins[request].plugin_help}")

                else:
                    await message.channel.send(f"No help found for `{request}`. You can get a list of the plugins with `{prefix}help`.")

        else:
            plugin_list = []

            for plugin in self.marcel.plugins:
                plugin_list.append(plugin)

            plugin_list_str = '\n'.join(plugin_list)

            await message.channel.send(f"Use `{prefix}help [plugin]` to show a specific help, or `{prefix}help all` to get everything.\nYou don't have to write the plugin's full name, for instance `{prefix}help basic` would autocomplete to the `Basic commands` plugin.\nHere's a list of the plugins:\n```\n{plugin_list_str}```")