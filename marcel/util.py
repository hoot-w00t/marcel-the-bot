import discord

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

def embed_message(title: str, color: discord.Color, message: str = "") -> discord.Embed:
    """Create a discord.Embed to display a simple message"""

    embed = discord.Embed(title=message, color=color)
    embed.set_author(name=title)

    return embed

def escape_text(text: str) -> str:
    """Escape mentions and markdown in text"""

    return discord.utils.escape_mentions(discord.utils.escape_markdown(text))