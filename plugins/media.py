from marcel import Marcel
from marcel.util import embed_message
import discord

class MarcelPlugin:
    """
        Media player plugin for Marcel the Discord Bot
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

    plugin_name = "Media player"
    plugin_description = "Bot Media player"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}join` joins the voice channel that you are in
    `{prefix}leave` leaves the voice channel that the bot is in.
    `{prefix}play` [request] plays the requested link (supports these: https://rg3.github.io/youtube-dl/supportedsites.html), or searches for the request on YouTube. Playlists are supported.
    `{prefix}stop`, `{prefix}pause` and `{prefix}resume` stop, pause or resume the playing media.
    `{prefix}skip` skips to the next song in the player queue (if any).
    `{prefix}add` [request] search for your request and add it to the player queue.
    `{prefix}shuffle` [request] is the same as play but will also shuffle playlists. If no request is given, shuffle the player queue.
    `{prefix}search` [request] searches for your request.
    `{prefix}clear` clears the player queue.
    `{prefix}queue` displays the player queue.
    `{prefix}playing` displays what's currently playing.
    `{prefix}volume` [0 - limit] sets the volume or displays the current (`{prefix}vol` is an alias).

    **For server administrators:**
    `{prefix}volume-limit` [0 - 200] sets the upper volume limit or displays the current (`{prefix}vol-limit` is an alias)
    """

    bot_commands = [
        ("join", "join_cmd", "clean_command"),
        ("leave", "leave_cmd", "clean_command"),
        ("play", "play_cmd", "clean_command"),
        ("skip", "skip_cmd", "clean_command"),
        ("stop", "stop_cmd", "clean_command"),
        ("pause", "pause_cmd", "clean_command"),
        ("resume", "resume_cmd", "clean_command"),
        ("search", "search_cmd", "clean_command"),
        ("add", "add_cmd", "clean_command"),
        ("shuffle", "shuffle_cmd", "clean_command"),
        ("clear", "clear_cmd", "clean_command"),
        ("queue", "queue_cmd", "clean_command"),
        ("playing", "playing_cmd", "clean_command"),
        ("volume", "volume_cmd", "clean_command"),
        ("volume-limit", "volume_limit_cmd", "clean_command"),
        ("vol", "volume_cmd", "clean_command"),
        ("vol-limit", "volume_limit_cmd", "clean_command")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel
        self.marcel.register_event_handler(self, "on_voice_join", "deafen_on_join")

    async def deafen_on_join(self, channel: discord.VoiceChannel):
        mp = self.marcel.get_server_mediaplayer(channel.guild)
        await mp.change_voice_state(self_deaf=True)

    async def join_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.join_member_voice_channel(message.author, message.channel)

    async def leave_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.leave_voice_channel(message.channel)

    async def play_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")
        request = " ".join(args).strip()

        if len(request) > 0:
            await mp.play(
                request,
                channel=message.channel,
                member=message.author,
                autoplay=True
            )

        elif mp.is_media_paused():
            await mp.resume(channel=message.channel)

        else:
            await mp.skip(message.channel, autoplay=True)

    async def shuffle_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")
        request = " ".join(args).strip()

        if len(request) > 0:
            if mp.is_media_playing() or mp.is_media_paused():
                await mp.player_queue_add(
                    request,
                    channel=message.channel,
                    shuffle=True
                )

            else:
                await mp.play(
                    request,
                    channel=message.channel,
                    member=message.author,
                    autoplay=True,
                    shuffle=True
                )

        else:
            await mp.player_queue_shuffle(channel=message.channel)

    async def skip_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.skip(channel=message.channel, autoplay=True)

    async def stop_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.stop(channel=message.channel)

    async def pause_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.pause(channel=message.channel)

    async def resume_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.resume(channel=message.channel)

    async def search_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")
        request = " ".join(args).strip()

        if len(request) > 0:
            async with message.channel.typing():
                pinfo = await mp.ytdl_fetch(request, as_playerinfo=True)

            if pinfo.found:
                await message.channel.send(
                    embed=pinfo.get_embed(
                        "Search result",
                        discord.Color.green()
                    )
                )
            else:
                await message.channel.send(
                    embed=embed_message(
                        "No results for",
                        discord.Color.dark_red(),
                        message=request
                    )
                )

        else:
            await message.channel.send(
                embed=embed_message(
                    "You can't search nothingness",
                    discord.Color.dark_red()
                ),
                delete_after=kwargs.get("settings").get("delete_after")
            )

    async def add_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.player_queue_add(" ".join(args).strip(), channel=message.channel)

    async def clear_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        await mp.player_queue_clear(channel=message.channel)

    async def queue_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        queue_embed = discord.Embed(color=discord.Color.blue())
        added = 0
        queue_len = len(mp.player_queue)

        if queue_len == 0:
            queue_embed.set_author(name="Player queue")
            queue_embed.title = "The player queue is empty"

        else:
            queue_embed.set_author(name="Player queue ({} song{})".format(
                queue_len,
                "s" if queue_len != 1 else ""
            ))

            for media in mp.player_queue:
                if added == 0:
                    queue_embed.title = media.title
                    queue_embed.description = media.author
                    queue_embed.url = media.url
                    if media.thumbnail:
                        queue_embed.set_thumbnail(url=media.thumbnail)
                else:
                    queue_embed.add_field(
                        name=media.title,
                        value=media.author,
                        inline=False
                    )
                added += 1

                if added == 19 and queue_len > 19:
                    remaining = queue_len - added
                    queue_embed.add_field(
                        name="...",
                        value="+ {} song{}".format(
                            remaining,
                            "s" if remaining != 1 else ""
                        ),
                        inline=False
                    )
                    break

        await message.channel.send(embed=queue_embed)

    async def playing_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")

        if mp.player_info.found:
            await message.channel.send(
                embed=mp.player_info.get_embed(
                    "Currently playing",
                    discord.Color.blue()
                )
            )

        else:
            await message.channel.send(
                embed=embed_message(
                    "Nothing is playing",
                    discord.Color.blue()
                ),
                delete_after=kwargs.get("settings").get("delete_after")
            )

    async def volume_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")
        settings = kwargs.get("settings")
        request = " ".join(args).strip()

        if len(request) > 0:
            try:
                new_volume = round(float(request) / 100, 2)

                if mp.player_volume_limit >= new_volume >= 0:
                    mp.set_volume(new_volume)
                    settings["volume"] = mp.player_volume
                    await message.channel.send(
                        embed=embed_message(
                            "Volume is now set to",
                            discord.Color.blue(),
                            "{}%".format(mp.player_volume * 100)
                        ),
                        delete_after=settings.get("delete_after")
                    )

                else:
                    await message.channel.send(
                        embed=embed_message(
                            "Volume must be >= 0% and <= {}%".format(mp.player_volume_limit * 100),
                            discord.Color.red()
                        ),
                        delete_after=settings.get("delete_after")
                    )

            except:
                await message.channel.send(
                    embed=embed_message(
                        "Invalid volume",
                        discord.Color.red()
                    ),
                    delete_after=settings.get("delete_after")
                )

        else:
            await message.channel.send(
                embed=embed_message(
                    "Current volume",
                    discord.Color.blue(),
                    "{}%".format(mp.player_volume * 100)
                ),
                delete_after=settings.get("delete_after")
            )

    async def volume_limit_cmd(self, message: discord.Message, args: list, **kwargs):
        mp = kwargs.get("mediaplayer")
        settings = kwargs.get("settings")
        request = " ".join(args).strip()

        if len(request) > 0:
            if not self.marcel.is_member_admin(message.author):
                await message.channel.send(
                    embed=embed_message(
                        "Only server administrators can change the volume limit",
                        discord.Color.red()
                    ),
                    delete_after=settings.get("delete_after")
                )
                return

            try:
                new_volume = round(float(request) / 100, 2)

                if 200.0 >= new_volume >= 0:
                    mp.set_volume_limit(new_volume)
                    settings["volume_limit"] = mp.player_volume_limit
                    await message.channel.send(
                        embed=embed_message(
                            "Volume limit is now set to",
                            discord.Color.blue(),
                            "{}%".format(mp.player_volume_limit * 100)
                        ),
                        delete_after=settings.get("delete_after")
                    )

                else:
                    await message.channel.send(
                        embed=embed_message(
                            "Volume limit must be >= 0% and <= 200%",
                            discord.Color.red()
                        ),
                        delete_after=settings.get("delete_after")
                    )

            except:
                await message.channel.send(
                    embed=embed_message(
                        "Invalid volume",
                        discord.Color.red()
                    ),
                    delete_after=settings.get("delete_after")
                )

        else:
            await message.channel.send(
                embed=embed_message(
                    "Current volume limit",
                    discord.Color.blue(),
                    "{}%".format(mp.player_volume_limit * 100)
                ),
                delete_after=settings.get("delete_after")
            )