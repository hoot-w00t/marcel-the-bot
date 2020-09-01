from typing import Union
from pathlib import Path
from marcel import Marcel
import json
import sys

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
        "level": "warning"
    },
    "voice_client": {
        "idle_limit": 1800,
        "player_queue_limit": 20,
        "duration_limit": 1800
    },
    "server_defaults": {
        "prefix": "!!",
        "clean_commands": False,
        "delete_after": 10.0,
        "volume": 1.0,
        "volume_limit": 1.25
    }
}

def initialize_cfg(path: Union[str, Path]) -> int:
    """Initialize configuration file"""

    if isinstance(path, str):
        path = Path(path).expanduser().resolve()

    if not path.exists():
        path.mkdir()

    cfg_file = path.joinpath("config.json")
    if cfg_file.exists():
        if not input("{}: already exists, overwrite? [y/N] ".format(
            str(cfg_file))
            ).strip().lower() in ["y", "yes"]:
            return 1

    with cfg_file.open("w") as h:
        cfg = sample_config.copy()

        token = input("Discord Bot Token: ").strip()
        if len(token) > 0:
            cfg["token"] = token

        json.dump(cfg, h, indent=4)

    print("Configuration initialized in: {}".format(path))
    return 0

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
        return initialize_cfg(args.initialize)

    marcel_the_bot = Marcel(
        args.cfg_path,
        args.plugins_path
    )
    marcel_the_bot.run()

    return 0

if __name__ == "__main__":
    exit(main())