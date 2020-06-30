from marcel import Marcel
from marcel.voice import PlayerInfo
from marcel.util import embed_message
from pathlib import Path
import discord
import tempfile
import gtts

class MarcelPlugin:

    """
        Google Text To Speech plugin for Marcel the Discord Bot
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

    plugin_name = "Google TTS"
    plugin_description = "Google Text To Speech plugin"
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """`{prefix}say`/`{prefix}speak` [text] speaks your text in a voice channel using Google's TTS.
    `{prefix}tts-lang` [lang] will change the Text To Speech language (`en` by default)"""

    bot_commands = [
        ("say", "tts_cmd"),
        ("speak", "tts_cmd"),
        ("tts-lang", "tts_lang_cmd")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

        self.langs = gtts.lang.tts_langs()

    def generate_tts(self, text: str, lang: str, filename: str):
        """Generate the TTS audio"""

        tmp_file = str(Path(tempfile.gettempdir()).joinpath(
            "{}.mp3".format(filename)
        ))

        gtts.gTTS(text=text, lang=lang, slow=False).save(tmp_file)

        return tmp_file

    async def tts_cmd(self, message: discord.Message, args: list):
        guild_settings = self.marcel.get_server_settings(message.guild)
        lang = guild_settings.get("tts_lang", "en")
        text = " ".join(args).strip()

        if len(text) > 0:
            mp = self.marcel.get_server_mediaplayer(message.guild)
            pinfo = PlayerInfo(
                title="Text To Speech",
                author=self.plugin_name,
                playback_url=self.generate_tts(
                    "{}: {}".format(
                        message.author.display_name,
                        text
                    ),
                    lang,
                    str(message.guild.id)
                ),
                found=True
            )

            await mp.play(
                pinfo,
                message.channel,
                message.author,
                silent=True,
                autoplay=True if len(mp.player_queue) > 0 else False)

    async def tts_lang_cmd(self, message: discord.Message, args: list):
        guild_settings = self.marcel.get_server_settings(message.guild)
        new_lang = " ".join(args).strip()

        if len(new_lang) == 0:
            await message.channel.send(
                embed=embed_message(
                    "Text To Speech",
                    discord.Color.blue(),
                    "Text To Speech language is: {}".format(
                        self.langs.get(
                            guild_settings.get("tts_lang", "en")
                        )
                    )
                )
            )
            return

        if not self.marcel.is_member_admin(message.author):
            await message.channel.send(
                embed=embed_message(
                    "Only the server administrators have access to this command",
                    discord.Color.dark_red()
                )
            )
            return

        lang_name = self.langs.get(new_lang)
        if lang_name:
            guild_settings["tts_lang"] = new_lang

            await message.channel.send(
                embed=embed_message(
                    "Text To Speech",
                    discord.Color.blue(),
                    "Text To Speech language is now: {}".format(lang_name)
                )
            )
        else:
            await message.channel.send(
                embed=embed_message(
                    "Text To Speech",
                    discord.Color.dark_red(),
                    "Invalid lang"
                )
            )