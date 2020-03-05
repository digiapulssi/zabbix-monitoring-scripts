#!/usr/bin/python

# Python imports
from argparse import ArgumentParser
import datetime
import docker
import json
import sys

# Declare variables
modes = ["discovery", "node_hostname", "service_name", "task_status",
         "service_uptime"] # List for available modes
services = {} # Dictionary for Docker service data

# Parse command-line arguments
parser = ArgumentParser(
    description="Discover or retrieve metrics from Docker Swarm services."
)
parser.add_argument("mode", choices=modes, help="Discovery or metric: " + \
                    ", ".join(modes))
parser.add_argument("-s", "--service", type=str,
                    help="Service name to retrieve information of.")
args = parser.parse_args()

# Retrieve docker client instance using environment settings
client = docker.from_env()

# Parse system time from Docker, use timezones on Python 3
if (sys.version_info > (3, 0)):
    system_time = datetime.datetime.strptime(
        client.info().get("SystemTime"),
        "%Y-%m-%dT%H:%M:%S.%f%z"
    )
else:
    system_time = datetime.datetime.strptime(
        client.info().get("SystemTime")[:-4],
        "%Y-%m-%dT%H:%M:%S.%f"
    )

# Loop services and tasks. Retrieve IDs for nodes where task is running.
for service in client.services.list():

    # Reset task variables for each service
    created_date = None
    task_created = None
    task_status = "not running"
    uptime = datetime.timedelta()

    # Loop tasks to collect data
    for task in service.tasks({"desired-state": "running"}):

        # Parse task creation date for comparison, use timezones on Python 3
        if (sys.version_info > (3, 0)):
            created_date = datetime.datetime.strptime(
                task.get("CreatedAt"),
                "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        else:
            created_date = datetime.datetime.strptime(
                task.get("CreatedAt")[:-4],
                "%Y-%m-%dT%H:%M:%S.%f"
            )

        # First time around, grab the first task
        if not task_created:
            task_created = created_date
            task_status = task.get("Status").get("State")
        # Compare previous task's date to current one
        elif task_created < created_date:
            task_created = created_date
            task_status = task.get("Status").get("State")

    # Count uptime
    if task_created:
        uptime = system_time - task_created

    # Append data to dictionary
    services[service.name] = {
        "service_name": service.name,
        "service_uptime": uptime.total_seconds(),
        "task_status": task_status
    }

# Loop nodes for additional information
"""
for node in client.nodes.list():
    if node.attrs.get("ID") in nodes:
        nodes[node.attrs.get("ID")]["node_hostname"] = node.attrs.get(
            "Description").get("Hostname")
"""

# Loop node data and create discovery
if args.mode == "discovery":
    output = []
    for service_name, service in services.items():
        output.append({
            #"{#NODE_HOSTNAME}": service.get("node_hostname"),
            "{#SERVICE_NAME}": service.get("service_name"),
            "{#SERVICE_UPTIME}": service.get("service_uptime"),
            "{#TASK_STATUS}": service.get("task_status")
        })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Retrieve task status from service's tasks
else:
    if not services.get(args.service):
        print("Invalid service name.")
        sys.exit()
    elif not services[args.service].get(args.mode):
        print("Invalid mode argument.")
        sys.exit()
    else:
        print(services[args.service].get(args.mode))
