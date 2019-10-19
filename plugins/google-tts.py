from gtts import gTTS
from os.path import join

class MarcelPlugin:

    """
        Google Text To Speech plugin for Marcel the Discord Bot
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

    plugin_name = "Google TTS"
    plugin_description = "Google TTS."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `say` or `speak` [text] uses the Google's TTS to say [text] in a vocal channel.
    """
    bot_commands = [
        "say",
        "speak",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    def generate_tts(self, text, lang, filepath):
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filepath)

    async def say(self, message, args):
        if not self.marcel.get_setting(message.guild, 'command_cleanup', self.marcel.default_settings['command_cleanup']):
            try:
                if message.guild.me.guild_permissions.manage_messages:
                    await message.delete()

            except:
                pass

        if len(args) > 0:
            temp_mp3 = join(self.marcel.temp_folder, f"{message.guild.id}.mp3")
            self.generate_tts(f"{message.author.display_name}: {' '.join(args)}", self.marcel.get_setting(message.guild, 'lang', self.marcel.default_settings['lang']), temp_mp3)
            await self.marcel.voice_client_play(message, temp_mp3, silent=True, use_ytdl=False, autoplay=False)

        else:
            await message.channel.send("Nothing to say.")

    async def speak(self, message, args):
        await self.say(message, args)