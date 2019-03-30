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
            "on_server_join": [],
            "on_server_remove": [],
        }
        
        self.temp_folder = os.path.join(bot_folder, "temp")
        self.resources_folder = os.path.join(bot_folder, "resources")
        self.settings_folder = os.path.join(bot_folder, "settings")
        self.plugins_folder = os.path.join(bot_folder, "plugins")

        if not os.path.exists(self.temp_folder):
            os.makedirs(self.temp_folder)

        if not os.path.exists(self.resources_folder):
            os.makedirs(self.resources_folder)

        if not os.path.exists(self.settings_folder):
            os.makedirs(self.settings_folder)

        
        self.bot = discord.Client()

        self.bot.event(self.on_ready)
        self.bot.event(self.on_message)
        self.bot.event(self.on_member_join)
        self.bot.event(self.on_member_remove)
        self.bot.event(self.on_server_join)
        self.bot.event(self.on_server_remove)
        self.bot.event(self.on_reaction_add)
        self.bot.event(self.on_reaction_remove)

        self.plugin_list = []
        for filename in os.listdir(self.plugins_folder):
            if filename.endswith('.py'):
                self.plugin_list.append(os.path.join(self.plugins_folder, filename))
        
        if self.verbose : print(self.plugin_list)

        self.plugins = {}
        self.commands = {}

        for plugin in self.plugin_list:
            loader = machinery.SourceFileLoader('MarcelPlugin', plugin)
            module = types.ModuleType(loader.name)
            loader.exec_module(module)
            
            for command in module.MarcelPlugin.bot_commands:
                self.commands[command] = module.MarcelPlugin.plugin_name

            self.plugins[module.MarcelPlugin.plugin_name] = module.MarcelPlugin(self)

        if self.verbose : print(self.plugins)
        if self.verbose : print(self.commands)    

        self.load_settings()

        print(str(len(self.plugins)) + " plugins loaded.\n" + str(len(self.commands)) + " commands available.")
        
        self.bot.run(bot_token)


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
                if self.verbose : print('Loading : ' + str(fullpath))
                file_handle = open(fullpath, 'r')
                file_content = file_handle.read()
                file_handle.close()

                json_content = json.loads(file_content)
                self.all_settings[json_content['server_id']] = json_content

    def write_settings(self, server_id):
        filepath = os.path.join(self.settings_folder, str(server_id) + '.json')
        json_content = json.dumps(self.all_settings[server_id])
        if self.verbose : print('Write to : ' + str(filepath))
        file_handle = open(filepath, 'w')
        file_handle.write(json_content)
        file_handle.close()
        

    def set_setting(self, server, setting, value):
        self.all_settings[server.id][setting] = value
        self.write_settings(server.id)
        if self.verbose : print("Set : " + setting + " = " + str(value))

    def get_setting(self, server, setting, default):
        if not server.id in self.all_settings:
            self.all_settings[server.id] = self.default_settings
            self.set_setting(server, 'server_id', str(server.id))
            if self.verbose : print("Created default settings for " + str(server.id))

        if not setting in self.all_settings[server.id] : self.set_setting(server, setting, default)

        return self.all_settings[server.id][setting]


    def is_admin(self, message):
        return message.author.server_permissions.administrator
    
    def is_moderator(self, message):
        # for now considers users with the manage_messages permission to be moderators
        return message.author.server_permissions.manage_messages

    def is_me(self, message):
        return message.author == self.bot.user


    async def change_presence(self, text, url=None, ptype=0):
        await self.bot.change_presence(game=discord.Game(name=text, url=url, type=ptype))



    def is_voice_client_initialized(self, server):
        return server.id in self.voice_clients

    def initialize_voice_client(self, server):
        if not self.is_voice_client_initialized(server):
            self.voice_clients[server.id] = MarcelVoiceClient(marcel=self, server=server)

    async def voice_client_join(self, message):
        self.initialize_voice_client(message.server)
        await self.voice_clients[message.server.id].join_voice_channel(message.channel, message.author)

    async def voice_client_leave(self, message):
        self.initialize_voice_client(message.server)
        await self.voice_clients[message.server.id].leave_voice_channel(message.channel, message.author)

    async def voice_client_play(self, message, request, silent=False, use_ytdl=True):
        self.initialize_voice_client(message.server)
        if not self.voice_clients[message.server.id].is_in_voice_channel():
            await self.voice_client_join(message)

        if self.voice_clients[message.server.id].is_in_voice_channel():
            await self.voice_clients[message.server.id].play_media(message.channel, request, silent, use_ytdl)

    async def voice_client_stop(self, message, silent=False):
        self.initialize_voice_client(message.server)        
        await self.voice_clients[message.server.id].stop_media(message.channel, silent)

    async def voice_client_skip(self, message, silent=False):
        self.initialize_voice_client(message.server)
        if not self.voice_clients[message.server.id].is_in_voice_channel():
            await self.voice_client_join(message)

        await self.voice_clients[message.server.id].skip(message.channel, False, silent)
    
    async def voice_client_pause(self, message):
        self.initialize_voice_client(message.server)
        await self.voice_clients[message.server.id].pause_media(message.channel)

    async def voice_client_resume(self, message):
        self.initialize_voice_client(message.server)
        await self.voice_clients[message.server.id].resume_media(message.channel)
    
    async def voice_client_queue_add(self, message, request):
        self.initialize_voice_client(message.server)        
        await self.voice_clients[message.server.id].player_queue_add(message.channel, request)
    
    async def voice_client_queue_clear(self, message):
        self.initialize_voice_client(message.server)
        await self.voice_clients[message.server.id].player_queue_clear(message.channel)

    async def voice_client_volume(self, message, volume):
        self.initialize_voice_client(message.server)
        await self.voice_clients[message.server.id].set_volume(volume / 100)



    async def on_message(self, message):
        if not (self.is_me(message) or message.channel.is_private):
            prefix = self.get_setting(message.server, 'prefix', self.default_settings['prefix'])
            if message.content.startswith(prefix):
                if self.get_setting(message.server, 'command_cleanup', self.default_settings['command_cleanup']) == True : await self.bot.delete_message(message)
                # is a command, supposedly
                split_message = message.content.split(' ')
                
                command = split_message[0][len(prefix):] # trim prefix length

                if command in self.commands:
                    args = []
                    if len(split_message) > 1:
                        args = split_message
                        del args[0] # remove command from arguments

                    func = getattr(self.plugins[self.commands[command]], command)
                    await func(message, args)
                else:
                    await self.bot.send_message(message.channel, "I know of no command such as : ```" + split_message[0] + "```")

        for method in self.event_triggers['on_message']:
            print(method)
            print("Running function " + method['plugin'])
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(message)

    async def on_ready(self):
        print('Bot logged in as:')
        print(self.bot.user.name)
        print(self.bot.user.id)
        print('-----')
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

    async def on_server_join(self, server):
        for method in self.event_triggers['on_server_join']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(server)

    async def on_server_remove(self, server):
        for method in self.event_triggers['on_server_remove']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(server)




