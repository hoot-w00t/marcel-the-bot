from pathlib import Path
from importlib import machinery
import discord
import asyncio
import sys, os, types
import time, logging, random
import json, youtube_dl

class Marcel:

    def __init__(self, bot_token, bot_folder, logging=True, verbose=False):
        self.default_settings = {
            "prefix": "!!",
            "lang": "fr",
            "command_cleanup": False,
            "maximum_volume": 2.0,
        }

        self.verbose = verbose
        self.logging = logging
        self.all_settings = {}
        self.voice_clients = {}

        self.event_triggers = {
            "on_message": [],
            "on_ready": [],
            "on_reaction_add": [],
            "on_reaction_remove": [],
            "on_member_join": [],
            "on_member_remove": [],
            "on_guild_join": [],
            "on_guild_remove": [],
        }
        
        self.temp_folder = os.path.join(bot_folder, "temp")
        self.resources_folder = os.path.join(bot_folder, "resources")
        self.settings_folder = os.path.join(bot_folder, "settings")
        self.plugins_folder = os.path.join(bot_folder, "plugins")
        self.logs_folder = os.path.join(bot_folder, "logs")

        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

        if not os.path.exists(self.resources_folder):
            os.makedirs(self.resources_folder)

        if not os.path.exists(self.settings_folder):
            os.makedirs(self.settings_folder)
        
        if not os.path.exists(self.logs_folder):
            os.makedirs(self.logs_folder)

        if self.logging:
            file_date = time.strftime('%Y_%m_%d_%H_%M_%S')
            self.log_file = open(os.path.join(self.logs_folder, "marcel-" + str(file_date) + '.log'), "w")
            self.print_log("Log file started at : " + time.strftime('%c'))

        self.bot = discord.Client()

        self.bot.event(self.on_ready)
        self.bot.event(self.on_message)
        self.bot.event(self.on_member_join)
        self.bot.event(self.on_member_remove)
        self.bot.event(self.on_guild_join)
        self.bot.event(self.on_guild_remove)
        self.bot.event(self.on_reaction_add)
        self.bot.event(self.on_reaction_remove)

        self.plugin_list = []
        for filename in os.listdir(self.plugins_folder):
            if filename.endswith('.py'):
                self.plugin_list.append(os.path.join(self.plugins_folder, filename))

        self.plugins = {}
        self.commands = {}

        for plugin in self.plugin_list:
            loader = machinery.SourceFileLoader('MarcelPlugin', plugin)
            module = types.ModuleType(loader.name)
            loader.exec_module(module)
            
            for command in module.MarcelPlugin.bot_commands:
                self.commands[command] = module.MarcelPlugin.plugin_name

            self.plugins[module.MarcelPlugin.plugin_name] = module.MarcelPlugin(self)

        self.load_settings()

        self.print_log(str(len(self.plugins)) + " plugins loaded.\n" + str(len(self.commands)) + " commands available.")
        
        self.bot.run(bot_token)


    def print_log(self, obj):
        print( "[" + time.strftime("%Y-%m-%d %H:%M:%S") + "] " + str(obj))
        if self.logging:
            self.log_file.write("[" + time.strftime("%Y-%m-%d %H:%M:%S") + "]" + str(obj) + "\n")
            self.log_file.flush()

    def register_event(self, plugin, event_name, function_name):
        if event_name in self.event_triggers:
            self.event_triggers[event_name].append({
                "plugin": plugin.plugin_name,
                "method": function_name,
            })
            return True
        
        return False
    
    def unregister_event(self, plugin, event_name, function_name):
        if event_name in self.event_triggers:
            event_trigger = {
                "plugin": plugin.plugin_name,
                "method": function_name,
            }
            if event_trigger in self.event_triggers[event_name]:
                del self.event_triggers[event_name][event_trigger]
                return True

        return False

    def load_settings(self):
        for filename in os.listdir(self.settings_folder):
            if filename.endswith('.json'):
                fullpath = os.path.join(self.settings_folder, filename)
                if self.verbose : self.print_log('Loading settings file: ' + str(fullpath))
                file_handle = open(fullpath, 'r')
                file_content = file_handle.read()
                file_handle.close()

                json_content = json.loads(file_content)
                self.all_settings[json_content['server_id']] = json_content

    def write_settings(self, guild_id):
        filepath = os.path.join(self.settings_folder, str(guild_id) + '.json')
        json_content = json.dumps(self.all_settings[guild_id])
        if self.verbose : self.print_log('Write to : ' + str(filepath))
        file_handle = open(filepath, 'w')
        file_handle.write(json_content)
        file_handle.close()
        

    def set_setting(self, guild, setting, value):
        guild_id = str(guild.id)
        self.all_settings[guild_id][setting] = value
        self.write_settings(guild_id)
        if self.verbose : self.print_log("Set : " + setting + " = " + str(value))

    def get_setting(self, guild, setting, default):
        guild_id = str(guild.id)
        if not guild_id in self.all_settings:
            self.all_settings[guild_id] = self.default_settings
            self.set_setting(guild, 'server_id', guild_id)
            if self.verbose : self.print_log("Created default settings for " + guild_id)

        if not setting in self.all_settings[guild_id] : self.set_setting(guild, setting, default)

        return self.all_settings[guild_id][setting]


    def is_admin(self, message):
        return message.author.guild_permissions.administrator

    def is_moderator(self, message):
        return message.author.guild_permissions.manage_messages

    def is_me(self, message):
        return message.author == self.bot.user


    async def mute_member(self, member, guild):
        try:
            if guild.me.guild_permissions.mute_members:
                await member.edit(mute=True)
        except Exception:
            pass
    
    async def unmute_member(self, member, guild):
        try:
            if guild.me.guild_permissions.mute_members:
                await member.edit(mute=False)
        except Exception:
            pass

    async def deafen_member(self, member, guild):
        try:
            if guild.me.guild_permissions.deafen_members:
                await member.edit(deafen=True)
        except Exception:
            pass

    async def undeafen_member(self, member, guild):
        try:
            if guild.me.guild_permissions.deafen_members:
                await member.edit(deafen=False)
        except Exception:
            pass

    def is_voice_client_initialized(self, guild):
        return str(guild.id) in self.voice_clients

    def initialize_voice_client(self, guild):
        if not self.is_voice_client_initialized(guild):
            self.voice_clients[str(guild.id)] = MarcelVoiceClient(marcel=self, guild=guild, max_volume=self.get_setting(guild, 'maximum_volume', self.default_settings['maximum_volume']))

    async def voice_client_join(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[str(message.guild.id)].join_voice_channel(message.channel, message.author)

    async def voice_client_leave(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[str(message.guild.id)].leave_voice_channel(message.channel, message.author)

    async def voice_client_play(self, message, request, silent=False, use_ytdl=True):
        self.initialize_voice_client(message.guild)
        if not self.voice_clients[str(message.guild.id)].is_in_voice_channel():
            await self.voice_client_join(message)

        if self.voice_clients[str(message.guild.id)].is_in_voice_channel():
            await self.voice_clients[str(message.guild.id)].play_media(message.channel, request, silent, use_ytdl)

    async def voice_client_stop(self, message, silent=False):
        self.initialize_voice_client(message.guild)        
        await self.voice_clients[str(message.guild.id)].stop_media(message.channel, silent)

    async def voice_client_skip(self, message, silent=False):
        self.initialize_voice_client(message.guild)
        if not self.voice_clients[str(message.guild.id)].is_in_voice_channel():
            await self.voice_client_join(message)

        await self.voice_clients[str(message.guild.id)].skip(message.channel, False, silent)
    
    async def voice_client_pause(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[str(message.guild.id)].pause_media(message.channel)

    async def voice_client_resume(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[str(message.guild.id)].resume_media(message.channel)
    
    async def voice_client_search(self, message, request, silent=False):
        self.initialize_voice_client(message.guild)        
        await self.voice_clients[str(message.guild.id)].player_search_ytdl(message.channel, request, silent)

    async def voice_client_queue_add(self, message, request):
        self.initialize_voice_client(message.guild)        
        await self.voice_clients[str(message.guild.id)].player_queue_add(message.channel, request)
    
    async def voice_client_queue_clear(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[str(message.guild.id)].player_queue_clear(message.channel)

    async def voice_client_volume(self, message, volume):
        self.initialize_voice_client(message.guild)
        self.voice_clients[str(message.guild.id)].set_volume(volume)
    
    async def voice_client_max_volume(self, message, volume):
        self.initialize_voice_client(message.guild)
        self.voice_clients[str(message.guild.id)].set_max_volume(volume)





    async def on_message(self, message):
        if not (self.is_me(message) or not isinstance(message.channel, discord.abc.GuildChannel)):
            prefix = self.get_setting(message.guild, 'prefix', self.default_settings['prefix'])
            if message.content.startswith(prefix):
                # is a command
                if self.get_setting(message.guild, 'command_cleanup', self.default_settings['command_cleanup']) == True:
                    if message.guild.me.guild_permissions.manage_messages:
                        await message.delete()
                    else:
                        await message.channel.send("I need the `Manages messages` permission in order to achieve my command cleanup mission.")

                split_message = message.content.split(' ')
                command = split_message[0][len(prefix):] # remove prefix

                if command in self.commands:
                    args = []
                    if len(split_message) > 1:
                        args = split_message
                        del args[0] # remove command from arguments

                    func = getattr(self.plugins[self.commands[command]], command)
                    await func(message, args)
                else:
                    # replace() and the space before we close the code line is to prevent escaping with a backslash and a code line
                    await message.channel.send("I know of no command such as : `" + split_message[0].replace('`', '') + " `.\nUse `" + prefix + "help` if you are lost.")

        for method in self.event_triggers['on_message']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(message)

    async def on_ready(self):
        self.print_log('Bot logged in as:')
        self.print_log(self.bot.user.name)
        self.print_log(self.bot.user.id)
        self.print_log('-----')
        for method in self.event_triggers['on_ready']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func()


    async def on_reaction_add(self, reaction, user):
        for method in self.event_triggers['on_reaction_add']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(reaction, user)

    async def on_reaction_remove(self, reaction, user):
        for method in self.event_triggers['on_reaction_remove']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(reaction, user)

    async def on_member_join(self, member):
        for method in self.event_triggers['on_member_join']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(member)

    async def on_member_remove(self, member):
        for method in self.event_triggers['on_member_remove']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(member)

    async def on_guild_join(self, guild):
        for method in self.event_triggers['on_guild_join']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(guild)

    async def on_guild_remove(self, guild):
        for method in self.event_triggers['on_guild_remove']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(guild)



class MarcelVoiceClient:

    def __init__(self, marcel, guild, max_volume=2.0):
        self.marcel = marcel
        self.guild = guild
        self.voice_client = None
        self.autoplay = False
        self.last_channel = None

        self.player_busy = False

        self.player_info = {}
        self.player_last_search = None

        self.player_volume = 1.0
        self.player_max_volume = max_volume
        self.respect_max_volume()

        self.player_queue = []

        self.max_duration = 900

        self.ytdl = youtube_dl.YoutubeDL({
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
        })

    def autoplay_trigger(self, error):
        if self.marcel.verbose : self.marcel.print_log("Autoplay triggered for " + str(self.guild.id) + ".")
        self.player_info = {}
        if self.autoplay:
            self.marcel.bot.loop.create_task(self.skip(self.last_channel, True))

    def is_in_voice_channel(self):
        if not self.voice_client == None:
            return self.voice_client.is_connected()

        return False

    def is_media_playing(self):
        if self.is_in_voice_channel():
            return self.voice_client.is_playing()
        
        return False

    def ytdl_fetch(self, request):
        try:
            return self.ytdl.extract_info(url=request, download=False)

        except Exception as e:
            return {'404': True, 'error': ''}

    def ytdl_to_playerinfo(self, request, limit_duration=True):
        try:
            ytdl_fetched = self.ytdl_fetch(request)
            ytdl_info = {}

            if 'entries' in ytdl_fetched:
                ytdl_info = ytdl_fetched['entries'][0]
            elif '404' in ytdl_fetched:
                return {'404': True, 'error': ytdl_fetched['error']}
            else:
                ytdl_info = ytdl_fetched

            if limit_duration and ytdl_info['duration'] > self.max_duration : return {'404': True, 'error': "You cannot play medias that last more than " + str(round(self.max_duration / 60)) + " minutes."}

            playerinfo = {
                "title": ytdl_info['title'],
                "author": ytdl_info['uploader'],
                "thumbnail": "",
                "url": ytdl_info['webpage_url'],
                "playback_url": ytdl_info['url'],
                "404": False,
            }

            if 'thumbnail' in ytdl_info:
                playerinfo["thumbnail"] = ytdl_info['thumbnail']

            return playerinfo

        except Exception as e:
            self.marcel.print_log('ytdl_to_playerinfo: ' + str(e) + '\nrequest=')
            self.marcel.print_log(request)
            return {'404': True, 'error': str(e)}
    
    def get_embed_from_playerinfo(self, title, color, playerinfo):
        embed = discord.Embed(title=playerinfo['title'], description="by " + playerinfo['author'], url=playerinfo['url'], color=color)
        embed.set_author(name=title)
        embed.set_thumbnail(url=playerinfo['thumbnail'])
        return embed
    
    def embed_message(self, message, color):
        embed = discord.Embed(color=color)
        embed.set_author(name=message)
        return embed

    async def join_voice_channel(self, channel, member):
        try:
            if member.voice:
                if self.is_in_voice_channel():
                    if self.voice_client.channel == member.voice.channel:
                        await channel.send(embed=self.embed_message("I'm sorry Dave. I'm afraid I cannot duplicate myself.", 0xff0000))

                    else:
                        await self.voice_client.move_to(member.voice.channel)
                        await channel.send(embed=self.embed_message("I moved over to `" + member.voice.channel.name + "`.", 0x00ff23))

                else:
                    self.voice_client = await member.voice.channel.connect()
                    await channel.send(embed=self.embed_message('Joined `' + self.voice_client.channel.name + '`.', 0x00ff23))

            else:
                await channel.send(embed=self.embed_message('You must join a voice channel first.', 0xff0000))

        except Exception as e:
            await channel.send('join_voice_channel: ```' + str(e) + '```')

    async def leave_voice_channel(self, channel, member):
        try:
            if self.is_in_voice_channel():
                if self.is_media_playing():
                    self.autoplay = False
                    self.voice_client.stop()

                voice_channel_name = self.voice_client.channel.name

                await self.voice_client.disconnect()
                self.voice_client = None
                self.player_info = {}
                self.player_busy = False

                await channel.send(embed=self.embed_message('Left `' + voice_channel_name + '`', 0xff0000))

            else:
                await channel.send(embed=self.embed_message("I'm sorry Dave. I'm afraid I wasn't connected to a voice channel.", 0xff0000))
                self.voice_client = None
                self.player_info = {}
                self.player_busy = False

        except Exception as e:
            await channel.send('leave_voice_channel: ```' + str(e) + '```')

    async def play_media(self, channel, request, silent=False, use_ytdl=True):
        if len(request) == 0:
            await channel.send(embed=self.embed_message("You can't play emptiness", 0xff0000))

        elif self.player_busy:
            await channel.send(embed=self.embed_message("The play requests are flowing too fast, I cannot process yours right now.", 0xff0000))

        else:
            self.player_busy = True

            try:
                self.last_channel = channel
                if self.is_media_playing():
                    self.autoplay = False
                    self.voice_client.stop()

                if use_ytdl:
                    async with channel.typing():
                        request_info = self.ytdl_to_playerinfo(request)

                    if request_info['404']:
                        if not silent : await channel.send("Unable to find results for: `" + request + "`\n" + request_info['error'])

                    else:
                        self.player_info = request_info
                        if self.marcel.verbose : self.marcel.print_log(request_info)

                        self.autoplay = True

                        player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.player_info['playback_url'], options='-vn', before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume=self.player_volume)
                        self.voice_client.play(player, after=self.autoplay_trigger)


                        if not silent : await channel.send(embed=self.get_embed_from_playerinfo("Now playing", 0xff0000, request_info))

                else:
                    # create a playerinfo for this, somehow
                    player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(request, options='-vn'), volume=self.player_volume)
                    self.voice_client.play(player, after=self.autoplay_trigger)
                    if not silent : await channel.send('Now playing `' + request + '`')
                
            except Exception as e:
                await channel.send('play_media: ```' + str(e) + '```')
            
            self.player_busy = False
    
    async def skip(self, channel, autoplay, silent=False, use_ytdl=True):
        if len(self.player_queue) == 0:
            await channel.send(embed=self.embed_message("There is nothing left to play", 0x0050ff))
        else:
            await self.play_media(channel, self.player_queue[0]['url'], silent, use_ytdl)
            del self.player_queue[0]

    async def stop_media(self, channel, silent=False):
        if self.is_media_playing():
            title = "[untitled]"
            try:
                title = self.player_info['title']
            except:
                print('Oopsie, error at stop_media for title')
            
            self.autoplay = False
            self.voice_client.stop()
            if not silent : await channel.send(embed=self.embed_message("Stopped playing `" + title + "`.", 0xff0000))
            self.player_info = {}

        else:
            if not silent : await channel.send(embed=self.embed_message("Nothing is playing", 0x0050ff))

    async def pause_media(self, channel, silent=False):
        if self.is_media_playing():
            try:
                self.voice_client.pause()
                if not silent : await channel.send(embed=self.embed_message("Paused `" + self.player_info['title'] + "`.", 0x0050ff))

            except Exception as e:
                await channel.send("pause_media: ```" + str(e) + "```")

        else:
            if not silent : await channel.send(embed=self.embed_message("Nothing is playing", 0x0050ff))

    async def resume_media(self, channel, silent=False):
        try:
            self.voice_client.resume()
            if not silent : await channel.send(embed=self.embed_message("Resumed playing `" + self.player_info['title'] + "`.", 0x0050ff))

        except Exception as e:
            await channel.send("resume_media: ```" + str(e) + "```")
    
    async def player_search_ytdl(self, channel, request, silent=False):
        async with channel.typing():
            playerinfo = self.ytdl_to_playerinfo(request)

        if playerinfo['404']:
            self.player_last_search = None
            if not silent : await channel.send("Unable to find results for: `" + request + "`\n" + playerinfo['error'])
        else:
            self.player_last_search = playerinfo
            if not silent : await channel.send(embed=self.get_embed_from_playerinfo("Search result", 0x0050ff, playerinfo))


    async def player_queue_add(self, channel, request):
        if len(request) == 0:
            if self.player_last_search == None:
                await channel.send(embed=self.embed_message("I cannot add nothing to the player queue", 0x0050ff))
            else:
                self.player_queue.append(self.player_last_search)
                await channel.send(embed=self.get_embed_from_playerinfo("Song added to the player queue", 0x00ff23, self.player_last_search))

        else:
            async with channel.typing():
                playerinfo = self.ytdl_to_playerinfo(request)

            if playerinfo['404']:
                await channel.send("Unable to find results for: `" + request + "`\n" + playerinfo['error'])
            else:
                self.player_queue.append(playerinfo)
                await channel.send(embed=self.get_embed_from_playerinfo("Song added to the player queue", 0x00ff23, playerinfo))

    async def player_queue_clear(self, channel):
        self.player_queue.clear()
        await channel.send(embed=self.embed_message("Player queue was cleared.", 0x0050ff))
    
    def set_volume(self, volume):
        if volume <= self.player_max_volume:
            self.player_volume = round(volume, 2)
        else:
            self.player_volume = self.player_max_volume

        if self.is_media_playing():
            self.voice_client.source.volume = self.player_volume

        if self.marcel.verbose : self.marcel.print_log("Volume: " + str(self.player_volume))

    def set_max_volume(self, volume):
        self.player_max_volume = round(volume, 2)
        self.respect_max_volume()
        if self.marcel.verbose : self.marcel.print_log("Max volume: " + str(self.player_max_volume))

    def respect_max_volume(self):
        if self.player_volume > self.player_max_volume:
            self.set_volume(self.player_max_volume)