from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
import os
import json
import logging
from mastodon import Mastodon
from pathlib import Path

from user_listener import UserListener

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

with open(Path(CURRENT_PATH, "config.json"), "r") as f:
    config = json.load(f)

LOG_FILENAME = Path(CURRENT_PATH, config["log_filename"])
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)

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
            mastodon.stream_user(UserListener(config, logging))
        except Exception as e:
            logging.debug(f"Error in stream_public: {e}. Restarting...")


try:
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(stream_from_server)]
except Exception as e:
    logging.debug(f"Error running threads: {e}")
