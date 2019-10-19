from discord import Embed
from json import load as json_load
from os.path import isfile, join
import unicodedata

class MarcelPlugin:

    """
        Music plugin for Marcel the Discord Bot
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

    plugin_name = "Music Player"
    plugin_description = "Default Music Player to listen to music."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `join` or `leave` to join the voice channel you are in / leave the one I am in.
    `play` [request] plays the requested link (supports these: https://rg3.github.io/youtube-dl/supportedsites.html), or searches the request on YouTube. (Playlists are not supported yet)
    `stop`, `pause` and `resume` do as they say on the media playing.
    `skip` skips to the next song in the player queue (if any).
    `add` [request] add a request to the player queue.
    `search` [request] searches for your request. You can later add it to the player queue using `add`.
    `clear` clears the player queue.
    `queue` displays the player queue.
    `playing` displays what's currently playing.
    `volume` [0 - 200] sets the volume (in %).

    **The following command is only for administrators/moderators.**
    `max_volume` [0 - 200] sets a maximum volume value (default is 100%), to prevent bleeding ears.

    You can also play some radios with `radio` [name of the radio] (supports autocompletion).
    """
    bot_commands = [
        'join',
        'leave',
        'play',
        'stop',
        'skip',
        'pause',
        'resume',
        'add',
        'search',
        'clear',
        'queue',
        'volume',
        'playing',
        'radio',
        'max_volume',
    ]

    def __init__(self, marcel):
        self.marcel = marcel

        self.radio_config_file = join(self.marcel.resources_folder, "radio.json")
        self.radio_list = []

        if isfile(self.radio_config_file):
            try:
                with open(self.radio_config_file, 'r') as h:
                    self.radio_config = json_load(h)

                for radio in self.radio_config:
                    self.radio_list.append(self.radio_config[radio]["name"])

            except Exception as e:
                self.marcel.print_log(f"[{self.plugin_name}] Could not load file: {self.radio_config_file}: {e}")

        else:
            self.marcel.print_log(f"[{self.plugin_name}] Radio configuration file does't exist or cannot be accessed: {self.radio_config_file}")

        if len(self.radio_list) == 0:
            self.plugin_help += "No radios available :confused:\n"

        else:
            self.plugin_help += f"**Radios available:** {', '.join(self.radio_list)}\n"

        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def join(self, message, args):
        await self.marcel.voice_client_join(message)

    async def leave(self, message, args):
        await self.marcel.voice_client_leave(message)

    async def play(self, message, args):
        if args:
            await self.marcel.voice_client_play(message, ' '.join(args).strip())

        else:
            await self.marcel.voice_client_skip(message)

    async def stop(self, message, args):
        await self.marcel.voice_client_stop(message)

    async def skip(self, message, args):
        await self.marcel.voice_client_skip(message)

    async def pause(self, message, args):
        await self.marcel.voice_client_pause(message)

    async def resume(self, message, args):
        await self.marcel.voice_client_resume(message)

    async def add(self, message, args):
        await self.marcel.voice_client_queue_add(message, ' '.join(args).strip())

    async def search(self, message, args):
        if args:
            await self.marcel.voice_client_search(message, ' '.join(args).strip())

        else:
            await message.channel.send("You can't search nothingness.")

    async def clear(self, message, args):
        await self.marcel.voice_client_queue_clear(message)

    async def queue(self, message, args):
        queue_embed=Embed(color=0x0050ff)
        queue_embed.set_author(name="Player queue")
        guild_id = f"{message.guild.id}"

        if guild_id in self.marcel.voice_clients:
            if len(self.marcel.voice_clients[guild_id].player_queue) > 0:
                for i in range(0, len(self.marcel.voice_clients[guild_id].player_queue)):
                    playerinfo = self.marcel.voice_clients[guild_id].player_queue[i]

                    if i == 0:
                        queue_embed.title = playerinfo['title']
                        queue_embed.description = playerinfo['author']
                        queue_embed.url = playerinfo['url']
                        queue_embed.set_thumbnail(url=playerinfo['thumbnail'])

                    else:
                        queue_embed.add_field(name=playerinfo['title'], value=playerinfo['author'], inline=False)

            else:
                queue_embed.title = "The player queue is empty."

        else:
            queue_embed.title = "The player queue is empty."

        await message.channel.send(embed=queue_embed)

    async def playing(self, message, args):
        queue_embed=Embed(color=0x0050ff)
        queue_embed.set_author(name="Currently playing")
        guild_id = f"{message.guild.id}"

        if guild_id in self.marcel.voice_clients:
            playerinfo = self.marcel.voice_clients[guild_id].player_info

            if 'title' in playerinfo:
                queue_embed.title = playerinfo['title']
                queue_embed.description = playerinfo['author']
                queue_embed.url = playerinfo['url']
                queue_embed.set_thumbnail(url=playerinfo['thumbnail'])

            else:
                queue_embed.title = "Nothing is playing at the moment."

        else:
            queue_embed.title = "Nothing is playing at the moment."

        await message.channel.send(embed=queue_embed)

    async def volume(self, message, args):
        guild_id = f"{message.guild.id}"

        if args:
            try:
                new_volume = round(float(args[0]) / 100, 2)
                max_volume = self.marcel.get_setting(message.guild, 'maximum_volume', self.marcel.default_settings['maximum_volume'])

                if max_volume >= new_volume >= 0:
                    await self.marcel.voice_client_volume(message, new_volume)
                    await message.channel.send(f"Volume changed to : **{new_volume * 100}%**.")

                else:
                    await message.channel.send(f"The volume cannot be less than **0%** and cannot exceed **{max_volume * 100}%**.")

            except:
                await message.channel.send("Incorrect volume value.")

        else:
            if guild_id in self.marcel.voice_clients:
                await message.channel.send(f"Current volume : **{self.marcel.voice_clients[guild_id].player_volume * 100}%**.")

    async def max_volume(self, message, args):
        if args:
            if self.marcel.is_admin(message) or self.marcel.is_moderator(message):
                try:
                    new_volume = round(float(args[0]) / 100, 2)
                    if 2 >= new_volume >= 0:
                        self.marcel.set_setting(message.guild, 'maximum_volume', new_volume)
                        await self.marcel.voice_client_max_volume(message, new_volume)
                        await message.channel.send(f"Maximum volume changed to : **{new_volume * 100}%**.")

                    else:
                        await message.channel.send("The volume cannot be less than **0%** and cannot exceed **200%**.")

                except:
                    await message.channel.send("Incorrect volume value.")

            else:
                await message.channel.send("Only administrators and moderators can change the maximum volume value.")

        else:
            await message.channel.send(f"Maximum volume is at : **{self.marcel.get_setting(message.guild, 'maximum_volume', self.marcel.default_settings['maximum_volume']) * 100}%**.")

    def remove_accents(self, input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    async def radio(self, message, args):
        if len(args) == 0:
            await message.channel.send(f"**Radios available:** {', '.join(self.radio_list)}")

        else:
            requested_radio = self.remove_accents(' '.join(args).lower()).strip()

            for radio in self.radio_config:
                if radio.lower().strip().startswith(requested_radio):
                    requested_radio = radio
                    break

            if requested_radio in self.radio_config:
                playerinfo = {
                    "title": self.radio_config[requested_radio]["name"],
                    "author": "Internet Radio",
                    "thumbnail": "",
                    "url": self.radio_config[requested_radio]["website"],
                    "playback_url": self.radio_config[requested_radio]["playback"],
                    "404": False,
                }

                if not self.radio_config[requested_radio]["thumbnail"] == None:
                    playerinfo["thumbnail"] = self.radio_config[requested_radio]["thumbnail"]

                await self.marcel.voice_client_play(message, playerinfo["playback_url"], silent=False, use_ytdl=False, autoplay=False, player_info=playerinfo)

            else:
                await message.channel.send(f"Radio `{requested_radio}` doesn't exist.")