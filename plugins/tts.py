from marcel import Marcel
from marcel.voice import PlayerInfo
from marcel.util import embed_message
from pathlib import Path
import discord
import tempfile
import gtts
import logging

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
    `{prefix}tts-lang` [lang] will change the Text To Speech language (`en` by default)
    `{prefix}tts-langs` will display a list of the supported Text To Speech languages"""

    bot_commands = [
        ("say", "tts_cmd", "clean_command"),
        ("speak", "tts_cmd", "clean_command"),
        ("tts-lang", "tts_lang_cmd", "clean_command"),
        ("tts-langs", "tts_langs_cmd", "clean_command")
    ]

    def __init__(self, marcel: Marcel):
        self.marcel = marcel

        logging.info("Fetching Google TTS langs...")
        self.langs = gtts.lang.tts_langs()
        logging.info("Done fetching Google TTS langs")

    def generate_tts(self, text: str, lang: str, filename: str):
        """Generate the TTS audio"""

        tmp_file = str(Path(tempfile.gettempdir()).joinpath(
            "{}.mp3".format(filename)
        ))

        gtts.gTTS(text=text, lang=lang, slow=False).save(tmp_file)

        return tmp_file

    async def tts_cmd(self, message: discord.Message, args: list, **kwargs):
        lang = kwargs.get("settings").get("tts_lang", "en")
        text = " ".join(args).strip()

        if len(text) > 0:
            mp = self.marcel.get_server_mediaplayer(message.guild)

            async with message.channel.typing():
                pinfo = PlayerInfo(
                    title="Text To Speech",
                    author=self.plugin_name,
                    playback_url=await self.marcel.loop.run_in_executor(
                        None,
                        lambda: self.generate_tts(
                            "{}: {}".format(
                                message.author.display_name,
                                text
                            ),
                            lang,
                            str(message.guild.id)
                        )
                    ),
                    found=True
                )

            await mp.play(
                pinfo,
                message.channel,
                message.author,
                silent=True,
                autoplay=True if len(mp.player_queue) > 0 else False
            )

    async def tts_lang_cmd(self, message: discord.Message, args: list, **kwargs):
        settings = kwargs.get("settings")
        new_lang = " ".join(args).strip()

        if len(new_lang) == 0:
            await message.channel.send(
                embed=embed_message(
                    "Text To Speech language is",
                    discord.Color.blue(),
                    self.langs.get(settings.get("tts_lang", "en"))
                ),
                delete_after=settings.get("delete_after")
            )
            return

        lang_name = self.langs.get(new_lang)
        if lang_name:
            settings["tts_lang"] = new_lang

            await message.channel.send(
                embed=embed_message(
                    "Text To Speech language set to",
                    discord.Color.blue(),
                    lang_name
                ),
                delete_after=settings.get("delete_after")
            )
            return

        new_lang = new_lang.lower()
        for lang in self.langs:
            if self.langs[lang].lower().startswith(new_lang):
                settings["tts_lang"] = lang

                await message.channel.send(
                    embed=embed_message(
                        "Text To Speech language set to",
                        discord.Color.blue(),
                        self.langs[lang]
                    ),
                    delete_after=settings.get("delete_after")
                )
                return

        await message.channel.send(
            embed=embed_message(
                self.plugin_name,
                discord.Color.dark_red(),
                "Invalid lang"
            ),
            delete_after=settings.get("delete_after")
        )

    async def tts_langs_cmd(self, message: discord.Message, args: list, **kwargs):
        part = 1
        count = 0

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name="Text to speech langs (part {})".format(part))

        for lang in self.langs:
            embed.add_field(
                name=self.langs[lang],
                value=lang,
                inline=True
            )
            count += 1

            if count >= 20:
                count = 0
                part += 1
                await message.channel.send(embed=embed)

                embed = discord.Embed(color=discord.Color.blue())
                embed.set_author(name="Text to speech langs (part {})".format(part))

        if count > 0:
            await message.channel.send(embed=embed)