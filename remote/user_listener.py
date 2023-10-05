import os
from io import BytesIO
import requests
from PIL import Image
from bs4 import BeautifulSoup
from pathlib import Path
from mastodon import StreamListener
from process_image import ImageProcessor

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))


class UserListener(StreamListener):
    def __init__(self, config, mastodon, logging):
        self.config = config
        self.mastodon = mastodon
        self.logging = logging
        self.processor = ImageProcessor(config, logging)

    def download_media(self, status):
        captured_media = []
        attachments = status["media_attachments"]

        for m in attachments:
            media_id = m["id"]
            extension = m["url"].split(".")[-1]

            if extension in self.config["mastodon_capture_allowed_extensions"]:
                capture_filename = f"%s.%s" % (media_id, extension)
                self.logging.debug(f"Downloading %s" % (capture_filename))
                capture_file = Path(
                    CURRENT_PATH,
                    self.config["mastodon_capture_folder"],
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

    def process_status(self, status, capture):
        capture_filename = f"%s.%s" % (capture["capture_id"], capture["extension"])
        capture_filepath = Path(
            CURRENT_PATH, self.config["mastodon_capture_folder"], capture_filename
        )
        self.logging.debug(f"Processing {capture_filepath}")

        processed_medias = self.processor.run(status, capture)

        mastodon_media_ids = []
        for media in processed_medias:
            mastodon_media_ids.append(
                self.mastodon.media_post(
                    media["filepath"],
                    description = media["description"]
                )
            )

        self.mastodon.status_post(
            status=self.config["mastodon_capture_reply_text"],
            in_reply_to_id=status["id"],
            media_ids=mastodon_media_ids,
            visibility="direct",
        )

    # called when receiving new post or status update
    def on_update(self, status):
        self.logging.debug(f"on update received from user %s" % (status["account"]["id"]))
        try:
            processable_update = (
                status["account"]["id"] in self.config["mastodon_whitelist_account_ids"]
                and status["in_reply_to_id"] is None
                and status["replies_count"] == 0
            )

            if processable_update:
                capture_media_ids = self.download_media(status)

                for capture_id in capture_media_ids:
                    self.process_status(status, capture_id)

            else:
                self.logging.debug("Update not processable")

                if (
                    status["account"]["id"]
                    not in self.config["mastodon_whitelist_account_ids"]
                ):
                    self.logging.debug(
                        f"Account id %s is not whitelisted" % (status["account"]["id"])
                    )

                if status["in_reply_to_id"] is not None:
                    self.logging.debug(f"Status is a reply, not a root message")

                if status["replies_count"] > 0:
                    self.logging.debug(f"Status has already been replied to")

        except Exception as e:
            self.logging.critical(e, exc_info=True)
