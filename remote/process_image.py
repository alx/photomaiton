import os
from PIL import Image
import PIL.ImageOps
from pathlib import Path
import glob
import json
import logging

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

with open(Path(CURRENT_PATH, 'config.json'), 'r') as f:
    config = json.load(f)

LOG_FILENAME = Path(CURRENT_PATH, config["log_filename"])
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)

print(f"Loading config: {config}")
CAPTURE_FOLDER = Path(CURRENT_PATH, config["mastodon_capture_folder"])
if not CAPTURE_FOLDER.exists():
    os.makedirs(CAPTURE_FOLDER)

try:
    from diffusers import (
        StableDiffusionXLAdapterPipeline,
        T2IAdapter,
        EulerAncestralDiscreteScheduler,
        AutoencoderKL,
    )
    from diffusers.utils import load_image, make_image_grid
    from controlnet_aux import OpenposeDetector, ZoeDetector, LineartDetector
    import torch
    import numpy as np
    from safetensors.torch import load
    import skimage.io
    import skimage.util
    import skimage.io
    import skimage.util
except ImportError:
    print("Error importing diffusers. Is it installed?")

class ImageProcessor:

    def run(self, capture_id, status):

        if config["processor"]["type"] == "cpu":
            self.process_cpu(capture_id, status)

        else:
            self.process_depth(capture_id, status)

    def create_hash(self, input_string: str):
        pairs = input_string.split("|")
        hash_dict = {}
        for pair in pairs:
            key_value = pair.strip().split(":")
            key = key_value[0].strip()
            try:
                value = float(key_value[1].strip())
            except ValueError:
                value = key_value[1].strip()
            hash_dict[key] = value
        return hash_dict


    def process_cpu(self, capture_id, status):

        capture_filepath = Path(CAPTURE_FOLDER, f"{capture_id}.jpg")
        dst_img = Path(
            CAPTURE_FOLDER, f"%s%s%s.jpg" % (OUTPUT_PREFIX, capture_id, OUTPUT_SUFFIX)
        )

        image = Image.open(capture_filepath)
        inverted_image = PIL.ImageOps.invert(image)
        inverted_image.save(dst_img)

    def process_depth(self, capture_id, status):

        GUIDANCE_SCALE = 15
        INFERENCE_STEPS = 30

        OUTPUT_PREFIX = "response_"
        OUTPUT_SUFFIX = ""

        device = torch.device("cuda:%i" % config["processor"]["gpu_id"])

        zoe_depth = ZoeDetector.from_pretrained(
            "valhalla/t2iadapter-aux-models",
            filename="zoed_nk.pth",
            model_type="zoedepth_nk",
        ).to(device)

        capture_filepath = Path(CAPTURE_FOLDER, f"{capture_id}.jpg")

        image = load_image(Image.open(capture_filepath))
        image = zoe_depth(
            image, gamma_corrected=True, detect_resolution=512, image_resolution=1024
        )

        prompt = "photo, portrait, standing, inside a cabin"
        negative_prompt = ""

        # status_hash = self.create_hash(status_text(status))
        # if hasattr(status_hash, "prompt"):
        #     prompt = status_hash["prompt"]
        # if hasattr(status_hash, "negative_prompt"):
        #     negative_prompt = status_hash["negative_prompt"]

        gen_images = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            num_inference_steps=30,
            adapter_conditioning_scale=1,
            guidance_scale=7.5,
        ).images[0]
        dst_img = Path(
            CAPTURE_FOLDER, f"%s%s%s.jpg" % (OUTPUT_PREFIX, capture_id, OUTPUT_SUFFIX)
        )
        gen_images.save(str(dst_img))

        return str(dst_img)

    def process_t2i_sdxl(self, capture_id, status):
        GUIDANCE_SCALE = 15
        INFERENCE_STEPS = 30

        OUTPUT_PREFIX = "response_"
        OUTPUT_SUFFIX = ""

        device = torch.device("cuda:%i" % config["processor"]["gpu_id"])

        # load adapter
        adapter = T2IAdapter.from_pretrained(
            "TencentARC/t2i-adapter-depth-zoe-sdxl-1.0",
            torch_dtype=torch.float16,
            varient="fp16",
        ).to(device)

        # load euler_a scheduler
        model_id = "stabilityai/stable-diffusion-xl-base-1.0"
        euler_a = EulerAncestralDiscreteScheduler.from_pretrained(
            model_id, subfolder="scheduler"
        )
        vae = AutoencoderKL.from_pretrained(
            "madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16
        )
        pipe = StableDiffusionXLAdapterPipeline.from_pretrained(
            model_id,
            vae=vae,
            adapter=adapter,
            scheduler=euler_a,
            torch_dtype=torch.float16,
            variant="fp16",
        ).to(device)
        pipe.enable_xformers_memory_efficient_attention()

        zoe_depth = ZoeDetector.from_pretrained(
            "valhalla/t2iadapter-aux-models",
            filename="zoed_nk.pth",
            model_type="zoedepth_nk",
        ).to(device)

        capture_filepath = Path(CAPTURE_FOLDER, f"{capture_id}.jpg")
        image = load_image(str(capture_filepath))
        image = zoe_depth(
            image, gamma_corrected=True, detect_resolution=512, image_resolution=1024
        )

        prompt = "couple of french bulldog  on a mini boat for a romantic ride on a flowery lake , many little butterflies are flying, wearing elegant attire, pink sunglasses, a bandana, big golden necklace, by anthro, very detailed, intrincated, cinematic light"
        negative_prompt = "((overexposure)), ((high contrast)),(((cropped))), (((watermark))), ((logo)), ((barcode)), ((UI)), ((signature)), ((text)), ((label)), ((error)), ((title)), stickers, markings, speech bubbles, lines, cropped, lowres, low quality, artifacts"

        # status_hash = self.create_hash(status_text(status))
        # if hasattr(status_hash, "prompt"):
        #     prompt = status_hash["prompt"]
        # if hasattr(status_hash, "negative_prompt"):
        #     negative_prompt = status_hash["negative_prompt"]

        gen_images = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            num_inference_steps=30,
            adapter_conditioning_scale=1,
            guidance_scale=7.5,
        ).images[0]
        dst_img = Path(
            CAPTURE_FOLDER, f"%s%s%s.jpg" % (OUTPUT_PREFIX, capture_id, OUTPUT_SUFFIX)
        )
        gen_images.save(str(dst_img))

        return str(dst_img)
