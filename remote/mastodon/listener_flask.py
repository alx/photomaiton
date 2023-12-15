from flask import Flask, request, send_file, send_from_directory
import uuid
from PIL import Image
import io

class FlaskListener:
    def __init__(self, config, logging):
        self.app = Flask(__name__, static_folder='react_webcam/build')
        self.config = config
        self.logging = logging
        self.processor = ImageProcessor(config, logging)

        # Serve React App
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def serve(path):
            if path != "" and os.path.exists(app.static_folder + '/' + path):
                return send_from_directory(app.static_folder, path)
            else:
                return send_from_directory(app.static_folder, 'index.html')


        @self.app.route('/processing', methods=['POST'])
        def process_image():
            prompt = request.form.get('prompt')
            file = request.files['image']

            # Open the image file
            img = Image.open(file.stream)

            # save image in capture folder
            capture_id = uuid.uuid4()
            capture_extension = ".jpg"
            capture_filename = f"%s.%s" % (capture_id, capture_extension)
            img.save(self.config["capture_folder"] + capture_filename)
            self.logging.debug(f"Destination %s" % (capture_filename))
            capture_file = Path(
                CURRENT_PATH,
                self.config["capture_folder"],
                capture_filename,
            )

            img = (
                Image.open(BytesIO(response.content))
                .convert("RGB")
                .resize((512, 512))
            )
            img.save(capture_file)

            # Process the image
            capture = {"capture_id": capture_id, "extension": capture_extension}
            processed_medias = self.processor.run(prompt, capture)

            # Convert the processed image into byte stream
            byte_io = io.BytesIO()
            processed_img.save(byte_io, 'JPEG')
            byte_io.seek(0)

            return send_file(byte_io, mimetype='image/jpeg')

    def run(self):
        self.app.run(use_reloader=True, port=5005, threaded=True)

if __name__ == '__main__':
    listener = FlaskListener()
    listener.run()
