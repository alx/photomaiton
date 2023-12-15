import os
from io import BytesIO
import requests
from PIL import Image
from bs4 import BeautifulSoup
from pathlib import Path
from mastodon import StreamListener
from process_image import ImageProcessor
from bs4 import BeautifulSoup

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))


class MastodonListener(StreamListener):
    def __init__(self, config, mastodon, logging):
        self.config = config
        self.mastodon_config = config["listeners"]["mastodon"]
        self.mastodon = mastodon
        self.logging = logging
        self.processor = ImageProcessor(config, logging)

        if self.config["alert_user"]:
            self.mastodon.status_post(
                status=f"user_listener ready - @%s" % (self.config["alert_user"]),
                visibility="direct",
            )

    def create_hash_from_status(self, status):

        soup = BeautifulSoup(status["content"], "html.parser")
        pairs = soup.get_text().split("|")

        hash_dict = {}

        for pair in pairs:

            key_value = pair.strip().split(":")

            if len(key_value) == 1:

                if key_value[0].startswith("@"):
                    key = "user"
                    value = key_value[0].strip()

                else:
                    key = "prompt"
                    try:
                        value = float(key_value[0].strip())
                    except ValueError:
                        value = key_value[0].strip()

            elif len(key_value) == 2:

                key = key_value[0].strip().replace(" ", "_")
                try:
                    value = float(key_value[1].strip())
                except ValueError:
                    value = key_value[1].strip()

            hash_dict[key] = value

        return hash_dict

    def download_media(self, status):
        captured_media = []
        attachments = status["media_attachments"]

        for m in attachments:
            self.logging.debug(f"Downloading media %s" % (m["url"]))
            media_id = m["id"]
            extension = m["url"].split(".")[-1]

            if not extension in self.mastodon_config["capture_allowed_extensions"]:
                self.logging.debug(f"Extension %s not allowed" % (extension))
            else:
                capture_filename = f"%s.%s" % (media_id, extension)
                self.logging.debug(f"Destination %s" % (capture_filename))
                capture_file = Path(
                    CURRENT_PATH,
                    self.config["capture_folder"],
                    capture_filename,
                )

                response = requests.get(m["url"])
                img = (
                    Image.open(BytesIO(response.content))
                    .convert("RGB")
                    .resize((512, 512))
                )
                img.save(capture_file)

                captured_media.append({"capture_id": media_id, "extension": extension})

        return captured_media

    def process_notification(self, notification, capture):

        status = notification["status"]
        
        capture_filename = f"%s.%s" % (capture["capture_id"], capture["extension"])
        capture_filepath = Path(
            CURRENT_PATH, self.config["capture_folder"], capture_filename
        )
        self.logging.debug(f"Processing {capture_filepath}")

        status_content = self.create_hash_from_status(status)
        processed_medias = self.processor.run(status_content, capture)

        mastodon_media_ids = []
        for media in processed_medias:
            mastodon_media_ids.append(
                self.mastodon.media_post(
                    media["filepath"],
                    description = media["description"]
                )
            )

        reply_text = f"@%s / %s %s" % (
            notification["account"]["acct"],
            self.mastodon_config["capture_reply_text"],
            processed_medias[0]["description"]
        )

        # limit reply text to 500 characters
        if len(reply_text) > 500:
            reply_text = reply_text[:497] + "..."

        self.mastodon.status_post(
            status=reply_text,
            in_reply_to_id=status["id"],
            media_ids=mastodon_media_ids,
            visibility="direct",
        )

    # called when receiving new post or status update
    def on_notification(self, notification):

        self.logging.debug(f"on update received from user %s" % (notification["account"]["acct"]))
        status = notification["status"]

        try:

            processable_update = (
                status["in_reply_to_id"] is None
                and status["replies_count"] == 0
            )

            if "whitelist_acct" in self.mastodon_config:
                processable_update = processable_update and (
                    processable_update
                    and str(notification["account"]["acct"]) in self.config["mastodon_whitelist_acct"]
                )

            if "whitelist_followers" in self.mastodon_config:
                # use mastodon.py to get followers
                followers = []
                processable_update = processable_update and (
                    processable_update
                    and str(notification["account"]["acct"]) in followers
                )

            if processable_update:

                self.logging.debug("Processable update")
                capture_media_ids = self.download_media(status)

                for capture_id in capture_media_ids:
                    self.process_notification(notification, capture_id)

            else:
                self.logging.debug("Update not processable")

                if (
                    str(notification["account"]["acct"])
                    not in self.mastodon_config["whitelist_acct"]
                ):
                    self.logging.debug(
                        f"Account acct %s is not whitelisted: %s" % (status["account"]["acct"], self.mastodon_config["whitelist_acct"])
                    )

                if status["in_reply_to_id"] is not None:
                    self.logging.debug(f"Status is a reply, not a root message")

                if status["replies_count"] > 0:
                    self.logging.debug(f"Status has already been replied to")

        except Exception as e:
            self.logging.critical(e, exc_info=True)
