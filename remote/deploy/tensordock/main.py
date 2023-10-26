import os
import sys
from time import sleep
import requests
import json
from pathlib import Path
import logging
from urllib.parse import urlencode
import yaml

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
with open(Path(CURRENT_PATH, "config.json"), "r") as f:
    config = json.load(f)

LOG_FILENAME = Path(CURRENT_PATH, config["log_filename"])
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    filename=LOG_FILENAME,
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger().addHandler(logging.StreamHandler())

def is_api_available():
    url_path = "/api/v0/auth/test"
    response = requests.request(
        "POST",
        config["tensordock"]["api_url"] + url_path,
        data = {
            'api_key': config["tensordock"]["api_key"],
            'api_token': config["tensordock"]["api_token"]
        }
    )
    sleep(1)
    data = json.loads(response.text)
    return data["success"]

def get_host_nodes():
    url_path = "/api/v0/client/deploy/hostnodes"
    response = requests.request(
        "GET",
        config["tensordock"]["api_url"] + url_path,
    )
    sleep(1)
    return json.loads(response.text)

def is_host_eligible(host):
    if not host["status"]["online"]:
        return False

    if host["specs"]["cpu"]["amount"] == 0:
        return False

    if host["specs"]["ram"]["amount"] < config["host_config"]["ram"]:
        return False

    if host["specs"]["storage"]["amount"] < config["host_config"]["hdd"]:
        return False

    if config["host_config"]["gpu_model"] not in host["specs"]["gpu"].keys():
        return False

    if host["specs"]["gpu"][config["host_config"]["gpu_model"]]["amount"] < config["host_config"]["gpu_count"]:
        return False

    if len(host["networking"]["ports"]) < len(config["host_config"]["internal_ports"]):
        return False

    return True

def deploy_machine(host):

    url_path = "/api/v0/client/deploy/single"
    num_ports = len(config["host_config"]["internal_ports"])

    payload = {
        'api_key': config["tensordock"]["api_key"],
        'api_token': config["tensordock"]["api_token"],
        'password': config["host_config"]["password"],
        'name': config["host_config"]["name"],
        'gpu_count': config["host_config"]["gpu_count"],
        'gpu_model': config["host_config"]["gpu_model"],
        'vcpus': config["host_config"]["vcpus"],
        'ram': config["host_config"]["ram"],
        'external_ports': str(set(host["networking"]["ports"][:num_ports])),
        'internal_ports': str(set(config["host_config"]["internal_ports"])),
        'hostnode': host["id"],
        'storage': config["host_config"]["hdd"],
        'operating_system': config["host_config"]["os"]
    }

    if "cloudinit_file" in config["host_config"] and \
        os.path.isfile(config["host_config"]["cloudinit_file"]):
        with open(config["host_config"]["cloudinit_file"], 'r') as f:
            payload["cloudinit_script"] = f.read().replace('\n', r'\n')

    logging.debug("Deploying machine")
    logging.debug(host)
    logging.debug("---")
    logging.debug(payload)
    logging.debug("===")

    req = requests.Request(
        "POST",
        config["tensordock"]["api_url"] + url_path,
        headers = {},
        data = payload
    )
    prepared = req.prepare()

    def pretty_print_POST(req):
        """
        At this point it is completely built and ready
        to be fired; it is "prepared".

        However pay attention at the formatting used in
        this function because it is programmed to be pretty
        printed and may differ from the actual request.
        """
        print('{}\n{}\r\n{}\r\n\r\n{}'.format(
            '-----------START-----------',
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
        ))

    pretty_print_POST(prepared)

    response = requests.Session().send(prepared)
    logging.debug(response.text)
    data = json.loads(response.text)
    success = data["success"]
    sleep(1)

    if success:
        logging.info("Machine deployed")
        ssh_port = 0
        http_port = 0
        for port in data["port_forwards"]:

            if int(data["port_forwards"][port]) == 22:
                ssh_port = int(port)
                logging.info(f"ssh-keygen -f $HOME/.ssh/known_hosts -R '[%s]:%i'" % (data["ip"], ssh_port))
                logging.info(f"ssh -o StrictHostKeyChecking=accept-new -p %i user@%s" % (ssh_port, data["ip"]))

            if int(data["port_forwards"][port]) in [8888, 5000]:
                http_port = int(port)
                logging.info(f"http://%s:%i" % (data["ip"], http_port))

    return success

def info_deploys():

    url_path = "/api/v0/client/list"
    response = requests.request(
        "POST",
        config["tensordock"]["api_url"] + url_path,
        data = {
            'api_key': config["tensordock"]["api_key"],
            'api_token': config["tensordock"]["api_token"]
        }
    )
    sleep(1)
    response = json.loads(response.text)

    for server_uuid in response["virtualmachines"]:

        url_path = "/api/v0/client/get/single"
        response = requests.request(
            "POST",
            config["tensordock"]["api_url"] + url_path,
            data = {
                'api_key': config["tensordock"]["api_key"],
                'api_token': config["tensordock"]["api_token"],
                'server': server_uuid
            }
        )
        response = json.loads(response.text)
        logging.debug(response)
        sleep(1)

def delete_deploys():

    url_path = "/api/v0/client/list"
    response = requests.request(
        "POST",
        config["tensordock"]["api_url"] + url_path,
        data = {
            'api_key': config["tensordock"]["api_key"],
            'api_token': config["tensordock"]["api_token"]
        }
    )
    sleep(1)
    response = json.loads(response.text)

    for server_uuid in response["virtualmachines"]:

        url_path = "/api/v0/client/delete/single"
        response = requests.request(
            "POST",
            config["tensordock"]["api_url"] + url_path,
            data = {
                'api_key': config["tensordock"]["api_key"],
                'api_token': config["tensordock"]["api_token"],
                'server': server_uuid
            }
        )
        sleep(1)

def deploy_node():
    hosts = get_host_nodes()
    host_nodes_keys = hosts["hostnodes"].keys()

    for key in host_nodes_keys:
        host = hosts["hostnodes"][key]
        logging.debug(host)
        if is_host_eligible(host):
            host["id"] = key
            success = deploy_machine(host)
            if success:
                break

if is_api_available():

    if "--delete" in sys.argv:
        delete_deploys()
    elif "--info" in sys.argv:
        info_deploys()
    else:
        deploy_node()

else:
    logging.info("API not available")
