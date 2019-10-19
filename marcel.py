#!/usr/bin/python3

"""
    Marcel the Discord Bot
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

from pathlib import Path
from importlib import machinery
from discord.ext import tasks
from discord.abc import GuildChannel
from discord import Client, Embed, PCMVolumeTransformer, FFmpegPCMAudio
from os.path import join, exists
from os import makedirs, listdir
import types
import time
import youtube_dl
from json import dump as json_dump
from json import load as json_load

class Marcel:

    def __init__(self, config_path, logging=False, verbose=False, measure_time=False, statistics=False):
        try:
            with open(args.configuration_path, 'r') as h:
                config = json_load(h)

            bot_folder = config.get("folder")
            bot_token = config.get("token")
            self.default_settings = config.get("default_server_settings")

        except Exception as e:
            print(f"Could not load configuration file: {args.configuration_path}: {e}")
            exit(1)

        if measure_time : start_time = time.time()

        self.verbose = verbose
        self.statistics = statistics
        self.measure_time = measure_time
        self.logging = logging
        self.all_settings = {}

        self.voice_client_timeout = 1800 # seconds == 30 mins, when idle leave voice channel after this time
        self.voice_client_timeout_extended = 7200 # seconds == 2h, when media is playing stay longer before deciding it timeouts
        self.voice_clients = {}
        self.voice_client_timeout_loop.start()

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

        self.temp_folder = join(bot_folder, "temp")
        self.resources_folder = join(bot_folder, "resources")
        self.settings_folder = join(bot_folder, "settings")
        self.plugins_folder = join(bot_folder, "plugins")
        self.logs_folder = join(bot_folder, "logs")

        if not exists(self.temp_folder):
            makedirs(self.temp_folder)

        if not exists(self.resources_folder):
            makedirs(self.resources_folder)

        if not exists(self.settings_folder):
            makedirs(self.settings_folder)

        if not exists(self.logs_folder):
            makedirs(self.logs_folder)

        if self.logging:
            file_date = time.strftime('%Y_%m_%d_%H_%M_%S')
            self.log_file = open(join(self.logs_folder, f"marcel-{file_date}.log"), "w")
            self.print_log(f"Log file started at: {time.strftime('%c')}")

        if self.statistics:
            self.statistics_file = join(bot_folder, "statistics.json")

            if exists(self.statistics_file):
                try:
                    with open(self.statistics_file, 'r') as h:
                        self.all_statistics = json_load(h)

                except Exception as e:
                    self.print_log(f"Could not load statistics file: {self.statistics_file}: {e}")

            else:
                self.all_statistics = {
                    "collecting_since": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "guilds": {}
                }
                self.save_statistics()

            self.print_log("Statistics are enabled and will be collected.")

        self.bot = Client()

        self.bot.event(self.on_ready)
        self.bot.event(self.on_message)
        self.bot.event(self.on_member_join)
        self.bot.event(self.on_member_remove)
        self.bot.event(self.on_guild_join)
        self.bot.event(self.on_guild_remove)
        self.bot.event(self.on_reaction_add)
        self.bot.event(self.on_reaction_remove)

        self.plugin_list = []
        for filename in listdir(self.plugins_folder):
            if filename.endswith('.py'):
                self.plugin_list.append(join(self.plugins_folder, filename))

        self.plugins = {}
        self.commands = {}

        for plugin in self.plugin_list:
            loader = machinery.SourceFileLoader('MarcelPlugin', plugin)
            module = types.ModuleType(loader.name)
            loader.exec_module(module)

            for command in module.MarcelPlugin.bot_commands:
                if command in self.commands:
                    self.print_log(f'Command conflict: "{command}" from plugin "{module.MarcelPlugin.plugin_name}". This one will not be loaded.')

                else:
                    self.commands[command] = module.MarcelPlugin.plugin_name

            self.plugins[module.MarcelPlugin.plugin_name] = module.MarcelPlugin(self)

        self.load_settings()

        self.print_log(f"{len(self.plugins)} plugins loaded.")
        self.print_log(f"{len(self.commands)} commands available.")

        if measure_time:
            stop_time = time.time()
            self.print_log(f"Initialization took: {stop_time - start_time} seconds")

        self.bot.run(bot_token)


    def print_log(self, obj):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {obj}"
        print(line)
        if self.logging:
            self.log_file.write(f"{line}\n")
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
        for filename in listdir(self.settings_folder):
            if filename.endswith('.json'):
                fullpath = join(self.settings_folder, filename)

                try:
                    if self.verbose : self.print_log(f"Loading settings file: {fullpath}")
                    with open(fullpath, 'r') as h:
                        json_content = json_load(h)
                        self.all_settings[json_content['server_id']] = json_content

                except Exception as e:
                    self.print_log(f"Error loading settings file: {fullpath}: {e}")

    def write_settings(self, guild_id):
        filepath = join(self.settings_folder, f"{guild_id}.json")

        try:
            if self.verbose : self.print_log(f"Writing settings file: {filepath}")

            with open(filepath, 'w') as h:
                json_dump(self.all_settings[guild_id], h, indent=4)

        except Exception as e:
            self.print_log(f"Error writing settings file: {filepath}: {e}")

    def ensure_settings_exists(self, guild):
        guild_id = f"{guild.id}"
        if not guild_id in self.all_settings:
            self.all_settings[guild_id] = self.default_settings
            self.all_settings[guild_id]['server_id'] = guild_id
            self.write_settings(guild_id)

            if self.verbose : self.print_log(f"Created default settings for: {guild_id}")

    def set_setting(self, guild, setting, value):
        self.ensure_settings_exists(guild)

        guild_id = f"{guild.id}"
        self.all_settings[guild_id][setting] = value
        self.write_settings(guild_id)
        if self.verbose : self.print_log(f"Set: {setting} = {value}")

    def get_setting(self, guild, setting, default):
        self.ensure_settings_exists(guild)

        guild_id = f"{guild.id}"
        if not setting in self.all_settings[guild_id] : self.set_setting(guild, setting, default)

        return self.all_settings[guild_id][setting]

    def save_statistics(self):
        with open(self.statistics_file, 'w') as h:
            json_dump(self.all_statistics, h, indent=4)

    def get_statistic(self, statistic, guild, item=None):
        if self.statistics:
            guild_id = f"{guild.id}"
            if not guild_id in self.all_statistics["guilds"]:
                    self.all_statistics["guilds"][guild_id] = {}
                    self.all_statistics["guilds"][guild_id]["collecting_since"] = time.strftime('%Y-%m-%d %H:%M:%S')

            if not statistic in self.all_statistics["guilds"][guild_id]:
                self.all_statistics["guilds"][guild_id][statistic] = {}

            if item == None:
                return self.all_statistics["guilds"][guild_id][statistic]
            
            else:
                if item in self.all_statistics["guilds"][guild_id][statistic]:
                    return self.all_statistics["guilds"][guild_id][statistic][item]

        return None

    def get_global_statistic(self, statistic):
        if self.statistics:
            global_statistic = {}
            for guild_id in self.all_statistics["guilds"]:
                if not statistic in self.all_statistics["guilds"][guild_id]:
                    self.all_statistics["guilds"][guild_id][statistic] = {}

                return self.all_statistics["guilds"][guild_id][statistic]

        return None

    def insert_statistic(self, statistic, guild, item, value=None, increment=True):
        if self.statistics:
            guild_id = f"{guild.id}"
            if not guild_id in self.all_statistics["guilds"]:
                    self.all_statistics["guilds"][guild_id] = {}
                    self.all_statistics["guilds"][guild_id]["collecting_since"] = time.strftime('%Y-%m-%d %H:%M:%S')

            if not statistic in self.all_statistics["guilds"][guild_id]:
                self.all_statistics["guilds"][guild_id][statistic] = {}

            if not item in self.all_statistics["guilds"][guild_id][statistic]:
                self.all_statistics["guilds"][guild_id][statistic][item] = 0

            if value == None:
                if increment:
                    self.all_statistics["guilds"][guild_id][statistic][item] += 1

                else:
                    self.all_statistics["guilds"][guild_id][statistic][item] -= 1

            else:
                self.all_statistics["guilds"][guild_id][statistic][item] = value

            self.save_statistics()

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



    @tasks.loop(seconds=60)
    async def voice_client_timeout_loop(self):
        for voice_client_id in self.voice_clients:
            try:
                voice_client = self.voice_clients[voice_client_id]

                if voice_client.is_media_playing():
                    if time.time() - voice_client.last_action > self.voice_client_timeout_extended:
                        if voice_client.is_in_voice_channel():
                            await voice_client.leave_voice_channel(None, True)

                else:
                    if time.time() - voice_client.last_action > self.voice_client_timeout:
                        if voice_client.is_in_voice_channel():
                            await voice_client.leave_voice_channel(None, True)

            except Exception as e:
                self.print_log(f"timeout_loop error: {e}")

    def is_voice_client_initialized(self, guild):
        return f"{guild.id}" in self.voice_clients

    def initialize_voice_client(self, guild):
        if not self.is_voice_client_initialized(guild):
            self.voice_clients[f"{guild.id}"] = MarcelVoiceClient(marcel=self, guild=guild, max_volume=self.get_setting(guild, 'maximum_volume', self.default_settings['maximum_volume']))

    async def voice_client_join(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].join_voice_channel(message.channel, message.author)

    async def voice_client_leave(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].leave_voice_channel(message.channel)

    async def voice_client_play(self, message, request, silent=False, use_ytdl=True, autoplay=True, player_info=None):
        self.initialize_voice_client(message.guild)
        if not self.voice_clients[f"{message.guild.id}"].is_in_voice_channel():
            await self.voice_client_join(message)

        if self.voice_clients[f"{message.guild.id}"].is_in_voice_channel():
            await self.voice_clients[f"{message.guild.id}"].play_media(message.channel, request, silent, use_ytdl, autoplay, player_info)

    async def voice_client_stop(self, message, silent=False):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].stop_media(message.channel, silent)

    async def voice_client_skip(self, message, silent=False):
        self.initialize_voice_client(message.guild)
        if not self.voice_clients[f"{message.guild.id}"].is_in_voice_channel():
            await self.voice_client_join(message)

        await self.voice_clients[f"{message.guild.id}"].skip(message.channel, False, silent)

    async def voice_client_pause(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].pause_media(message.channel)

    async def voice_client_resume(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].resume_media(message.channel)

    async def voice_client_search(self, message, request, silent=False):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].player_search_ytdl(message.channel, request, silent)

    async def voice_client_queue_add(self, message, request):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].player_queue_add(message.channel, request)

    async def voice_client_queue_clear(self, message):
        self.initialize_voice_client(message.guild)
        await self.voice_clients[f"{message.guild.id}"].player_queue_clear(message.channel)

    async def voice_client_volume(self, message, volume):
        self.initialize_voice_client(message.guild)
        self.voice_clients[f"{message.guild.id}"].set_volume(volume)

    async def voice_client_max_volume(self, message, volume):
        self.initialize_voice_client(message.guild)
        self.voice_clients[f"{message.guild.id}"].set_max_volume(volume)



    async def on_message(self, message):
        if not (self.is_me(message) or not isinstance(message.channel, GuildChannel)):
            prefix = self.get_setting(message.guild, 'prefix', self.default_settings['prefix'])
            if message.content.startswith(prefix):
                # is a command
                if self.get_setting(message.guild, 'command_cleanup', self.default_settings['command_cleanup']) == True:
                    if message.guild.me.guild_permissions.manage_messages:
                        await message.delete()

                    else:
                        await message.channel.send("I need the `Manages messages` permission in order to achieve my command cleanup mission.")

                if message.author.id in self.get_setting(message.guild, 'denied_users', []) and not self.is_admin(message):
                    await message.channel.send("You are not allowed to use the bot.")

                else:
                    split_message = message.content.split(' ')
                    command = split_message[0][len(prefix):] # remove prefix

                    if command in self.commands:
                        if self.statistics:
                            self.insert_statistic("commands", message.guild, command)

                        args = []
                        if len(split_message) > 1:
                            args = split_message
                            del args[0] # remove command from arguments

                        if self.measure_time : start_time = time.time()

                        func = getattr(self.plugins[self.commands[command]], command)
                        await func(message, args)

                        if self.measure_time:
                            stop_time = time.time()
                            self.print_log(f"Command: {command}: took a total of {stop_time - start_time} seconds")

                    else:
                        # replace() and the space before we close the code line is to prevent escaping with a backslash and a code line
                        await message.channel.send(f"I know of no command such as : `{split_message[0].replace('`', '')}`.\nUse `{prefix}help` if you are lost.")

        for method in self.event_triggers['on_message']:
            func = getattr(self.plugins[method['plugin']], method['method'])
            await func(message)

    async def on_ready(self):
        self.print_log(f"Bot logged in as: {self.bot.user.name} ({self.bot.user.id})")

        guild_list = []
        for guild in self.bot.guilds:
            guild_list.append(guild.name)

        self.print_log(f"Bot is in {len(guild_list)} servers: {', '.join(guild_list)}")

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

    def __init__(self, marcel, guild, max_volume=1, player_queue_limit=10):
        self.marcel = marcel
        self.guild = guild
        self.voice_client = None
        self.autoplay = False
        self.last_channel = None

        self.player_busy = False

        self.player_info = {}
        self.player_last_search = None

        if max_volume >= 0.5:
            self.default_volume = max_volume / 4

        else:
            self.default_volume = 0.25

        self.player_volume = self.default_volume
        self.player_max_volume = max_volume
        self.respect_max_volume()

        self.player_queue_limit = player_queue_limit
        self.player_queue = []

        self.max_duration = 1200

        self.last_action = time.time()

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
        if self.marcel.verbose : self.marcel.print_log(f"Autoplay triggered for {self.guild.id}.")

        self.player_info = {}
        if self.autoplay:
            self.marcel.bot.loop.create_task(self.skip(self.last_channel, True))

    def is_in_voice_channel(self):
        try:
            if not self.voice_client == None:
                return self.voice_client.is_connected()
        except:
            pass

        return False

    def is_media_playing(self):
        if self.is_in_voice_channel():
            return self.voice_client.is_playing()

        return False

    def is_media_paused(self):
        if self.is_in_voice_channel():
            return self.voice_client.is_paused()

        return False

    def ytdl_fetch(self, request):
        try:
            return self.ytdl.extract_info(url=request, download=False)

        except Exception as e:
            return {'404': True, 'error': f"{e}"}

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

            if limit_duration and ytdl_info['duration'] > self.max_duration : return {'404': True, 'error': f"You cannot play medias that last more than {round(self.max_duration / 60)} minutes."}

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
            self.marcel.print_log(f'ytdl_to_playerinfo: {e}\nrequest=')
            self.marcel.print_log(request)
            return {'404': True, 'error': f"{e}"}

    def get_embed_from_playerinfo(self, title, color, playerinfo):
        embed = Embed(title=playerinfo['title'], description=f"by {playerinfo['author']}", url=playerinfo['url'], color=color)
        embed.set_author(name=title)
        embed.set_thumbnail(url=playerinfo['thumbnail'])
        return embed

    def embed_message(self, message, color):
        embed = Embed(color=color)
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

                        self.last_action = time.time()
                        self.last_channel = channel

                        await channel.send(embed=self.embed_message(f"I moved over to: {member.voice.channel.name}", 0x00ff23))

                else:
                    try:
                        self.voice_client = await member.voice.channel.connect(timeout=5, reconnect=False)

                        self.last_action = time.time()
                        self.last_channel = channel
                        if self.player_volume > self.default_volume:
                            self.set_volume(self.default_volume)

                        await channel.send(embed=self.embed_message(f'Joined: {self.voice_client.channel.name}', 0x00ff23))

                    except:
                        await channel.send(embed=self.embed_message(f"I cannot join: {member.voice.channel}", 0xff0000))

            else:
                await channel.send(embed=self.embed_message('You must join a voice channel first.', 0xff0000))

        except Exception as e:
            await channel.send(f'join_voice_channel: ```{e}```')

    async def leave_voice_channel(self, channel, timeout=False):
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

                if timeout:
                    await self.last_channel.send(embed=self.embed_message(f'Left voice channel due to inactivity: {voice_channel_name}', 0xff0000))

                else:
                    await channel.send(embed=self.embed_message(f'Left: {voice_channel_name}', 0xff0000))

            else:
                await channel.send(embed=self.embed_message("I'm sorry Dave. I'm afraid I wasn't connected to a voice channel.", 0xff0000))
                self.voice_client = None
                self.player_info = {}
                self.player_busy = False

        except Exception as e:
            await channel.send(f'leave_voice_channel: ```{e}```')

    async def play_media(self, channel, request, silent=False, use_ytdl=True, autoplay=True, player_info=None):
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
                        if not silent : await channel.send(f"Unable to find results for: `{request}`\n{request_info['error']}")

                    else:
                        self.player_info = request_info

                        self.autoplay = autoplay
                        player = PCMVolumeTransformer(FFmpegPCMAudio(self.player_info['playback_url'], options='-vn', before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume=self.player_volume)
                        self.voice_client.play(player, after=self.autoplay_trigger)

                        self.last_action = time.time()
                        if not silent : await channel.send(embed=self.get_embed_from_playerinfo("Now playing", 0xff0000, request_info))

                else:
                    self.autoplay = autoplay
                    player = PCMVolumeTransformer(FFmpegPCMAudio(request, options='-vn'), volume=self.player_volume)
                    self.voice_client.play(player, after=self.autoplay_trigger)
                    self.last_action = time.time()

                    if player_info:
                        self.player_info = player_info
                        if not silent : await channel.send(embed=self.get_embed_from_playerinfo("Now playing", 0xff0000, player_info))

                    else:
                        if not silent : await channel.send(f'Now playing `{request}`')

            except Exception as e:
                await channel.send(f'play_media: ```{e}```')

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
                pass

            self.autoplay = False
            self.voice_client.stop()
            if not silent : await channel.send(embed=self.embed_message(f"Stopped playing: {title}.", 0xff0000))
            self.player_info = {}

        else:
            self.autoplay = False
            if not silent : await channel.send(embed=self.embed_message("Nothing is playing", 0x0050ff))

    async def pause_media(self, channel, silent=False):
        if self.is_media_playing():
            try:
                self.voice_client.pause()
                if not silent : await channel.send(embed=self.embed_message(f"Paused: {self.player_info['title']}", 0x0050ff))

            except Exception as e:
                await channel.send(f"pause_media: ```{e}```")

        else:
            if not silent : await channel.send(embed=self.embed_message("Nothing is playing", 0x0050ff))

    async def resume_media(self, channel, silent=False):
        if self.is_media_paused():
            try:
                self.voice_client.resume()
                self.last_action = time.time()
                if not silent : await channel.send(embed=self.embed_message(f"Resumed playing: {self.player_info['title']}", 0x0050ff))

            except Exception as e:
                await channel.send(f"resume_media: ```{e}```")

        else:
            if not silent : await channel.send(embed=self.embed_message("Nothing was playing", 0x0050ff))

    async def player_search_ytdl(self, channel, request, silent=False):
        async with channel.typing():
            playerinfo = self.ytdl_to_playerinfo(request)

        if playerinfo['404']:
            self.player_last_search = None
            if not silent : await channel.send(f"Unable to find results for: `{request}` : {playerinfo['error']}")
        else:
            self.player_last_search = playerinfo
            if not silent : await channel.send(embed=self.get_embed_from_playerinfo("Search result", 0x0050ff, playerinfo))


    async def player_queue_add(self, channel, request):
        if len(self.player_queue) >= self.player_queue_limit:
            await channel.send(embed=self.embed_message(f"Cannot add more than {self.player_queue_limit} songs to the player queue", 0x0050ff))

        else:
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
                    await channel.send(f"Unable to find results for: `{request}` : {playerinfo['error']}")

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

    def set_max_volume(self, volume):
        self.player_max_volume = round(volume, 2)
        self.respect_max_volume()

    def respect_max_volume(self):
        if self.player_volume > self.player_max_volume:
            self.set_volume(self.player_max_volume)



if __name__ == "__main__":
    from argparse import ArgumentParser

    arg_parser = ArgumentParser(description="Marcel the Discord Bot")
    arg_parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Display additional (verbose) information about the bot")
    arg_parser.add_argument("-t", "--time", dest="measure_time", action="store_true", help="Display the time that some functions take to diagnose a performance issue")
    arg_parser.add_argument("-s", "--statistics", dest="stats", action="store_true", help="Collect general statistics about the bot's usage (like which commands are used most)")
    arg_parser.add_argument("-n", "--no-logs", dest="no_logs", action="store_true", help="Disable logging to a file")
    arg_parser.add_argument("-c", "--config", dest="configuration_path", nargs="?", default='config.json', help="Path to the configuration file (default=config.json)")
    args = arg_parser.parse_args()

    marcel_the_bot = Marcel(
        config_path=args.configuration_path,
        logging=not args.no_logs,
        verbose=args.verbose,
        measure_time=args.measure_time,
        statistics=args.stats
        )