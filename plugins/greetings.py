import random

class MarcelPlugin:

    plugin_name = "Greetings"
    plugin_description = "Greetings to guild members from the bot."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    I mention people that join or leave the guild with a short message.

    **The following command can only be run by an administrator.**
    `greetings` [here, off] enables/disables greeting/leave messages. They will land in the channel where you activate them.
    """
    bot_commands = [
        "greetings",
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.join_phrases = [
            "Welcome [member] to the guild!",
            "Heyo [member] !",
        ]
        self.leave_phrases = [
            "Cya [member]. You will be missed!",
            "[member] left the guild.",
        ]

        if not self.marcel.register_event(self, "on_member_join", "on_member_join"):
            self.marcel.print_log("[Greetings] Could not register the 'on_member_join' event.")
        if not self.marcel.register_event(self, "on_member_remove", "on_member_remove"):
            self.marcel.print_log("[Greetings] Could not register the 'on_member_remove' event.")
        
        if self.marcel.verbose : self.marcel.print_log("[Greetings] Plugin loaded.")
    
    def is_greeting_enabled(self, guild):
        if self.marcel.get_setting(guild, 'greetings', False):
            if not self.marcel.get_setting(guild, 'greetings_channel', 0) == 0:
                return True

        return False

    async def on_member_join(self, member):
        if self.is_greeting_enabled(member.guild) : await member.guild.get_channel(self.marcel.get_setting(member.guild, 'greetings_channel', 0)).send(self.join_phrases[random.randint(0, len(self.join_phrases) - 1)].replace("[member]", member.mention))

    async def on_member_remove(self, member):
        if self.is_greeting_enabled(member.guild) : await member.guild.get_channel(self.marcel.get_setting(member.guild, 'greetings_channel', 0)).send(self.leave_phrases[random.randint(0, len(self.leave_phrases) - 1)].replace("[member]", member.mention))

    async def greetings(self, message, args):
        if args:
            if self.marcel.is_admin(message):
                if args[0] == "here":
                    self.marcel.set_setting(message.guild, 'greetings_channel', message.channel.id)
                    self.marcel.set_setting(message.guild, 'greetings', True)
                    await message.channel.send("Greetings are now enabled and will be sent to this channel.")
    
                elif args[0] == "off":
                    self.marcel.set_setting(message.guild, 'greetings', False)
                    await message.channel.send("Greetings are now disabled.")
                
                else:
                    await message.channel.send("Wrong request. Type `" + self.marcel.get_setting(message.guild, 'prefix', self.marcel.default_settings['prefix']) + 'help greetings`.')
    
            else:
                await message.channel.send("Only administrators have access to this command.")

        else:
            if self.is_greeting_enabled(message.guild):
                await message.channel.send("Greetings are enabled.")
            else:
                await message.channel.send("Greetings are disabled.")