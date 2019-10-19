from os.path import join, exists
from os import listdir
from random import randint

class MarcelPlugin:

    """
        SoundBox plugin for Marcel the Discord Bot
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

    plugin_name = "SoundBox"
    plugin_description = "SoundBox to play in a voice channel."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """   Sounds that you can invoke
    `soundlist` displays a list of all the sounds available.
    `s` or `sound` {sound} plays the requested sound (supports autocompletion, e.g. for a `nyan cat` sound you could type `ny`). If no sound is given it will play one at random.
    """
    bot_commands = [
        "soundlist",
        "sound",
        "s",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        self.sounds_folder = join(self.marcel.resources_folder, "soundbox")

        self.sounds = {}
        self.sounds_list = []
        self.media_extensions = [
            '.mp3',
            '.ogg',
            '.webm',
        ]

        if exists(self.sounds_folder):
            for filename in listdir(self.sounds_folder):
                for extension in self.media_extensions:
                    if filename.endswith(extension):
                        plain_filename = filename[:len(filename) - len(extension)].lower().strip()

                        if plain_filename in self.sounds:
                            self.marcel.print_log(f"[{self.plugin_name}] Duplicate filename, will be ignored: {filename}")

                        else:
                            self.sounds[plain_filename] = filename
                            self.sounds_list.append(plain_filename)

        else:
            self.marcel.print_log(f"[{self.plugin_name}] Sounds folder doesn't exist or cannot be accessed: {self.sounds_folder}")

        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def soundlist(self, message, args):
        if len(self.sounds_list) == 0:
            await message.channel.send("The soundbox is empty :confused:")

        else:
            await message.channel.send(f"**The soundbox contains {len(self.sounds_list)} sounds:** {', '.join(self.sounds_list)}")

    async def sound(self, message, args):
        if len(self.sounds_list) == 0:
            await message.channel.send("The soundbox is empty :confused:")

        else:
            if len(args) > 0:
                requested_sound = ' '.join(args).lower().strip()
                for sound in self.sounds_list:
                    if sound.startswith(requested_sound):
                        requested_sound = sound
                        break

                if requested_sound in self.sounds_list:
                    await self.marcel.voice_client_play(message, join(self.sounds_folder, self.sounds[requested_sound]), silent=True, use_ytdl=False, autoplay=False)

                else:
                    await message.channel.send("This sound doesn't exist.")

            else:
                random_sound = self.sounds_list[randint(0, len(self.sounds_list) - 1)]
                await self.marcel.voice_client_play(message, join(self.sounds_folder, self.sounds[random_sound]), silent=True, use_ytdl=False, autoplay=False)

    async def s(self, message, args):
        await self.sound(message, args)