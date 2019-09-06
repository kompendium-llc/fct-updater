#!/usr/bin/python3
import sys
import json
import subprocess
from urllib.request import urlopen

num_tags = 20
url ='https://hub.docker.com/v2/repositories/factominc/factomd/tags/?page_size=%s' % num_tags
docker_path = '/usr/bin/docker'

def prompt(tag_list):
    print("Please choose an image to install:")
    for i, tag in enumerate(tag_list):
        print("%s) %s" % (i+1, tag))
    choice = input("Enter Image Number: ")
    while True:
        try:
            index = int(choice)
            selection = tag_list[index - 1]
            return selection
        except (ValueError, IndexError):
            print("Not a valid selection. CTRL + C to exit or choose again.")
            choice = input("Enter Image Number: ")

def parse_results(results):
    valid_list = []
    for tag in results:
        name = tag["name"]
        if name[0] == "v":
            valid_list.append(name)
        elif "develop" in name:
            valid_list.append(name)
        elif "master" in name:
            valid_list.append(name)
    return valid_list

with urlopen(url) as response:
    if response.status != 200:
        print("Error connecting to Docker Hub. Exiting...")
        sys.exit(1)
    response_content = response.read()
response_content.decode('utf-8')
data = json.loads(response_content)
results = data["results"]
tag_list = parse_results(results)
selection = prompt(tag_list)

try:
    subprocess.call([docker_path, "stop", "factomd"])
    subprocess.call([docker_path, "rm", "factomd"])

    run_commands = [docker_path, 'run', '-d',
                    '--name', 'factomd',
                    '-v', 'factom_database:/root/.factom/m2',
                    '-v', 'factom_keys:/root/.factom/private',
                    '--restart', 'unless-stopped',
                    '-p', '8088:8088',
                    '-p', '8090:8090',
                    '-p', '8110:8110',
                    '-l', 'name=factomd',
                    'factominc/factomd:%s' % selection,
                    '-broadcastnum=16',
                    '-network=CUSTOM',
                    '-customnet=fct_community_test',
                    '-startdelay=600',
                    '-faulttimeout=120',
                    '-config=/root/.factom/private/factomd.conf']
    subprocess.call(run_commands)
except FileNotFoundError:
    print("Unable to run docker.\nEither run as sudo or check path is correct: %s" % docker_path)
    sys.exit(2)