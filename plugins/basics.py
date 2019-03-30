class MarcelPlugin:

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
        if self.marcel.verbose : print("Basic commands plugin loaded.")

    async def ping(self, message, args):
        await self.marcel.bot.send_message(message.channel, "Pong! " + message.author.mention)
    
    async def help(self, message, args):
        prefix = self.marcel.get_setting(message.server, 'prefix', self.marcel.default_settings['prefix'])
        if len(args) > 0:
            if args[0] == "all":
                helps = []

                for plugin in self.marcel.plugins:
                    helps.append('**' + self.marcel.plugins[plugin].plugin_name + "**:\n" + self.marcel.plugins[plugin].plugin_help)
                
                help_message = message.author.mention + " here's the help for all the plugins.\n" + '\n'.join(helps).strip()
                
                if len(help_message) > 2000:
                    await self.marcel.bot.send_message(message.channel, "Unable to display the helps from all plugins at once, it exceeds Discord's 2000 character limit. Use `" + prefix + "help [plugin]` instead.")
                
                else:
                    await self.marcel.bot.send_message(message.channel, help_message)

            else:
                request = ' '.join(args)
                found_help = False
                for plugin in self.marcel.plugins:
                    if plugin.lower().startswith(request.lower()):
                        await self.marcel.bot.send_message(message.channel, message.author.mention + " here's the help for **" + plugin + "**:\n" + self.marcel.plugins[plugin].plugin_help)
                        found_help = True
                        break
                
                if not found_help:
                    await self.marcel.bot.send_message(message.channel, "No help found for `" + request + "`. You can get a list of the plugins with `" + prefix + "help`.")

        else:
            plugin_list = []

            for plugin in self.marcel.plugins:
                plugin_list.append(plugin)
            
            await self.marcel.bot.send_message(message.channel, "Use `" + prefix + "help [plugin]` to show a specific help, or `" + prefix + "help all` to get everything.\nYou don't have to write the plugin's full name, for instance `" + prefix + "help basic` would autocomplete to the `Basic commands` plugin.\nHere's a list of the plugins:\n```\n" + '\n'.join(plugin_list) + '```')
            