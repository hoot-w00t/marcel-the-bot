from typing import Union
from datetime import timedelta
from discord.ext import tasks
from marcel.util import embed_message
import asyncio
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

        if isinstance(duration, int):
            self.duration = duration
        else:
            try:
                self.duration = int(duration)

            except:
                self.duration = 0

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
            embed.set_footer(text=str(timedelta(seconds=self.duration)).split(".")[0].strip())

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

        self.loop = asyncio.get_event_loop()

        self.reset_timeout()

    @tasks.loop(seconds=15)
    async def timeout_loop(self):
        if self.is_in_voice_channel():
            current_time = time.time()

            if self.is_media_playing():
                if current_time - self.last_action > self.timeout_playing:
                    logging.info("Playing Timeout reached for guild: {}".format(self.guild.id))
                    await self.leave_voice_channel(timed_out=True)
                    self.timeout_loop.stop()

            else:
                if current_time - self.last_action > self.timeout_idle:
                    logging.info("Idle Timeout reached for guild: {}".format(self.guild.id))
                    await self.leave_voice_channel(timed_out=True)
                    self.timeout_loop.stop()

        else:
            self.timeout_loop.stop()

    @timeout_loop.after_loop
    async def after_timeout_loop(self):
        logging.info("timeout_loop ended for guild: {}".format(
            self.guild.id
        ))

        if self.is_in_voice_channel():
            logging.error("timeout_loop ended for guild: {}: but voice client is still connected, trying to start it back".format(
                self.guild.id
            ))
            self.timeout_loop.start()

    def after_callback(self, error):
        """Callback after a media has finished playing"""

        logging.info("after_callback for guild: {}".format(self.guild.id))
        if error:
            logging.error("after_callback error for guild: {}: {}".format(self.guild.id, error))

        if self.autoplay:
            self.loop.create_task(self.skip(autoplay=True))

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

    async def ytdl_fetch(
        self,
        request: str,
        as_playerinfo: bool = False,
        parse_all_entries: bool = False,
        with_playlists: bool = False):
        """Fetch information about a given request using youtube-dl
        request: can either be a link or a text search
        Returns either a list or a PlayerInfo if as_playerinfo is True"""

        try:
            ytdl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
                "simulate": True,
                "skip_download": True,
                "playlistend": self.player_queue_limit,
                "restrictfilenames": True,
                "nocheckcertificate": True,
                "ignoreerrors": False,
                "logtostderr": False,
                "quiet": True,
                "no_warnings": True,
                "default_search": "auto",
                "source_address": "0.0.0.0"
            }

            if not with_playlists:
                ytdl_opts["noplaylist"] = True

            with youtube_dl.YoutubeDL(params=ytdl_opts) as ytdl:
                await self.loop.run_in_executor(None, ytdl.cache.remove)
                info = await self.loop.run_in_executor(None, lambda: ytdl.extract_info(url=request, download=False))

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
                        "I'm sorry Dave, I'm afraid I cannot duplicate myself",
                        discord.Color.dark_red()
                    )
                )

            else:
                self.reset_timeout()
                await self.voice_client.move_to(voice_channel)

                await self.previous_channel.send(
                    embed=embed_message(
                        "I moved over to",
                        discord.Color.green(),
                        voice_channel.name
                    )
                )

        else:
            try:
                self.reset_timeout()
                self.voice_client = await voice_channel.connect(timeout=10, reconnect=False)

                try:
                    self.timeout_loop.start()

                except:
                    pass

                await self.previous_channel.send(
                    embed=embed_message(
                        "Joined voice channel",
                        discord.Color.green(),
                        message=self.voice_client.channel.name
                    )
                )

            except Exception as e:
                logging.error("Unable to join voice channel for guild: {}: {}".format(
                    self.guild.id,
                    e
                ))
                await self.previous_channel.send(
                    embed=embed_message(
                        "I cannot join voice channel",
                        discord.Color.dark_red(),
                        message=voice_channel.name
                    )
                )

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
                if self.is_media_playing() or self.is_media_paused():
                    self.autoplay = False
                    self.voice_client.stop()

                name = self.voice_client.channel.name

                await self.voice_client.disconnect()

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
                        "I'm sorry Dave, I'm afraid I wasn't connected to a voice channel",
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

        pinfos = None
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
                pinfos = await self.ytdl_fetch(
                    request,
                    as_playerinfo=True,
                    parse_all_entries=True,
                    with_playlists=True
                )

            if isinstance(pinfos, PlayerInfo):
                pinfos = [pinfos] if pinfos.found else list()

            if len(pinfos) == 0:
                if not silent:
                    await self.previous_channel.send(
                        embed=embed_message(
                            "No results for",
                            discord.Color.dark_red(),
                            message=request
                        )
                    )
                return

            pinfo = pinfos[0]

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

            # Trigger callback as if media had been played to skip to the next
            self.autoplay = autoplay
            self.after_callback(None)
            return

        self.player_busy = True # lock player
        try:
            if self.is_media_playing():
                # Always disable autplay before stopping to prevent the callback to play something else
                self.autoplay = False
                self.voice_client.stop()

            self.player_info = pinfo

            self.reset_timeout()
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

        if isinstance(pinfos, list):
            if len(pinfos) > 1:
                await self.player_queue_add(
                    pinfos[1:],
                    channel=None,
                    silent=silent
                )

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

            if autoplay:
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
        if self.is_media_playing() or self.is_media_paused():
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

        elif self.is_media_paused():
            if not silent:
                await self.previous_channel.send(
                    embed=self.player_info.get_embed(
                        "Already paused",
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

        elif self.is_media_playing():
            if not silent:
                await self.previous_channel.send(
                    embed=self.player_info.get_embed(
                        "Already playing",
                        discord.Color.dark_red()
                    )
                )

        else:
            if not silent:
                await self.send_nothing_playing()

    async def player_queue_add(self, request: Union[str, list, PlayerInfo], channel: discord.TextChannel = None, silent: bool = False):
        """Add PlayerInfo or PlayerInfo list or request results (including playlists) to the player queue"""

        self.set_previous_channel(channel)

        if isinstance(request, PlayerInfo):
            pinfos = [request]

        else:
            if len(request) == 0:
                if not silent:
                    await self.previous_channel.send(
                        embed=embed_message(
                            "I cannot add nothing to the player queue",
                            discord.Color.dark_red()
                        )
                    )
                return

            if isinstance(request, list):
                pinfos = request

            else:
                async with self.previous_channel.typing():
                    pinfos = await self.ytdl_fetch(
                        request,
                        as_playerinfo=True,
                        parse_all_entries=True,
                        with_playlists=True
                    )

                if isinstance(pinfos, PlayerInfo):
                    pinfos = [pinfos] if pinfos.found else list()

        if len(pinfos) == 0:
            if not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "No results for",
                        discord.Color.dark_red(),
                        request
                    )
                )
            return

        if len(self.player_queue) >= self.player_queue_limit:
            if not silent:
                await self.previous_channel.send(
                    embed=embed_message(
                        "Cannot add more than {} songs to the player queue".format(
                            self.player_queue_limit
                        ),
                        discord.Color.gold()
                    )
                )
            return

        added = 0
        playlist_embed = discord.Embed(color=discord.Color.green())
        for pinfo in pinfos:
            self.player_queue.append(pinfo)

            if added == 0:
                playlist_embed.title = pinfo.title
                playlist_embed.description = pinfo.author
                playlist_embed.url = pinfo.url
                if pinfo.thumbnail:
                    playlist_embed.set_thumbnail(url=pinfo.thumbnail)

            elif added <= 19:
                playlist_embed.add_field(
                    name=pinfo.title,
                    value=pinfo.author,
                    inline=False
                )

            added += 1

            if len(self.player_queue) >= self.player_queue_limit:
                if not silent and len(pinfos) > added:
                    await self.previous_channel.send(
                        embed=embed_message(
                            "Discarded {} songs because the player queue is full".format(
                                len(pinfos) - added
                            ),
                            discord.Color.dark_red()
                        )
                    )
                break

        if added > 19:
            remaining = added - 19
            playlist_embed.add_field(
                name="...",
                value="+ {} song{}".format(
                    remaining,
                    "s" if remaining != 1 else ""
                ),
                inline=False
            )

        if added == 1:
            playlist_embed.set_author(name="Song added to the player queue")

        else:
            playlist_embed.set_author(name="Added {} songs to the player queue".format(
                added
            ))

        if not silent:
            await self.previous_channel.send(embed=playlist_embed)

    async def player_queue_clear(self, channel: discord.TextChannel, silent: bool = False):
        """Clear player queue"""

        self.set_previous_channel(channel)

        self.player_queue.clear()

        if not silent:
            await self.previous_channel.send(
                embed=embed_message(
                    "Player queue was cleared",
                    discord.Color.dark_blue()
                )
            )

    def player_queue_set_limit(self, limit: int) -> None:
        """Set the player queue limit"""

        if limit <= 0:
            return

        self.player_queue_limit = limit

        while len(self.player_queue) > self.player_queue_limit:
            self.player_queue.pop()

    def set_volume(self, volume: float) -> None:
        """Set player volume"""

        volume = round(volume, 2)
        if volume > self.player_volume_limit:
            volume = self.player_volume_limit

        self.player_volume = volume
        if self.is_media_playing() or self.is_media_paused():
            self.voice_client.source.volume = self.player_volume

    def set_volume_limit(self, volume: float) -> None:
        """Set volume limit"""

        self.player_volume_limit = round(volume, 2)
        self.apply_volume_limit()

    def apply_volume_limit(self) -> None:
        """Make sure that the volume limit is respected"""

        if self.player_volume > self.player_volume_limit:
            self.set_volume(self.player_volume_limit)