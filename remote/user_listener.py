import requests
from PIL import Image
from bs4 import BeautifulSoup
from pathlib import Path
from mastodon import StreamListener
from process_image import ImageProcessor

class UserListener(StreamListener):

    def status_text(self, status):
        soup = BeautifulSoup(status["content"], "html.parser")

        # remore h-card
        hcard = soup.find("span", {"class": "h-card"})
        print(f"Found h-card: {hcard}")

        if hcard:
            hcard.decompose()

        return soup.text

    def download_media(self, status):
        is_file_captured = -1
        attachments = status["media_attachments"]

        # TODO allow multiple attachments
        if len(attachments) == 1:
            m = attachments[0]
            media_id = m["id"]
            extension = m["url"].split(".")[-1]

            # TODO global array
            if extension in ["jpg"]:
                filename = f"%s.jpg" % (media_id)
                capture_file = Path(CAPTURE_FOLDER, filename)

                response = requests.get(m["url"])
                img = Image.open(BytesIO(response.content)).convert("RGB").resize((512, 512))
                img.save(capture_file)

                is_file_captured = media_id

        return is_file_captured

    def process_status(self, status, capture_id):

        uapture_filepath = Path(CAPTURE_FOLDER, f"{capture_id}.jpg")
        print(f"Processing {capture_filepath}")

        response_filepath = ImageProcessor.run(capture_id, status)
        print(f"Response {response_filepath}")

        media_ids = mastodon.media_post(response_filepath)

        mastodon.status_post(
            status="@alx this is back",
            in_reply_to_id=status["id"],
            media_ids=media_ids,
            visibility="direct",
        )

    # called when receiving new post or status update
    def on_update(self, status):
        try:
            processable_update = \
                status["account"]["id"] in WHITELISTED_ACCOUNTS \
                and status["in_reply_to_id"] is None \
                and status["replies_count"] == 0

            if processable_update:

                capture_id = self.download_media(status)

                if capture_id != -1:
                    self.process_status(status, capture_id)

        except Exception as e:
            print(f"Error: {e}")

    def on_notification(self, status):
        try:
            print(f"New notif: {status}")
        except Exception as e:
            print(f"Error: {e}")
