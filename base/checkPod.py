import requests
import subprocess
from datetime import datetime

available_urls = [
    "http://vmgpu.taile7da6.ts.net:5005/api/processing",
    "http://vmgpu-1.taile7da6.ts.net:5005/api/processing",
    "http://vmgpu-2.taile7da6.ts.net:5005/api/processing",
    "http://vmgpu-3.taile7da6.ts.net:5005/api/processing"
]

url_found = False
for url in available_urls:
    try:
        # get Ã  la con.
        response = requests.get(url)
        response.raise_for_status() 

        # il existe, refresh
        print("Refresh Pod", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        subprocess.call(["sudo", "/home/minutepapillons/vmgpu.sh", "restart"])
        url_found = True
        break
    except requests.exceptions.RequestException as e:
        print("Pod pas trouvé:", url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        continue

if not url_found:
    # Aucun serveur n'est disponible, exÃ©cuter votre script shell initial
    subprocess.call(["/home/minutepapillons/code/runpod/start.sh"])
    print("Restart Pod", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
