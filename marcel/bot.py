from marcel.voice import MarcelMediaPlayer
from marcel.util import embed_message
from pathlib import Path
from typing import Union
from importlib import machinery
from discord.ext import tasks
import os
import re
import json
import logging
import discord
import types
import time

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

class Marcel:
    def __init__(self, cfg_path: Union[str, Path], plugins_path: Union[str, Path]):
        # Expand cfg_path (bot root folder)
        if isinstance(cfg_path, Path):
            self.cfg_path = cfg_path
        else:
            self.cfg_path = Path(cfg_path).expanduser().resolve()

        # Create Path() objects for config.json and servers.json
        self.cfg_file = self.cfg_path.joinpath("config.json")
        self.servers_file = self.cfg_path.joinpath("servers.json")

        # Load bot configuration file
        self.load_cfg()

        # Initializing variables
        self.plugins = dict()         # Loaded bot plugins
        self.commands = dict()        # Commands' function handlers
        self.voice_clients = dict()   # Voice clients for each server
        self.event_handlers = dict()  # Bot events' function handlers
        self.owners = None            # Bot owners

        self.bot = discord.Client()

        self.bot.event(self.on_ready)
        self.bot.event(self.on_disconnect)
        self.bot.event(self.on_message)
        self.bot.event(self.on_member_join)
        self.bot.event(self.on_member_remove)
        self.bot.event(self.on_guild_join)
        self.bot.event(self.on_guild_remove)
        self.bot.event(self.on_reaction_add)
        self.bot.event(self.on_reaction_remove)

        # Setup logging
        log_level_cfg = self.cfg.get("logging", dict()).get("level", "warning")
        log_level = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "warn": logging.WARN,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }.get(log_level_cfg, None)

        if log_level == None:
            raise Exception("Accepted ogging levels are debug, info, warning, error, critical (case-sensitive)")

        log_formatter = logging.Formatter("[%(levelname)s] [%(asctime)s] %(message)s")
        logger = logging.getLogger()
        logger.setLevel(log_level)

        log_stdout = logging.StreamHandler(stream=os.sys.stdout)
        log_stdout.setFormatter(log_formatter)
        logger.addHandler(log_stdout)

        # Load configuration settings
        self.load_server_settings()

        # Expand plugins_path (bot plugins folder)
        if isinstance(plugins_path, Path):
            self.plugins_path = plugins_path
        else:
            self.plugins_path = Path(plugins_path).expanduser().resolve()

        # Load plugins
        self.load_plugins()

    def run(self):
        """Run the bot (blocking)"""

        self.bot.run(self.cfg.get("token"))
        self.save_server_settings()

    def load_cfg(self):
        """Load bot configuration from config.json"""

        with self.cfg_file.open("r") as h:
            self.cfg = json.load(h)

        self.server_settings_default = self.cfg.get("server_default", dict())

    def load_owners(self):
        """Find bot owners"""

        if self.owners == None:
            self.owners = list()
        else:
            self.owners.clear()

        for owner in self.cfg.get("owners", list()):
            self.owners.append(self.bot.get_user(int(owner)))

    def load_plugin(self, filepath: Union[str, Path]):
        """Load plugin"""

        if not isinstance(filepath, Path):
            filepath = Path(filepath).expanduser().resolve()

        try:
            logging.info("Loading plugin: {}".format(filepath))
            loader = machinery.SourceFileLoader("MarcelPlugin", str(filepath))
            module = types.ModuleType(loader.name)
            loader.exec_module(module)

            plugin_name = module.MarcelPlugin.plugin_name

            if plugin_name in self.plugins:
                raise Exception("Plugin: {}: is already loaded".format(plugin_name))

            plugin_module = module.MarcelPlugin(self)

            for command in module.MarcelPlugin.bot_commands:
                command_name = command[0]
                command_funcname = command[1] if len(command) > 1 else command_name

                if command_name in self.commands:
                    logging.error("Unable to add command: {}: from {}: command already exists".format(
                        command_name,
                        plugin_name
                    ))

                else:
                    logging.info("Adding command: {}: from {}".format(
                        command_name,
                        plugin_name
                    ))
                    self.commands[command_name] = {
                        "plugin_name": plugin_name,
                        "function_name": command_funcname
                    }

            self.plugins[plugin_name] = {
                "module": plugin_module,
                "filepath": filepath
            }

            return True

        except Exception as e:
            logging.error("Unable to load plugin: {}: {}".format(
                filepath,
                e
            ))

        return False

    def unload_plugin(self, name: str):
        """Unload plugin by name"""

        plugin = self.plugins.get(name)
        if plugin:
            logging.info("Unloading plugin: {}".format(name))

            try:
                unload_func = getattr(plugin.get("module"), "unload")
                logging.info("Executing unload function for plugin: {}".format(name))
                unload_func()

            except:
                pass

            for command in list(self.commands):
                if self.commands[command]["plugin_name"] == name:
                    logging.info("Removing command {}: from {}".format(
                        command,
                        name
                    ))
                    del self.commands[command]

            for event in self.event_handlers:
                self.unregister_event_handler(name, event)

            del plugin["module"]
            plugin.clear()
            del self.plugins[name]

            return True

        else:
            logging.error("Unable to unload plugin: {}: does not exist".format(name))

        return False

    def load_plugins(self):
        """Load all plugins from the plugins folder"""

        logging.info("Loading plugins from folder: {}".format(self.plugins_path))
        for filename in self.plugins_path.iterdir():
            if filename.name.lower().endswith(".py"):
                self.load_plugin(filename)

    def unload_plugins(self):
        """Unload all currently loaded plugins"""

        for plugin in list(self.plugins):
            self.unload_plugin(plugin)

    def reload_plugin(self, name: str):
        """Reload plugin"""

        filepath = self.plugins.get(name, dict()).get("filepath")
        if filepath:
            self.unload_plugin(name)
            return self.load_plugin(filepath)

        return False

    def reload_plugins(self):
        """Reload all plugins from the plugins folder"""

        self.unload_plugins()
        self.load_plugins()

        return True

    def get_command_func(self, command: str):
        """Return command function or None if it is not found"""

        command_info = self.commands.get(command)

        if command_info:
            plugin = self.plugins.get(command_info["plugin_name"], dict())
            return getattr(plugin.get("module"), command_info["function_name"])

        return None

    def get_event_handler_functions(self, event_name: str):
        """Return a list of handler functions for event_name"""

        funcs = list()
        handlers = self.event_handlers.get(event_name)

        if handlers:
            for handler in handlers:
                plugin = self.plugins.get(handler["plugin_name"], dict())
                func = getattr(plugin.get("module"), handler["function_name"])
                if func:
                    funcs.append(func)

        return funcs

    def register_event_handler(self, plugin: Union[str, object], event_name: str, function_name: str):
        """Register function_name from plugin for event_name
        plugin can be the plugin name (str) or the class object (self, if called from the plugin)"""

        if isinstance(plugin, str):
            plugin_name = plugin
        else:
            plugin_name = plugin.plugin_name

        if not event_name in self.event_handlers:
            self.event_handlers[event_name] = list()

        logging.info("Registering function {}: in event handler {}: from plugin {}".format(
            function_name,
            event_name,
            plugin_name
        ))
        self.event_handlers[event_name].append({
            "plugin_name": plugin_name,
            "function_name": function_name,
        })

        return True

    def unregister_event_handler(self, plugin: Union[str, object], event_name: str, function_name: str = None):
        """Unregister function_name from plugin for event_name
        plugin can be the plugin name (str) or the class object (self, if called from the plugin)
        If function_name is None all registered functions for the plugin will be unregistered"""
        if isinstance(plugin, str):
            plugin_name = plugin
        else:
            plugin_name = plugin.plugin_name

        logging.info("Unregistering {}: from event handler {}: from plugin {}".format(
            "all functions" if function_name == None else "function {}".format(function_name),
            event_name,
            plugin_name
        ))
        if event_name in self.event_handlers:
            for handler in self.event_handlers[event_name]:
                if handler["plugin_name"] == plugin_name:
                    if function_name == None or handler["function_name"] == function_name:
                        self.event_handlers[event_name].remove(handler)

        return True

    def load_server_settings(self):
        """Load server settings from servers.json"""

        if self.servers_file.exists():
            logging.info("Loading server settings from {}".format(self.servers_file))

            with self.servers_file.open("r") as h:
                self.server_settings = json.load(h)

        else:
            self.server_settings = dict()

        self.server_settings_diff = self.server_settings.copy()

    def save_server_settings(self):
        """Save server settings to servers.json"""

        logging.info("Saving server settings to {}".format(self.servers_file))
        with self.servers_file.open("w") as h:
            json.dump(self.server_settings, h, indent=4)

        self.server_settings_diff = self.server_settings.copy()

    def get_server_settings(self, guild: Union[discord.Guild, int]) -> dict:
        """Return server settings dict() for the given guild"""

        if isinstance(guild, discord.Guild):
            guild_id = str(guild.id)
        else:
            guild_id = str(guild)

        if not guild_id in self.server_settings:
            logging.debug("Creating default settings for guild: {}".format(guild_id))
            self.server_settings[guild_id] = self.cfg.get("server_defaults", dict()).copy()

        return self.server_settings.get(guild_id)

    def get_server_mediaplayer(self, guild: discord.Guild) -> MarcelMediaPlayer:
        """Return server MarcelMediaPlayer for the given guild"""

        guild_id = str(guild.id)

        if not guild_id in self.voice_clients:
            logging.info("Creating Media Player for guild: {}".format(guild_id))
            guild_settings = self.get_server_settings(guild.id)

            self.voice_clients[guild_id] = MarcelMediaPlayer(
                guild,
                volume=guild_settings.get("volume", 1.0),
                volume_limit=guild_settings.get("volume_limit", 1.0),
                player_queue_limit=self.cfg.get("voice_client", dict()).get("player_queue_limit", 20),
                duration_limit=self.cfg.get("voice_client", dict()).get("duration_limit", 1800),
                timeout_idle=self.cfg.get("voice_client", dict()).get("timeout_idle", 1800),
                timeout_playing=self.cfg.get("voice_client", dict()).get("timeout_playing", 7200)
            )

        return self.voice_clients.get(guild_id)

    def is_member_owner(self, member: discord.Member):
        """Return True if member is an owner"""

        if self.owners == None:
            self.load_owners()

        for owner in self.owners:
            if member == owner:
                return True

        return False

    def is_member_admin(self, member: discord.Member):
        """Return True if member is a bot administrator"""

        return self.is_member_owner(member) or member.guild_permissions.administrator

    def is_me(self, member: discord.Member):
        """Return True if member is the bot user"""

        return member == self.bot.user

    async def on_message(self, message: discord.Message):
        if not (self.is_me(message.author) or not isinstance(message.channel, discord.abc.GuildChannel)):
            guild_settings = self.get_server_settings(message.guild)
            prefix = guild_settings.get("prefix")
            ack_commands = guild_settings.get("ack_commands", False)

            if not isinstance(prefix, str):
                logging.critical("No prefix set for guild {} ({})".format(
                    message.guild.name,
                    message.guild.id
                ))
                return

            if message.content.startswith(prefix):
                args = message.content.split()
                command = args[0][len(prefix):]
                del args[0]

                func = self.get_command_func(command)
                if func:
                    if ack_commands:
                        await message.add_reaction("\U0001F44D")
                    await func(message, args)

                elif len(command) > 0:
                    if ack_commands:
                        await message.add_reaction("\U0001F44E")
                    else:
                        await message.channel.send("No such command: `{command}`\nUse `{prefix}help` if you're lost".format(
                            command=command,
                            prefix=prefix
                        ))

                else:
                    if ack_commands:
                        await message.add_reaction("\U0001F44E")
                    else:
                        await message.channel.send("Use `{prefix}help` if you're lost".format(
                            prefix=prefix
                        ))

        for func in self.get_event_handler_functions("on_message"):
            await func(message)

    async def on_ready(self):
        logging.warning("Logged in as: {} ({})".format(
            self.bot.user.name,
            self.bot.user.id
        ))

        guilds_str = list()
        for guild in self.bot.guilds:
            guilds_str.append(guild.name)

        logging.warning("Bot is in {} servers: {}".format(
            len(self.bot.guilds),
            ", ".join(guilds_str)
        ))

        for func in self.get_event_handler_functions("on_ready"):
            await func()

    async def on_disconnect(self):
        for func in self.get_event_handler_functions("on_disconnect"):
            await func()

    async def on_reaction_add(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        for func in self.get_event_handler_functions("on_reaction_add"):
            await func(reaction, user)

    async def on_reaction_remove(self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
        for func in self.get_event_handler_functions("on_reaction_remove"):
            await func(reaction, user)

    async def on_member_join(self, member: discord.Member):
        for func in self.get_event_handler_functions("on_member_join"):
            await func(member)

    async def on_member_remove(self, member: discord.Member):
        for func in self.get_event_handler_functions("on_member_remove"):
            await func(member)

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        for func in self.get_event_handler_functions("on_member_update"):
            await func(before, after)

    async def on_guild_join(self, guild: discord.Guild):
        for func in self.get_event_handler_functions("on_guild_join"):
            await func(guild)

    async def on_guild_remove(self, guild: discord.guild):
        for func in self.get_event_handler_functions("on_guild_remove"):
            await func(guild)