class MarcelVoiceClient:

    def __init__(self, marcel, server):
        self.marcel = marcel
        self.server = server
        self.voice_client = None
        self.autoplay = False
        self.last_channel = None
        self.player = None
        self.player_busy = False
        self.player_info = {}
        self.player_volume = 1.0
        self.player_queue = []

    def autoplay_trigger(self):
        self.player_info = {}
        if self.autoplay:
            self.marcel.bot.loop.create_task(self.skip(self.last_channel, True))

    def is_in_voice_channel(self):
        if self.voice_client:
            return self.voice_client.is_connected()

        return False
    
    def ytdl_fetch(self, request, ytdl_options={'default_search': 'auto', 'quiet': True, 'noplaylist': True}):
        try:
            with youtube_dl.YoutubeDL(ytdl_options) as ydl:
                return ydl.extract_info(url=request, download=False)
        except Exception as e:
            return {'404': True, 'error': str(e)}

    def ytdl_to_playerinfo(self, request):
        try:
            ytdl_fetched = self.ytdl_fetch(request)
            ytdl_info = {}

            if 'entries' in ytdl_fetched:
                ytdl_info = ytdl_fetched['entries'][0]
            elif '404' in ytdl_fetched:
                return {'404': True}
            else:
                ytdl_info = ytdl_fetched

            playerinfo = {
                "title": ytdl_info['title'],
                "author": ytdl_info['uploader'],
                "thumbnail": "",
                "url": ytdl_info['webpage_url'],
                "404": False,
            }

            if 'thumbnail' in ytdl_info:
                playerinfo["thumbnail"] = ytdl_info['thumbnail']

            return playerinfo

        except Exception as e:
            print('ytdl_to_playerinfo: ' + str(e) + '\nrequest=')
            print(request)
            return {}
    
    def get_embed_from_playerinfo(self, title, color, playerinfo):
        embed=discord.Embed(title=playerinfo['title'], description="by " + playerinfo['author'], url=playerinfo['url'], color=color)
        embed.set_author(name=title)
        embed.set_thumbnail(url=playerinfo['thumbnail'])
        return embed

    async def join_voice_channel(self, channel, author):
        try:
            user_voice_channel = author.voice.voice_channel

            if user_voice_channel:
                if self.voice_client:
                    if self.voice_client.channel == user_voice_channel:
                        await self.marcel.bot.send_message(channel, "I'm sorry Dave. I'm afraid I cannot duplicate myself.")

                    else:
                        await self.voice_client.move_to(user_voice_channel)
                        await self.marcel.bot.send_message(channel, "I moved over to `" + self.voice_client.channel.name + "`.")

                else:
                    await self.marcel.bot.join_voice_channel(user_voice_channel)
                    self.voice_client = self.marcel.bot.voice_client_in(self.server)
                    await self.marcel.bot.send_message(channel, 'Joined `' + self.voice_client.channel.name + '`.')

            else:
                await self.marcel.bot.send_message(channel, 'You must join a voice channel first.')

        except Exception as e:
            await self.marcel.bot.send_message(channel, 'join_voice_channel: ```' + str(e) + '```')

    async def leave_voice_channel(self, channel, author):
        try:
            if self.is_in_voice_channel:
                if not self.player == None:
                    self.autoplay = False
                    if self.player.is_playing() : self.player.stop()

                voice_channel_name = self.voice_client.channel.name

                await self.voice_client.disconnect()
                self.voice_client = None
                self.player_info = {}
                self.player_busy = False
                await self.marcel.bot.send_message(channel, 'Left `' + voice_channel_name + '`')

            else:
                await self.marcel.bot.send_message(channel, "I'm sorry Dave. I'm afraid I wasn't connected to a voice channel.")

        except Exception as e:
            await self.marcel.bot.send_message(channel, 'leave_voice_channel: ```' + str(e) + '```')

    async def play_media(self, channel, request, silent=False, use_ytdl=True):
        if len(request) == 0:
            await self.marcel.bot.send_message(channel, "You can't play emptiness.")

        elif self.player_busy:
            await self.marcel.bot.send_message(channel, "The play requests are flowing too fast. I cannot process yours right now.")

        else:
            self.player_busy = True

            if not self.player == None:
                self.autoplay = False
                if self.player.is_playing() : self.player.stop()

            try:
                self.last_channel = channel

                if use_ytdl:
                    request_info = self.ytdl_to_playerinfo(request)
                    if request_info['404']:
                        if not silent : await self.marcel.bot.send_message(channel, "Unable to find results for:\n```\n" + request + "```")

                    else:
                        self.player_info = request_info
                        if self.marcel.verbose : print(request_info)

                        self.autoplay = True
                        self.player = await self.voice_client.create_ytdl_player(request_info['url'], ytdl_options={'default_search': 'auto', 'quiet': True, 'noplaylist': True}, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", after=self.autoplay_trigger)

                        if not silent : await self.marcel.bot.send_message(channel, embed=self.get_embed_from_playerinfo("Now playing", 0xff0000, request_info))

                else:
                    self.player = self.voice_client.create_ffmpeg_player(request)
                    if not silent : await self.marcel.bot.send_message(channel, 'Now playing `' + self.player.title + '`')

                if not self.player == None:
                    self.player.volume = self.player_volume
                    self.player.start()
                
            except Exception as e:
                await self.marcel.bot.send_message(channel, 'play_media: ```' + str(e) + '```')
            
            self.player_busy = False
    
    async def skip(self, channel, autoplay, silent=False, use_ytdl=True):
        if len(self.player_queue) == 0:
            await self.marcel.bot.send_message(channel, "There is nothing left to play.")
        else:
            await self.play_media(channel, self.player_queue[0]['url'], silent, use_ytdl)
            del self.player_queue[0]

    async def stop_media(self, channel, silent=False):
        if self.player == None:
            if not silent : await self.marcel.bot.send_message(channel, "Nothing is playing.")
        else:
            if self.player.is_playing():
                title = ""
                try:
                    title = self.player.title
                except:
                    pass
                
                self.autoplay = False
                self.player.stop()
                if not silent : await self.marcel.bot.send_message(channel, "Stopped playing `" + title + "`.")
                self.player_info = {}

            else:
                if not silent : await self.marcel.bot.send_message(channel, "Nothing is playing.")

    async def pause_media(self, channel, silent=False):
        if self.player == None:
            if not silent : await self.marcel.bot.send_message(channel, "Nothing is playing.")
        else:
            if self.player.is_playing():
                try:
                    self.player.pause()
                    if not silent : await self.marcel.bot.send_message(channel, "Paused `" + self.player.title + "`.")

                except Exception as e:
                    await self.marcel.bot.send_message(channel, "pause_media: ```" + str(e) + "```")

            else:
                if not silent : await self.marcel.bot.send_message(channel, "Nothing is playing.")

    async def resume_media(self, channel, silent=False):
        if self.player == None:
            if not silent : await self.marcel.bot.send_message(channel, "Nothing is playing.")
        else:
            try:
                self.player.resume()
                if not silent : await self.marcel.bot.send_message(channel, "Resumed playing `" + self.player.title + "`.")

            except Exception as e:
                await self.marcel.bot.send_message(channel, "pause_media: ```" + str(e) + "```")
    
    async def player_queue_add(self, channel, request):
        playerinfo = self.ytdl_to_playerinfo(request)
        if playerinfo['404']:
            await self.marcel.bot.send_message(channel, "Unable to find results for:\n```\n" + request + "```")
        else:
            self.player_queue.append(playerinfo)
            await self.marcel.bot.send_message(channel, embed=self.get_embed_from_playerinfo("Song added to the player queue", 0x00ff23, playerinfo))

    async def player_queue_clear(self, channel):
        self.player_queue.clear()
        await self.marcel.bot.send_message(channel, "Player queue was cleared.")
    
    async def set_volume(self, volume):
        self.player_volume = round(volume, 2)
        if not self.player == None:
            self.player.volume = self.player_volume

