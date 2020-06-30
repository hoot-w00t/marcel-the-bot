from typing import Union
from datetime import timedelta
from discord.ext import tasks
from marcel.util import embed_message
import discord
import time
import youtube_dl
import logging

"""
    Marcel the Discord Bot
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

class PlayerInfo:
    def __init__(
        self,
        title: str = None,
        author: str = None,
        thumbnail: str = None,
        duration: int = 0,
        url: str = None,
        playback_url: str = None,
        found: bool = False):
        """Media player information"""
        self.title = title
        self.author = author
        self.thumbnail = thumbnail
        self.duration = duration
        self.url = url
        self.playback_url = playback_url
        self.found = found

    def clear(self) -> None:
        self.title = None
        self.author = None
        self.thumbnail = None
        self.duration = 0
        self.url = None
        self.playback_url = None
        self.found = False

    def is_http(self) -> bool:
        if self.playback_url:
            if self.playback_url.startswith("http://") or self.playback_url.startswith("https://"):
                return True

        return False

    def get_embed(self, title: str, color: discord.Color, show_duration: bool = True) -> discord.Embed:
        """Create a discord.Embed to display PlayerInfo information"""

        embed = discord.Embed(
            title=self.title if self.title else "[untitled]",
            description="by {}".format(self.author if self.author else "[unknown]"),
            url=self.url if self.url else "",
            color=color
        )

        embed.set_author(name=title)
        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)

        if show_duration and self.duration > 0:
            embed.set_footer(text=str(timedelta(seconds=self.duration)))

        return embed

class MarcelMediaPlayer:
    def __init__(
        self,
        guild: discord.Guild,
        volume: float = 1.0,
        volume_limit: float = 1.25,
        player_queue_limit: int = 20,
        duration_limit: int = 1800,
        timeout_idle: int = 1800,
        timeout_playing: int = 7200):
        """Marcel media player
        guild: discord.Guild() to which the media player belongs to
        volume: volume value (1.0 represents 100%)
        volume_limit: maximum volume value (1.0 represents 125%)
        player_queue_limit: maximum size of the player queue
        duration_limit: maximum requested media duration (in seconds)
        timeout_idle: seconds of idle before timing out
        timeout_playing: seconds of idle while playing a media before timing out"""
        self.guild = guild
        self.player_volume = volume
        self.player_volume_limit = volume_limit
        self.player_queue_limit = player_queue_limit
        self.duration_limit = duration_limit
        self.timeout_idle = timeout_idle
        self.timeout_playing = timeout_playing

        self.voice_client = None
        self.autoplay = False
        self.previous_channel = None
        self.player_busy = False
        self.player_info = PlayerInfo()
        self.player_queue = list()

        self.ytdl = youtube_dl.YoutubeDL({
            "format": "bestaudio/best",
            "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
            "restrictfilenames": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0"
        })

        self.reset_timeout()

    @tasks.loop(seconds=15)
    async def timeout_loop(self):
        current_time = time.time()

        if self.is_media_playing():
            if current_time - self.last_action > self.timeout_playing:
                logging.info("Playing Timeout reached for guild: {}".format(self.guild.id))
                await self.leave_voice_channel(timed_out=True)

        else:
            if current_time - self.last_action > self.timeout_idle:
                logging.info("Idle Timeout reached for guild: {}".format(self.guild.id))
                await self.leave_voice_channel(timed_out=True)

    def reset_timeout(self):
        self.last_action = time.time()

    def set_previous_channel(self, channel: discord.TextChannel):
        """Set previous_channel if needed"""

        if channel:
            self.previous_channel = channel

    def is_in_voice_channel(self):
        """Return True if voice client is connected to a voice channel"""

        return self.voice_client.is_connected() if isinstance(self.voice_client, discord.VoiceClient) else False

    def is_media_playing(self):
        """Return True if media is currently playing"""

        return self.voice_client.is_playing() if self.is_in_voice_channel() else False

    def is_media_paused(self):
        """Return True if media is currently paused"""

        return self.voice_client.is_paused() if self.is_in_voice_channel() else False

    def ytdl_entry_to_playerinfo(self, entry: dict):
        """Parse Youtube-DL entry into PlayerInfo"""

        return PlayerInfo(
            title=entry.get("title"),
            author=entry.get("uploader"),
            thumbnail=entry.get("thumbnail"),
            duration=entry.get("duration"),
            url=entry.get("webpage_url"),
            playback_url=entry.get("url"),
            found=True if entry.get("url") else False
        )

    def ytdl_fetch(
        self,
        request: str,
        as_playerinfo: bool = False,
        parse_all_entries: bool = False):
        """Fetch information about a given request using youtube-dl
        request: can either be a link or a text search
        Returns either a list or a PlayerInfo if as_playerinfo is True"""

        try:
            info = self.ytdl.extract_info(url=request, download=False)

            if as_playerinfo:
                entries = info.get("entries", [info])

                if len(entries) == 0:
                    return PlayerInfo()
                elif parse_all_entries:
                    return [self.ytdl_entry_to_playerinfo(x) for x in entries]
                else:
                    return self.ytdl_entry_to_playerinfo(entries[0])

            else:
                return info

        except Exception as e:
            logging.error("ytdl_fetch: {}".format(e))
            return PlayerInfo() if as_playerinfo else dict()

    def after_callback(self, error):
        """Callback after a media has finished playing"""

        logging.info("After callback for guild: {}".format(self.guild.id))
        if error:
            logging.error("Play callback error for guild: {}: {}".format(self.guild.id, error))

        if self.autoplay:
            self.voice_client.loop.create_task(self.skip(autoplay=True))

    async def send_nothing_playing(self):
        """Send a nothing is playing message to the previous channel"""

        await self.previous_channel.send(
            embed=embed_message(
                "Nothing is playing",
                discord.Color.blue()
                )
            )

    async def join_voice_channel(self, voice_channel: discord.VoiceChannel):
        """Join or move to a voice channel"""

        if self.is_in_voice_channel():
            if self.voice_client.channel == voice_channel:
                await self.previous_channel.send(
                    embed=embed_message(
                        "I'm sorry Dave. I'm afraid I cannot duplicate myself.",
                        discord.Color.dark_red()
                    )
                )

            else:
                await self.voice_client.move_to(voice_channel)

                self.reset_timeout()

                await self.previous_channel.send(
                    embed=embed_message(
                        "I moved over to",
                        discord.Color.green(),
                        voice_channel.name
                    )
                )

        else:
            try:
                self.voice_client = await voice_channel.connect(timeout=10, reconnect=False)

                self.timeout_loop.start()
                self.reset_timeout()

                await self.previous_channel.send(
                    embed=embed_message(
                        "Joined voice channel",
                        discord.Color.green(),
                        message=self.voice_client.channel.name
                    )
                )

            except:
                await self.previous_channel.send(
                    embed=embed_message(
                        "I cannot join voice channel",
                        discord.Color.dark_red(),
                        message=voice_channel.name
                    )
                )

        self.ytdl.cache.remove()

    async def join_member_voice_channel(self, member: discord.Member, channel: discord.TextChannel = None):
        """Join or move to the voice channel the member is in"""

        self.set_previous_channel(channel)

        try:
            if member.voice:
                await self.join_voice_channel(member.voice.channel)

            else:
                await self.previous_channel.send(
                    embed=embed_message(
                        "You must join a voice channel first",
                        discord.Color.dark_red()
                    )
                )

        except Exception as e:
            logging.error("join_voice_channel: {}".format(e))
            await self.previous_channel.send("Unexpected error:\n```{}```".format(e))

    async def leave_voice_channel(self, channel: discord.TextChannel = None, silent: bool = False, timed_out: bool = False):
        """Leave the connected voice channel"""

        self.set_previous_channel(channel)

        try:
            if self.is_in_voice_channel():
                if self.is_media_playing():
                    self.autoplay = False
                    self.voice_client.stop()

                name = self.voice_client.channel.name

                await self.voice_client.disconnect()
                self.timeout_loop.stop()

                if not silent:
                    await self.previous_channel.send(
                        embed=embed_message(
                            "Left voice channel{}".format(
                                " (due to inactivity)" if timed_out else ""
                            ),
                            discord.Color.red(),
                            name
                        )
                    )

            elif not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "I'm sorry Dave. I'm afraid I wasn't connected to a voice channel.",
                        discord.Color.red()
                    )
                )

            self.player_busy = False

        except Exception as e:
            logging.error("leave_voice_channel: {}".format(e))
            await self.previous_channel.send("Unexpected error:\n```{}```".format(e))

    async def play(
        self,
        request: Union[str, PlayerInfo],
        channel: discord.TextChannel = None,
        member: discord.Member = None,
        silent: bool = False,
        autoplay: bool = False,
        respect_duration_limit: bool = True):
        """Play a media
        If request is not a PlayerInfo, it youtube-dl to fetch information
        silent: If True no messages will be sent to the previous text channel
        autoplay: whether autoplay should be enabled
        respect_duration_limit: If False, ignore the media duration limit"""

        self.set_previous_channel(channel)

        if self.player_busy:
            await self.previous_channel.send(
                embed=embed_message(
                    "The play requests are flowing too fast! Skipping this one",
                    discord.Color.gold()
                )
            )
            return

        if isinstance(request, PlayerInfo):
            pinfo = request

        elif len(request) == 0:
            await self.previous_channel.send(
                embed=embed_message(
                    "You can't play emptiness",
                    discord.Color.dark_red()
                )
            )
            return

        else:
            async with self.previous_channel.typing():
                pinfo = self.ytdl_fetch(
                    request,as_playerinfo=True,
                    parse_all_entries=False
                )

            if not pinfo.found and not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "No results for",
                        discord.Color.dark_red(),
                        message=request
                    )
                )
                return

        if not self.is_in_voice_channel() and member:
            await self.join_member_voice_channel(member, self.previous_channel)

        if not self.is_in_voice_channel():
            await self.previous_channel.send(
                embed=embed_message(
                    "Cannot play media",
                    discord.Color.dark_red(),
                    message="Not connected to a voice channel"
                )
            )
            return

        if respect_duration_limit and pinfo.duration > self.duration_limit:
            await self.previous_channel.send(
                embed=pinfo.get_embed(
                    "Cannot play medias that last more than {} minutes".format(int(self.duration_limit / 60)),
                    discord.Color.gold()
                )
            )
            return

        self.player_busy = True # lock player
        try:
            if self.is_media_playing():
                # Always disable autplay before stopping to prevent the callback to play something else
                self.autoplay = False
                self.voice_client.stop()

            self.player_info = pinfo

            player = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    pinfo.playback_url,
                    options="-vn",
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5" if pinfo.is_http() else ""
                ),
                volume=self.player_volume
            )

            self.voice_client.play(
                player,
                after=self.after_callback
            )

            self.reset_timeout()
            if not silent:
                await self.previous_channel.send(
                    embed=pinfo.get_embed(
                        "Now playing",
                        discord.Color.red()
                    )
                )

            self.autoplay = autoplay

        except Exception as e:
            logging.error("play: {}".format(e))
            await self.previous_channel.send("Unexpected error:\n```{}```".format(e))

        self.player_busy = False # unlock player

    async def skip(
        self,
        channel: discord.TextChannel = None,
        silent: bool = False,
        autoplay: bool = False,
        respect_duration_limit: bool = True):
        """Skip current media and play the next in queue"""

        self.set_previous_channel(channel)

        if len(self.player_queue) == 0:
            if not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "There is nothing left to play",
                        discord.Color.blue()
                    )
                )
            self.player_info.clear()

        else:
            await self.play(
                self.player_queue[0],
                channel=channel,
                member=None,
                silent=silent,
                autoplay=autoplay,
                respect_duration_limit=respect_duration_limit
            )
            del self.player_queue[0]

    async def stop(self, channel: discord.TextChannel = None, silent: bool = False):
        """Stop any currently playing media and disable autoplay"""

        self.set_previous_channel(channel)

        self.autoplay = False
        if self.is_media_playing():
            self.voice_client.stop()

            if not silent:
                await self.previous_channel.send(
                    embed=self.player_info.get_embed(
                        "Stopped playing",
                        discord.Color.dark_red()
                    )
                )
            self.player_info.clear()

        else:
            if not silent:
                await self.send_nothing_playing()

    async def pause(self, channel: discord.TextChannel = None, silent: bool = False):
        """Pause a playing media"""

        self.set_previous_channel(channel)

        if self.is_media_playing():
            self.voice_client.pause()
            self.reset_timeout()

            if not silent:
                await self.previous_channel.send(
                    embed=self.player_info.get_embed(
                        "Paused",
                        discord.Color.dark_blue()
                    )
                )

        else:
            if not silent:
                await self.send_nothing_playing()

    async def resume(self, channel: discord.TextChannel = None, silent: bool = False):
        """Resume a paused media"""

        self.set_previous_channel(channel)

        if self.is_media_paused():
            self.voice_client.resume()
            self.reset_timeout()

            if not silent:
                await self.previous_channel.send(
                    embed=self.player_info.get_embed(
                        "Resumed",
                        discord.Color.red()
                    )
                )

        else:
            if not silent:
                await self.send_nothing_playing()

    async def player_queue_add(self, request: Union[str, PlayerInfo], channel: discord.TextChannel = None, silent: bool = False):
        """Add media to the player queue"""

        self.set_previous_channel(channel)

        if len(self.player_queue) >= self.player_queue_limit:
            if not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "Cannot add more than {} songs to the player queue".format(self.player_queue_limit),
                        discord.Color.gold()
                    )
                )
            return

        if isinstance(request, PlayerInfo):
            pinfo = request
        elif len(request) == 0:
            if not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "I cannot add nothing to the player queue",
                        discord.Color.dark_red()
                    )
                )
            return

        else:
            async with self.previous_channel.typing():
                pinfo = self.ytdl_fetch(request, as_playerinfo=True)

        if not pinfo.found:
            if not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "No results for",
                        discord.Color.dark_red(),
                        request
                    )
                )
            return

        self.player_queue.append(pinfo)
        if not silent:
            await self.previous_channel.send(
                embed=pinfo.get_embed(
                    "Song added to the player queue",
                    discord.Color.green()
                )
            )

    async def player_queue_clear(self, channel: discord.TextChannel, silent: bool = False):
        """Clear player queue"""

        self.set_previous_channel(channel)

        self.player_queue.clear()

        if not silent:
            await self.previous_channel.send(
                embed=embed_message(
                    "Player queue was cleared.",
                    discord.Color.dark_blue()
                )
            )

    def set_volume(self, volume: float):
        """Set player volume"""

        volume = round(volume, 2)
        if volume > self.player_volume_limit:
            volume = self.player_volume_limit

        self.player_volume = volume
        if self.is_media_playing() or self.is_media_paused():
            self.voice_client.source.volume = self.player_volume

    def set_volume_limit(self, volume: float):
        """Set volume limit"""

        self.player_volume_limit = round(volume, 2)
        self.apply_volume_limit()

    def apply_volume_limit(self):
        """Make sure that the volume limit is respected"""

        if self.player_volume > self.player_volume_limit:
            self.set_volume(self.player_volume_limit)