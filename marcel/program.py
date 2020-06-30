from typing import Union
from pathlib import Path
import marcel
import json

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

sample_config = {
    "token": "your_bot_token_goes_here",
    "owners": [],
    "logging": {
        "level": "info"
    },
    "voice_client": {
        "timeout_idle": 1800,
        "timeout_playing": 7200,
        "player_queue_limit": 20,
        "duration_limit": 1800
    },
    "server_defaults": {
        "prefix": "!!",
        "ack_commands": False,
        "volume": 1.0,
        "volume_limit": 1.25
    }
}

def initialize_cfg(path: Union[str, Path]):
    if isinstance(path, str):
        path = Path(path).expanduser().resolve()

    if path.exists():
        raise FileExistsError(str(path))

    path.mkdir()

    cfg_file = path.joinpath("config.json")
    with cfg_file.open("w") as h:
        json.dump(sample_config, h, indent=4)

    print("Default configuration initialized in: {}".format(path))
    print("Do not forget to put your bot token in the 'config.json' file")

def main():
    from argparse import ArgumentParser

    arg_parser = ArgumentParser(description="Marcel the Discord Bot")
    arg_parser.add_argument(
        "-c", "--cfg-path",
        dest="cfg_path",
        type=str,
        default="./",
        help="Path to the configuration folder (default=./)"
    )
    arg_parser.add_argument(
        "-p", "--plugins-path",
        dest="plugins_path",
        type=str,
        default="./plugins/",
        help="Path to the plugins folder (default=./plugins/)"
    )
    arg_parser.add_argument(
        "-i", "--initialize",
        dest="initialize",
        type=str,
        default=None,
        help="Initialize configuration folder in the given path"
    )
    args = arg_parser.parse_args()

    if args.initialize:
        initialize_cfg(args.initialize)
        return 0

    marcel_the_bot = marcel.Marcel(
        args.cfg_path,
        args.plugins_path
    )
    marcel_the_bot.run()
    return 0