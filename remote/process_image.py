import os
from PIL import Image
import PIL.ImageOps
from pathlib import Path
import glob
import json
import logging

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

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
    print("Error importing diffusers, it will run fine on CPU")


class ImageProcessor:
    def __init__(self, config, logging):
        self.config = config
        self.process_config = config["processor"]
        self.logging = logging

    def run(self, status, capture):
        if self.config["processor"]["type"] == "cpu":
            return self.process_cpu(status, capture)
        else:
            return self.process_gpu(status, capture)

    def src_path(self, capture):
        src_filename = f"%s.%s" % (capture["capture_id"], capture["extension"])

        return Path(CURRENT_PATH, self.config["mastodon_capture_folder"], src_filename)

    def dst_path(self, capture):
        dst_filename = f"%s%s%s.%s" % (
            self.process_config["output_prefix"],
            capture["capture_id"],
            self.process_config["output_suffix"],
            capture["extension"],
        )

        return Path(CURRENT_PATH, self.config["mastodon_capture_folder"], dst_filename)

    def process_cpu(self, status, capture):
        src_path = self.src_path(capture)
        dst_path = self.dst_path(capture)

        image = Image.open(src_path)
        inverted_image = PIL.ImageOps.invert(image)
        inverted_image.save(dst_path)

        return str(dst_path)

    def process_gpu(self, status, capture):
        src_path = self.src_path(capture)
        dst_path = self.dst_path(capture)

        device = torch.device("cuda:%i" % self.config["processor"]["gpu_id"])

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

        image = load_image(str(src_path))
        image = zoe_depth(
            image, gamma_corrected=True, detect_resolution=512, image_resolution=1024
        )

        gen_images = pipe(
            prompt=self.config["processor"]["prompt"],
            negative_prompt=self.config["processor"]["negative_prompt"],
            image=image,
            num_inference_steps=30,
            adapter_conditioning_scale=1,
            guidance_scale=7.5,
        ).images[0]

        gen_images.save(str(dst_path))
        return str(dst_path)

    def create_hash(self, input_string: str):
        # Use it with following code:
        #
        # status_hash = self.create_hash(status_text(status))
        # if hasattr(status_hash, "prompt"):
        #     prompt = status_hash["prompt"]
        # if hasattr(status_hash, "negative_prompt"):
        #     negative_prompt = status_hash["negative_prompt"]

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
