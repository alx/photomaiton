import os
from PIL import Image
import PIL.ImageOps
from pathlib import Path
import glob
import json
import logging
import cv2
import re
import swapper
from bs4 import BeautifulSoup
import insightface
from insightface.app import FaceAnalysis
from collections import Counter

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
    def __init__(self,
                 config=None,
                 logging=None,
                 swapper_model = "./checkpoints/inswapper_128.onnx"
                 ):
        self.config = config

        if config is not None:
            self.process_config = config["processor"]

        self.logging = logging

        self.face_analyser = FaceAnalysis(name='buffalo_l')
        self.face_analyser.prepare(ctx_id=0)

        self.swapper = insightface.model_zoo.get_model(swapper_model)

    def run(self, status, capture):
        if self.config["processor"]["type"] == "cpu":
            return self.process_cpu(status, capture)
        else:
            return self.process_gpu(status, capture)

    def src_path(self, capture):
        src_filename = f"%s.%s" % (capture["capture_id"], capture["extension"])

        return Path(CURRENT_PATH, self.config["mastodon_capture_folder"], src_filename)

    def dst_path(self, capture, prefix = "", suffix = ""):
        dst_filename = f"%s%s%s%s%s.%s" % (
            self.process_config["output_prefix"],
            prefix,
            capture["capture_id"],
            self.process_config["output_suffix"],
            suffix,
            capture["extension"],
        )

        return Path(CURRENT_PATH, self.config["mastodon_capture_folder"], dst_filename)

    def face_to_prompt(faces):

        if len(faces) == 0:
            return ""

        prompt = []
        ages = [face['age'] for face in faces]
        genders = ["woman" if face['gender'] == 0 else "man" for face in faces]
        count_gender = dict(Counter(genders).items())

        if len(faces) == 1:
            prompt.append(f"%s years old" % (ages[0]))
            prompt.append(f"a %s" % (genders[0]))
        else:
            prompt.append(", ".join([f"%s years old" % (age) for age in ages]))
            for gender in count_gender:
                if count_gender[gender] == 1:
                    prompt.append(f"a %s" % (gender))
                else:
                    prompt.append(f"%i %s" % (
                        count_gender[gender],
                        gender.replace("man", "men")
                    ))

        return ", ".join(prompt)

    def face_swap(self, source, target):

        try:
            source_faces = self.face_analyser.get(cv2.imread(str(source)))
            target_faces = self.face_analyser.get(cv2.imread(str(target)))
        except ValueError:
            pass

        frame = cv2.imread(str(target))
        for source_face, target_face in zip(source_faces, target_faces):
            frame = self.swapper.get(target_frame, target_face, source_face, paste_back=True)

        return frame

    def process_cpu(self, status, capture):
        src_path = self.src_path(capture)
        dst_path = self.dst_path(capture)

        image = Image.open(src_path)
        inverted_image = PIL.ImageOps.invert(image)
        inverted_image.save(dst_path)

        return [{
            "filepath": str(dst_path),
            "description": "process_cpu invert_color"
        }]

    def process_gpu(self, status, capture):

        processed_medias = []
        src_path = self.src_path(capture)

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

        src_img = load_image(str(src_path))
        src_img = zoe_depth(
            src_img,
            gamma_corrected=True,
            detect_resolution=512,
            image_resolution=1024
        )

        prompt = ""
        negative_prompt = ""

        if "prompt" in self.config["processor"]:
            prompt=self.config["processor"]["prompt"]

        if "negative_prompt" in self.config["processor"]:
            negative_prompt=self.config["processor"]["negative_prompt"]

        status_hash = self.create_hash_from_status(status)
        if "prompt" in status_hash:
            prompt = ", ".join([prompt, status_hash["prompt"]])
        if "negative_prompt" in status_hash:
            negative_prompt = ", ".join([negative_prompt, status_hash["negative_prompt"]])

        dst_img = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=src_img,
            num_inference_steps=30,
            adapter_conditioning_scale=1,
            guidance_scale=7.5,
        ).images[0]

        dst_path = self.dst_path(capture)
        dst_img.save(str(dst_path))
        processed_medias.append({
            "filepath": dst_path,
            "description": str(status_hash)
        })

        if "swap" in status_hash["extra"]:

            frame = self.face_swap(
                source=src_path,
                target=dst_path
            )

            dst_path = self.dst_path(capture, "", "_inswapper")
            cv2.imwrite(str(dst_path), frame)

            processed_medias.append({
                "filepath": dst_path,
                "description": ""
            })

        #if "keep_original" in status_hash["extra"]:
        if True:

            processed_medias.append({
                "filepath": src_path,
                "description": ""
            })

        return processed_medias

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
