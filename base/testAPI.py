import base64
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor

url = "http://uncanny.taile7da6.ts.net:7860"

payload = {
    "batch_size" :1,
    "prompt" :"un schrtroumpf dans une baignoire",
    "steps" :20,
    "styles" :[ ],
    "subseed" :-1,
    "subseed_strength" :0,
    "tiling" :False,
    "width" :512
}

def callServer(index):
    print("post")
    response = requests.post(f'{url}/sdapi/v1/txt2img', json=payload)
    if not response.ok:
        print(f'{url}/sdapi/v1/txt2img')
        print(response)
        raise RuntimeError("post request failed")
    print("réponse serveur")
    # write each file to disk
    for i, base64_image in enumerate(response.json()['images']):
        # attention: the API does return the file type set in the backend options
        #   trusting it to be always png will go wrong eventually
        with open(f'output{index}TEST.png', 'wb') as fp:
            fp.write(base64.b64decode(base64_image))
    return response

# request the image generation from the backend
def main():
    print("start")
    executor = ThreadPoolExecutor(max_workers=4)
    future =  executor.submit(callServer, 0)
    future =  executor.submit(callServer, 1)
    print("continue")



main()
