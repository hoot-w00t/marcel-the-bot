from marcel import Marcel
from marcel.voice import PlayerInfo
from marcel.util import embed_message
from pathlib import Path
import discord
import random

class MarcelPlugin:

    """
        SoundBox plugin for Marcel the Discord Bot
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

    plugin_name = "SoundBox"
    plugin_description = "SoundBox plugin"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}soundlist` displays a list of all the sounds available.
    `{prefix}s` or `{prefix}sound` [sound] plays the requested sound (supports autocompletion, e.g. for a `nyan cat` sound you could type `ny`).
    If no sound is given it will play one at random.
    """
    bot_commands = [
        ("soundlist", "list_sounds", "clean_command"),
        ("sound", "play_sound_cmd", "clean_command"),
        ("s", "play_sound_cmd", "clean_command")
    ]

    media_extensions = [
        ".mp3",
        ".ogg",
        ".webm",
        ".wav",
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel
        self.sounds_path = self.marcel.cfg_path.joinpath("soundbox")

        self.sounds = list()

        for filename in self.sounds_path.iterdir():
            for ext in self.media_extensions:
                if filename.name.lower().endswith(ext):
                    if not filename in self.sounds:
                        self.sounds.append(filename)
                        break

    async def send_empty_soundbox(self, channel: discord.TextChannel):
        await channel.send(
            embed=embed_message(
                "The soundbox is empty",
                discord.Color.red()
            )
        )

    async def list_sounds(self, message: discord.Message, args: list, **kwargs):
        if len(self.sounds) == 0:
            await self.send_empty_soundbox(message.channel)
            return

        count = len(self.sounds)
        sounds = list()
        for sound in self.sounds:
            sounds.append(sound.name[:len(sound.name) - len(sound.suffix)])

        await message.channel.send(
            embed=embed_message(
                "{} sound{} loaded".format(
                    count if count > 0 else "No",
                    "s" if count != 1 else ""
                ),
                discord.Color.blue(),
                message=", ".join(sounds)
            )
        )

    async def play_sound(self, message: discord.Message, sound: Path):
        mp = self.marcel.get_server_mediaplayer(message.guild)

        pinfo = PlayerInfo(
            title=sound.name[:len(sound.name) - len(sound.suffix)],
            author=self.plugin_name,
            playback_url=str(sound),
            found=True
        )
        await mp.play(
            pinfo,
            message.channel,
            message.author,
            silent=True,
            autoplay=True if len(mp.player_queue) > 0 else False)

    async def play_sound_cmd(self, message: discord.Message, args: list, **kwargs):
        if len(self.sounds) == 0:
            await self.send_empty_soundbox(message.channel)
            return

        request = " ".join(args).strip().lower()

        if len(request) > 0:
            for sound in self.sounds:
                if sound.name.lower().startswith(request):
                    await self.play_sound(message, sound)
                    return

            await message.channel.send(
                embed=embed_message(
                    "This sound doesn't exist",
                    discord.Color.red()
                ),
                delete_after=kwargs.get("settings").get("delete_after")
            )

        else:
            await self.play_sound(
                message,
                self.sounds[random.randint(0, len(self.sounds) - 1)]
            )