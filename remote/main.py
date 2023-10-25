from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
import os
import json
import logging
import argparse
from mastodon import Mastodon
from pathlib import Path

from user_listener import UserListener

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

parser = argparse.ArgumentParser(description="Read config file path")
parser.add_argument("--config", type=str, help="Path to the configuration file")
args = parser.parse_args()

if args.config:
    config_path = os.path.abspath(args.config)
    print(f"Config file path: {config_path}")
else:
    config_path = Path(CURRENT_PATH, "config.json")
    print("No configuration file provided. Use --config [path_to_config_file] to specify one.")

with open(config_path, "r") as f:
    config = json.load(f)

LOG_FILENAME = Path(CURRENT_PATH, config["log_filename"])
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger().addHandler(logging.StreamHandler())

try:
    mastodon = Mastodon(
        api_base_url=config["mastodon_base_url"],
        access_token=config["mastodon_access_token"],
    )
except Exception as e:
    logging.debug(f"Error connecting to mastodon server {base_url}: {e}")


def stream_from_server():
    while True:
        try:
            logging.debug("Start listening to stream")
            mastodon.stream_user(UserListener(config, mastodon, logging))
        except Exception as e:
            logging.debug(f"Error in stream_public: {e}")
            exit(1)

try:
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(stream_from_server)]
except Exception as e:
    logging.debug(f"Error running threads: {e}")
