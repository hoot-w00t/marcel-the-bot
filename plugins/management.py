class MarcelPlugin:

    """
        Management plugin for Marcel the Discord Bot
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

    plugin_name = "Management"
    plugin_description = "Settings and tools to tweak the bot to your liking."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    **These commands can only be run by an administrator.**
    `prefix` [prefix] changes the prefix used by the bot (default is !!), cannot exceed 3 characters long.
    `lang` [fr, en] changes the lang (not being used yet and will change to locales [fr-fr, en-us] in the future).
    `command_cleanup` [on, off] enables/disables the automatic deletion of this bot's commands in text channels.
    `deny` or `allow` @someone denies or re-allows people to use the bot. `denied` displays the list of denied users.
    `purge` @someone deletes every message from mentionned people in the last 100 messages sent in a channel. You can `purge` [amount] @someone to search in the last [amount] of messages sent.
    `purgeall` deletes every message in a channel (in the last 50 messages). You can `purgeall` [amount] to delete the [amount] of messages.
    Purge [amount] cannot exceed 250.
    """
    bot_commands = [
        "prefix",
        "lang",
        "command_cleanup",
        "denied",
        "deny",
        "allow",
        "purge",
        "purgeall",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def send_access_denied(self, channel):
        await channel.send("Only the server administrators have access to this command.")

    async def prefix(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_prefix = args[0]
                if 4 > len(new_prefix) > 0:
                    self.marcel.set_setting(message.guild, 'prefix', new_prefix)
                    await message.channel.send(f"The prefix is now: `{new_prefix}`")
                else:
                    await message.channel.send("The prefix cannot exceed 3 characters.")

            else:
                await message.channel.send("You need to specify a new prefix.")

        else:
            await self.send_access_denied(message.channel)

    async def lang(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_lang = args[0]
                if new_lang in ['fr', 'en']:
                    self.marcel.set_setting(message.guild, 'lang', new_lang)
                    await message.channel.send(f"The lang is now: `{new_lang}`")

                else:
                    await message.channel.send("Invalid lang.")

            else:
                await message.channel.send(f"The lang is currently: `{self.marcel.get_setting(message.guild, 'lang', self.marcel.default_settings['lang'])}`")

        else:
            await self.send_access_denied(message.channel)

    async def command_cleanup(self, message, args):
        if self.marcel.is_admin(message):
            if args:
                new_value = args[0].lower()
                if new_value == 'on':
                    self.marcel.set_setting(message.guild, 'command_cleanup', True)
                else:
                    self.marcel.set_setting(message.guild, 'command_cleanup', False)

            state = self.marcel.get_setting(message.guild, 'command_cleanup', self.marcel.default_settings['command_cleanup'])
            if state:
                await message.channel.send(f"Command cleanup is enabled.")

            else:
                await message.channel.send(f"Command cleanup is disabled.")

        else:
            await self.send_access_denied(message.channel)

    async def denied(self, message, args):
        if self.marcel.is_admin(message):
            denied_users = []

            for user_id in self.marcel.get_setting(message.guild, 'denied_users', []):
                user = message.guild.get_member(user_id)
                denied_users.append(user.mention)

            if len(denied_users) == 0:
                await message.channel.send("No one is denied from using the bot.")

            else:
                await message.channel.send(f"Denied users: {', '.join(denied_users)}")

        else:
            await self.send_access_denied(message.channel)

    async def deny(self, message, args):
        if self.marcel.is_admin(message):
            if len(message.mentions) == 0:
                await message.channel.send("You need to tag people to deny.")

            else:
                denied_users = self.marcel.get_setting(message.guild, 'denied_users', [])

                for user in message.mentions:
                    if not user.id in denied_users:
                        denied_users.append(user.id)
                        await message.channel.send(f"{user.mention} is now denied.")

                    else:
                        await message.channel.send(f"{user.mention} is already denied.")

                self.marcel.set_setting(message.guild, 'denied_users', denied_users)

        else:
            await self.send_access_denied(message.channel)

    async def allow(self, message, args):
        if self.marcel.is_admin(message):
            if len(message.mentions) == 0:
                await message.channel.send("You need to tag people to allow.")

            else:
                denied_users = self.marcel.get_setting(message.guild, 'denied_users', [])

                for user in message.mentions:
                    if user.id in denied_users:
                        denied_users.remove(user.id)
                        await message.channel.send(f"{user.mention} is now allowed.")

                    else:
                        await message.channel.send(f"{user.mention} is already allowed.")

                self.marcel.set_setting(message.guild, 'denied_users', denied_users)

        else:
            await self.send_access_denied(message.channel)

    async def purge(self, message, args, mentions_only=True, limit=100):
        if self.marcel.is_admin(message):
            if len(args) > 0:
                try:
                    limit = int(args[0])

                except:
                    pass

            if limit < 0:
                limit = 0

            elif limit > 250:
                limit = 250

            if message.guild.me.guild_permissions.manage_messages:
                try:
                    if mentions_only:
                        users_to_purge = message.mentions

                        def purge_condition(m):
                            return m.author in users_to_purge

                        deleted = await message.channel.purge(limit=limit, check=purge_condition, bulk=True)

                    else:
                        deleted = await message.channel.purge(limit=limit, bulk=True)

                    await message.channel.send(f"{len(deleted)} messages deleted.")

                except Exception as e:
                    await message.channel.send(f"Purge messages: {e}")

            else:
                await message.channel.send("I need the `Manage messages` permission to purge messages.")

        else:
            await self.send_access_denied(message.channel)

    async def purgeall(self, message, args):
        await self.purge(message, args, mentions_only=False, limit=50)