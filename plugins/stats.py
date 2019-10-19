from json import load as json_load
from os.path import join

class MarcelPlugin:

    """
        Bot Management plugin for Marcel the Discord Bot
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

    plugin_name = "Statistics"
    plugin_description = "Statistics commands."
    plugin_author = "https://github.com/hoot-w00t"
    plugin_help = """    Statistics about the bot: `statistics` or `statistics global`
    """
    bot_commands = [
        "statistics",
    ]

    def __init__(self, marcel):
        self.marcel = marcel
        if self.marcel.verbose : self.marcel.print_log(f"[{self.plugin_name}] Plugin loaded.")

    async def statistics(self, message, args):
        if self.marcel.statistics:
            request = ' '.join(args).lower().strip()
            guild_id = f"{message.guild.id}"
            amount_of_stats = 8

            if request == "global":
                total_commands = 0
                global_command_stats = {}

                for guild in self.marcel.all_statistics["guilds"]:
                    for command in self.marcel.all_statistics["guilds"][guild]["commands"]:
                        total_commands += self.marcel.all_statistics["guilds"][guild]["commands"][command]

                        if not command in global_command_stats:
                            global_command_stats[command] = self.marcel.all_statistics["guilds"][guild]["commands"][command]

                        else:
                            global_command_stats[command] += self.marcel.all_statistics["guilds"][guild]["commands"][command]

                sorted_command_stats = sorted(global_command_stats.items(), key=lambda kv: kv[1], reverse=True)

                stats_message = ""
                if len(sorted_command_stats) < amount_of_stats:
                    amount_of_stats = len(sorted_command_stats)

                for i in range(0, amount_of_stats):
                    stats_message += f"{sorted_command_stats[i][0]}: used {sorted_command_stats[i][1]} times ({round(sorted_command_stats[i][1] / total_commands * 100, 2)}%)\n"

                await message.channel.send(f"**Global statistics since {self.marcel.all_statistics['collecting_since']}**\nTotal commands issued: {total_commands}\nMost used commands:\n{stats_message}")

            else:
                total_commands = 0
                server_command_stats = {}

                for command in self.marcel.all_statistics["guilds"][guild_id]["commands"]:
                    total_commands += self.marcel.all_statistics["guilds"][guild_id]["commands"][command]
                    server_command_stats[command] = self.marcel.all_statistics["guilds"][guild_id]["commands"][command]

                sorted_command_stats = sorted(server_command_stats.items(), key=lambda kv: kv[1], reverse=True)

                stats_message = ""
                if len(sorted_command_stats) < amount_of_stats:
                    amount_of_stats = len(sorted_command_stats)

                for i in range(0, amount_of_stats):
                    stats_message += f"{sorted_command_stats[i][0]}: used {sorted_command_stats[i][1]} times ({round(sorted_command_stats[i][1] / total_commands * 100, 2)}%)\n"

                print(self.marcel.all_statistics['guilds'][guild_id]['collecting_since'])
                await message.channel.send(f"**Server statistics since {self.marcel.all_statistics['guilds'][guild_id]['collecting_since']}**\nTotal commands issued: {total_commands}\nMost used commands:\n{stats_message}")

        else:
            await message.channel.send("Statistics are disabled.")