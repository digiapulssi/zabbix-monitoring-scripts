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
nodes = {} # Dictionary for docker node data

# Parse command-line arguments
parser = ArgumentParser(
    description="Discover or retrieve metrics from Docker Swarm services."
)
parser.add_argument("mode", choices=modes, help="Discovery or metric: " + \
                    ", ".join(modes))
parser.add_argument("-n", "--node_id", type=str,
                    help="ID for Docker node to retrieve information.")
args = parser.parse_args()

# Retrieve docker client instance using environment settings
client = docker.from_env()

# Loop services and tasks. Retrieve IDs for nodes where task is running.
for service in client.services.list():

    # Reset task variables for each service
    created_date = None
    node_id = None
    node_status = None
    prev_date = None
    updated_date = None
    updated_last = None

    # Parse service's creation date, use timezones on Python 3
    if (sys.version_info > (3, 0)):
        service_created = datetime.datetime.strptime(
            service.attrs.get("CreatedAt"),
            "%Y-%m-%dT%H:%M:%S.%f%z"
        )
    else:
        service_created = datetime.datetime.strptime(
            service.attrs.get("CreatedAt")[:-4],
            "%Y-%m-%dT%H:%M:%S.%f"
        )

    # Loop tasks to collect data
    for task in service.tasks():

        # Parse task date for comparisons
        if (sys.version_info > (3, 0)):
            created_date = datetime.datetime.strptime(
                task.get("CreatedAt"),
                "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            updated_date = datetime.datetime.strptime(
                task.get("UpdatedAt"),
                "%Y-%m-%dT%H:%M:%S.%f%z"
            )
        else:
            created_date = datetime.datetime.strptime(
                task.get("CreatedAt")[:-4],
                "%Y-%m-%dT%H:%M:%S.%f"
            )
            updated_date = datetime.datetime.strptime(
                task.get("UpdatedAt")[:-4],
                "%Y-%m-%dT%H:%M:%S.%f"
            )

        # Retrieve the lastest update time
        if not updated_last:
            updated_last = updated_date
        elif updated_last < updated_date:
            updated_last = updated_date

        # First time around, grab the first task
        if not node_id:
            prev_date = created_date
            node_id = task.get("NodeID")
            node_status = task.get("Status").get("State")
        # Compare previous task's date to current one
        elif prev_date < created_date:
            prev_date = created_date
            node_id = task.get("NodeID")
            node_status = task.get("Status").get("State")

    # Count uptime days, hours, minutes and seconds
    uptime = updated_last - service_created
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Append data to dictionary
    nodes[node_id] = {
        "service_name": service.name,
        "service_uptime": "{} days, {} hours, {} minutes, {} seconds.".format(
            uptime.days, int(hours), int(minutes), int(seconds)
        ),
        "task_status": node_status
    }

# Loop nodes for additional information
for node in client.nodes.list():
    if node.attrs.get("ID") in nodes:
        nodes[node.attrs.get("ID")]["node_hostname"] = node.attrs.get(
            "Description").get("Hostname")

# Loop node data and create discovery
if args.mode == "discovery":
    output = []
    for node_id, node in nodes.items():
        output.append({
            "{#NODE_HOSTNAME}": node.get("node_hostname"),
            "{#NODE_ID}": node_id,
            "{#SERVICE_NAME}": node.get("service_name"),
            "{#SERVICE_UPTIME}": node.get("service_uptime"),
            "{#TASK_STATUS}": node.get("task_status")
        })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Retrieve task status from service's tasks
else:
    if not nodes.get(args.node_id):
        print("Invalid node ID.")
        sys.exit()
    elif not nodes[args.node_id].get(args.mode):
        print("Invalid mode argument.")
        sys.exit()
    else:
        print(nodes[args.node_id].get(args.mode))
