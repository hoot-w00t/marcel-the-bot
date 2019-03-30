class MarcelPlugin:

    plugin_name = "Management"
    plugin_description = "Settings and tools to tweak the bot to your liking."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    **These commands can only be run by an administrator.**
    `prefix` [prefix] changes the prefix used by the bot (default is !!), cannot exceed 3 characters long.
    `lang` [fr, en] changes the lang (not being used yet and will change to locales [fr-fr, en-us] in the future).
    `command_cleanup` [true, false] enables/disables the automatic deletion of this bot's commands in text channels.
    """
    bot_commands = [
        "prefix",
        "lang",
        "command_cleanup",
        "debug",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : print("Management plugin loaded.")

    async def send_access_denied(self, channel):
        await self.marcel.bot.send_message(channel, "Only the server administrators have access to this command.")

    async def debug(self, message, args):
        print(self.marcel.all_settings)

    async def prefix(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_prefix = args[0]
                if 4 > len(new_prefix) > 0:
                    self.marcel.set_setting(message.server, 'prefix', new_prefix)
                    await self.marcel.bot.send_message(message.channel, "The prefix is now : `" + new_prefix + "`")
                else:
                    await self.marcel.bot.send_message(message.channel, "The prefix cannot exceed 3 characters.")

            else:
                await self.marcel.bot.send_message(message.channel, "You need to specify a new prefix.")

        else:
            await self.send_access_denied(message.channel)
    
    async def lang(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_lang = args[0]
                if new_lang in ['fr', 'en']:
                    self.marcel.set_setting(message.server, 'lang', new_lang)
                    await self.marcel.bot.send_message(message.channel, "The lang is now : `" + new_lang + "`")
                else:
                    await self.marcel.bot.send_message(message.channel, "Invalid lang.")

            else:
                await self.marcel.bot.send_message(message.channel, "The lang is currently : `" + self.marcel.get_setting(message.server, 'lang', self.marcel.default_settings['lang']) + "`")

        else:
            await self.send_access_denied(message.channel)

    async def command_cleanup(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_value = args[0].lower()
                if new_value == 'true':
                    self.marcel.set_setting(message.server, 'command_cleanup', True)
                else:
                    self.marcel.set_setting(message.server, 'command_cleanup', False)
                
                await self.marcel.bot.send_message(message.channel, "Command cleanup is now : `" + str(self.marcel.get_setting(message.server, 'command_cleanup', self.marcel.default_settings['command_cleanup'])) + "`")

            else:
                await self.marcel.bot.send_message(message.channel, "Command cleanup is currently : `" + str(self.marcel.get_setting(message.server, 'command_cleanup', self.marcel.default_settings['command_cleanup'])) + "`")

        else:
            await self.send_access_denied(message.channel)