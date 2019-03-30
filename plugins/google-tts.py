from gtts import gTTS
import os

class MarcelPlugin:

    plugin_name = "Google TTS"
    plugin_description = "Google TTS."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    `speak` [text] uses the Google's TTS to say [text] in a vocal channel.
    """
    bot_commands = [
        "speak",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : print("Google TTS plugin loaded.")
    
    def generate_tts(self, text, lang, filepath):
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filepath)

    async def speak(self, message, args):
        if len(args) > 0:
            temp_mp3 = os.path.join(self.marcel.temp_folder, str(message.server.id) + ".mp3")
            self.generate_tts(' '.join(args), self.marcel.get_setting(message.server, 'lang', self.marcel.default_settings['lang']), temp_mp3)
            await self.marcel.voice_client_play(message, temp_mp3, silent=True, use_ytdl=False)
        else:
            await self.marcel.bot.send_message(message.channel, "Nothing to say.")