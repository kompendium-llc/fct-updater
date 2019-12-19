#!/usr/bin/python3
import sys
import json
import subprocess
from urllib.request import urlopen

docker_path = '/usr/bin/docker'
num_tags = 20
url ='https://hub.docker.com/v2/repositories/factominc/factomd/tags/?page_size=%s' % num_tags

def selection_error():
    print("Not a valid selection. Choose again or CTRL + C to exit.")

# CLI interaction
def prompt(tag_list):
    while True:
        try:
            network = int(input("\n### Network Selection ###\n1) MainNet\n2) TestNet\nChoice: "))
            if network == 1:
                mainnet = True
                break
            elif network == 2:
                mainnet = False
                break
            else:
                selection_error()
        except ValueError:
            selection_error()

    print("\n### Docker Image Selection ###")
    for i, tag in enumerate(tag_list):
        print("%s) %s" % (i+1, tag))

    while True:
        try:
            choice = input("Choice: ")
            index = int(choice)
            selection = tag_list[index - 1]
            print("\n### Confirm ###\nNetwork: %s" % ("Mainnet" if mainnet else "Testnet"))
            print("Image: %s" % selection)
            return selection, mainnet
        except (ValueError, IndexError):
            selection_error()

# Strip out feature tags
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

# Request docker tag data
with urlopen(url) as response:
    if response.status != 200:
        print("Error connecting to Docker Hub. Exiting...")
        sys.exit(1)
    response_content = response.read()

# Parse data
try:
    data = json.loads(response_content.decode('utf-8'))
    results = data["results"]
except (json.JSONDecodeError, KeyError, UnicodeDecodeError) as e:
    print("Error parsing Docker Hub response: %s" % e)
    sys.exit(3)
tag_list = parse_results(results)

# Prompt user
(selection, mainnet) = prompt(tag_list)

# Network specific settings
if mainnet:
    port_publish = '8108:8108'
    network = []
else:
    port_publish = '8110:8110'
    network = [ '-network=CUSTOM',
                '-customnet=fct_community_test']
# Confirm
try:
    input("Press enter to continue. CTRL+C to cancel")
except KeyboardInterrupt:
    print("Exiting...")
    sys.exit(4)

# Stop / Remove / Run new version
try:
    print("Stopping factomd container...")
    subprocess.call([docker_path, "stop", "factomd"])
    print("Removing factomd container...")
    subprocess.call([docker_path, "rm", "factomd"])
    print("Updating factomd container...")
    run_commands = [docker_path, 'run', '-d',
                    '--name', 'factomd',
                    '-v', 'factom_database:/root/.factom/m2',
                    '-v', 'factom_keys:/root/.factom/private',
                    '-p', '8088:8088',
                    '-p', '8090:8090',
                    '-p', port_publish,
                    '-l', 'name=factomd',
                    'factominc/factomd:%s' % selection,
                    '-startdelay=600',
                    '-faulttimeout=120',
                    '-config=/root/.factom/private/factomd.conf']
    run_commands.extend(network)
    print(run_commands)
    subprocess.call(run_commands)
except FileNotFoundError:
    print("Unable to run docker.\nEither run as sudo or check path is correct: %s" % docker_path)
    sys.exit(2)