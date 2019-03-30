#!/usr/bin/python3
import marcel, json, getopt, sys

help_message = """Usage ./main.py [parameters]

--help                      Display this help.
--verbose                   Show additionnal information about Marcel's state (for debugging / verbose nerds).
--config=[path]             Specify the path to the configuration file (by default looks for 'config.json' in the working directory).
"""

def print_message(message, close=False):
    print(message)
    if close : sys.exit(0)

config_path = "config.json"
verbose = False

try:
    opts, args = getopt.getopt(sys.argv[1:], 'h', ['help', 'verbose', 'config='])

except getopt.GetoptError:
    print_message(help_message, close=True)

try:
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_message(help_message, close=True)
        elif opt == '--verbose' : verbose = True
        elif opt == '--config' : config_path = arg

except Exception as e:
    print_message("Error: " + str(e), close=True)


try:
    h = open(config_path)
    config = json.loads(h.read())
    h.close()

except Exception as e:
    print_message("Error: " + str(e), close=True)

marcel_the_bot = marcel.Marcel(bot_token = config['bot_token'], bot_folder=config['bot_folder'], verbose=verbose, logging=config['logging'])
