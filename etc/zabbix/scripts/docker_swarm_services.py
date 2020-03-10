#!/usr/bin/python

# Python imports
from argparse import ArgumentParser
import datetime
import docker
import json

# Declare variables
modes = ["discovery", "hostname", "status", "uptime"] # Available modes
services = {} # Dictionary for Docker service(s) data

# Parse command-line arguments
parser = ArgumentParser(
    description="Discover or retrieve metrics from Docker Swarm services."
)
parser.add_argument("mode", choices=modes, help="Discovery or metric: " + \
                    ", ".join(modes))
parser.add_argument("-s", "--service", type=str,
                    help="Service name to retrieve information from.")
args = parser.parse_args()

# Retrieve docker client instance using environment settings
client = docker.from_env()

# Parse system time from Docker, skip timezone information
system_time = datetime.datetime.strptime(
    client.info().get("SystemTime")[:-4],
    "%Y-%m-%dT%H:%M:%S.%f"
)

# Limit results to specific service if service parameter is used
service_filters = {}
if args.service:
    service_filters["name"] = args.service

# Loop services and tasks and retrieve information
for service in client.services.list(filters=service_filters):

    # Reset task variables for each service
    created_date = None # Task's creation date
    nodes = [] # A list of nodes where task is currently running
    task_created = None # A datetime object for latest task's creation date
    task_status = "not running" # Task status, default is "not running"
    uptime = datetime.timedelta() # A datetime object for latest task's uptime

    # Loop tasks to collect data, but only from running tasks
    for task in service.tasks({"desired-state": "running"}):

        # Parse task creation date for comparison, skip timezone information
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

        # Grab node ID for later matching from nodes list
        nodes.append(task.get("NodeID"))

    # Count uptime
    if task_created:
        uptime = system_time - task_created

    # Append service data to dictionary
    services[service.name] = {
        "nodes": nodes,
        "status": task_status,
        "uptime": uptime.total_seconds()
    }

# Loop services and nodes to retrieve additional information
for name, service in services.items():

    # List of hostnames for nodes
    hostnames = []

    # Loop nodes and match node IDs, try to retrieve hostname(s) for nodes
    for node in client.nodes.list():
        if node.attrs.get("ID") in service.get("nodes"):
            hostnames.append(node.attrs.get("Description").get("Hostname"))

    # Append hostnames to services-dictionary
    services[name]["hostname"] = ", ".join(hostnames)

# Loop service data and create discovery
if args.mode == "discovery":
    output = []
    for name, service in services.items():
        output.append({
            "{#SERVICE}": name,
            "hostname": service.get("hostname"),
            "uptime": service.get("uptime"),
            "service": name,
            "status": service.get("status")
        })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Retrieve service information using command-line arguments
else:
    if not services.get(args.service):
        print("Invalid service name.")
    elif not services[args.service].get(args.mode):
        print("Invalid mode argument.")
    else:
        print(services[args.service].get(args.mode))
