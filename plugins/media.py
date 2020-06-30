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
    `{prefix}play` [request] plays the requested link (supports these: https://rg3.github.io/youtube-dl/supportedsites.html), or searches for the request on YouTube. (Playlists are not supported yet)
    `{prefix}stop`, `{prefix}pause` and `{prefix}resume` stop, pause or resume the playing media.
    `{prefix}skip` skips to the next song in the player queue (if any).
    `{prefix}add` [request] search for your request and add it to the player queue.
    `{prefix}search` [request] searches for your request.
    `{prefix}clear` clears the player queue.
    `{prefix}queue` displays the player queue.
    `{prefix}playing` displays what's currently playing.
    `{prefix}volume` [0 - limit] sets the volume or displays the current (`{prefix}vol` is an alias).

    **For server administrators:**
    `{prefix}volume-limit` [0 - 200] sets the upper volume limit or displays the current (`{prefix}vol-limit` is an alias)
    """

    bot_commands = [
        ("join", "join_cmd"),
        ("leave", "leave_cmd"),
        ("play", "play_cmd"),
        ("skip", "skip_cmd"),
        ("stop", "stop_cmd"),
        ("pause", "pause_cmd"),
        ("resume", "resume_cmd"),
        ("search", "search_cmd"),
        ("add", "add_cmd"),
        ("clear", "clear_cmd"),
        ("queue", "queue_cmd"),
        ("playing", "playing_cmd"),
        ("volume", "volume_cmd"),
        ("volume-limit", "volume_limit_cmd"),
        ("vol", "volume_cmd"),
        ("vol-limit", "volume_limit_cmd")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

    async def join_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.join_member_voice_channel(message.author, message.channel)

    async def leave_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.leave_voice_channel(message.channel)

    async def play_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)
        request = " ".join(args).strip()

        if len(request) > 0:
            await mp.play(
                request,
                channel=message.channel,
                member=message.author,
                autoplay=True
            )

        else:
            await mp.skip(message.channel, autoplay=True)

    async def skip_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.skip(channel=message.channel, autoplay=True)

    async def stop_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.stop(channel=message.channel)

    async def pause_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.pause(channel=message.channel)

    async def resume_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.resume(channel=message.channel)

    async def search_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)
        request = " ".join(args).strip()

        if len(request) > 0:
            async with message.channel.typing():
                pinfo = mp.ytdl_fetch(request, as_playerinfo=True)

            if pinfo.found:
                await message.channel.send(
                    embed=pinfo.get_embed(
                        "Search result",
                        discord.Color.blue()
                    )
                )
            else:
                await message.channel.send(
                    embed=embed_message(
                        "No results for",
                        discord.Color.red(),
                        message=request
                    )
                )

        else:
            await message.channel.send(
                embed=embed_message(
                    "You can't search nothingness.",
                    discord.Color.red()
                )
            )

    async def add_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.player_queue_add(" ".join(args).strip(), channel=message.channel)

    async def clear_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        await mp.player_queue_clear()

    async def queue_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        queue_embed=discord.Embed(color=discord.Color.blue())
        queue_embed.set_author(name="Player queue")

        if len(mp.player_queue) == 0:
            queue_embed.title = "The player queue is empty."
        else:
            first = True
            for media in mp.player_queue:
                if first:
                    first = False
                    queue_embed.title = media.title
                    queue_embed.description = media.author
                    queue_embed.url = media.url
                    queue_embed.set_thumbnail(url=media.thumbnail)
                else:
                    queue_embed.add_field(
                        name=media.title,
                        value=media.author,
                        inline=False
                    )

        await message.channel.send(embed=queue_embed)

    async def playing_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)

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
                )
            )

    async def volume_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)
        guild_settings = self.marcel.get_server_settings(message.guild)
        request = " ".join(args).strip()

        if len(request) > 0:
            try:
                new_volume = round(float(request) / 100, 2)

                if mp.player_volume_limit >= new_volume >= 0:
                    mp.set_volume(new_volume)
                    guild_settings["volume"] = mp.player_volume
                    await message.channel.send(
                        embed=embed_message(
                            "Volume is now at: {}%".format(mp.player_volume * 100),
                            discord.Color.blue()
                        )
                    )

                else:
                    await message.channel.send(
                        embed=embed_message(
                            "Volume must be >= 0% and <= {}%".format(mp.player_volume_limit * 100),
                            discord.Color.red()
                        )
                    )

            except:
                await message.channel.send(
                    embed=embed_message(
                        "Invalid volume",
                        discord.Color.red()
                    )
                )

        else:
            await message.channel.send(
                embed=embed_message(
                    "Current volume: {}%".format(mp.player_volume * 100),
                    discord.Color.blue()
                )
            )

    async def volume_limit_cmd(self, message: discord.Message, args: list):
        mp = self.marcel.get_server_mediaplayer(message.guild)
        guild_settings = self.marcel.get_server_settings(message.guild)
        request = " ".join(args).strip()

        if len(request) > 0:
            if not self.marcel.is_member_admin(message.author):
                await message.channel.send(
                    embed=embed_message(
                        "Only server administrators can change the volume limit",
                        discord.Color.red()
                    )
                )
                return

            try:
                new_volume = round(float(request) / 100, 2)

                if 200.0 >= new_volume >= 0:
                    mp.set_volume_limit(new_volume)
                    guild_settings["volume_limit"] = mp.player_volume_limit
                    await message.channel.send(
                        embed=embed_message(
                            "Volume limit is now at: {}%".format(mp.player_volume_limit * 100),
                            discord.Color.blue()
                        )
                    )

                else:
                    await message.channel.send(
                        embed=embed_message(
                            "Volume limit must be >= 0% and <= 200%",
                            discord.Color.red()
                        )
                    )

            except:
                await message.channel.send(
                    embed=embed_message(
                        "Invalid volume",
                        discord.Color.red()
                    )
                )

        else:
            await message.channel.send(
                embed=embed_message(
                    "Current volume limit: {}%".format(mp.player_volume_limit * 100),
                    discord.Color.blue()
                )
            )