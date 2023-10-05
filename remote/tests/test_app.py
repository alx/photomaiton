# test_app.py

import unittest
from remote.process_image import ImageProcessor

class TestApp(unittest.TestCase):

    def test_create_hash(args):
        obj = ImageProcessor()

        input_string = 'prompt: 10 | negative_prompt: 20'
        status= { "content": input_string }
        hash_dict = obj.create_hash_from_status(status)

        assert isinstance(hash_dict, dict), 'Return type must be a dictionary'
        assert hash_dict['prompt'] == 10, 'Key `prompt` must have a value of 10'
        assert hash_dict['negative_prompt'] == 20, 'Key `negative_prompt` must have a value of 20'

        input_string = 'prompt: Hello | negative_prompt: World'
        status= { "content": input_string }
        hash_dict = obj.create_hash_from_status(status)

        assert hash_dict['prompt'] == 'Hello', 'Key `prompt` must be Hello'
        assert hash_dict['negative_prompt'] == 'World', 'Key `negative_prompt` must be World'

        input_string = 'Hello | negative_prompt: World'
        status= { "content": input_string }
        hash_dict = obj.create_hash_from_status(status)

        assert hash_dict['prompt'] == 'Hello', 'Key `prompt` must be Hello'
        assert hash_dict['negative_prompt'] == 'World', 'Key `negative_prompt` must be World'

        input_string = "<p><span class=\"h-card\"><a href=\"https://mastodon.tetaneutral.net/@alx\" class=\"u-url mention\">@<span>alx</span></a></span> prompt: test image | negative_prompt: cartoon | other_param: 0.2</p>"
        status= { "content": input_string }
        hash_dict = obj.create_hash_from_status(status)

        assert hash_dict['@alx prompt'] == 'test image', 'Key `prompt` must be test image'
        assert hash_dict['negative_prompt'] == 'cartoon', 'Key `negative_prompt` must be cartoon'
        assert hash_dict['other_param'] == 0.2, 'Key `negative_prompt` must be cartoon'

        input_string = "<p>prompt: test image | negative_prompt: cartoon | other_param: 0.2 | <span class=\"h-card\"><a href=\"https://mastodon.tetaneutral.net/@alx\" class=\"u-url mention\">@<span>alx</span></a></span> </p>"
        status= { "content": input_string }
        hash_dict = obj.create_hash_from_status(status)

        assert hash_dict['prompt'] == 'test image', 'Key `prompt` must be test image'
        assert hash_dict['negative_prompt'] == 'cartoon', 'Key `negative_prompt` must be cartoon'
        assert hash_dict['other_param'] == 0.2, 'Key `other_param` must be 0.2'
        assert hash_dict['user'] == "@alx", 'Key `user` must be @alx'

if __name__ == "__main__":
    unittest.main()
