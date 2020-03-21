#!/usr/bin/python

"""
Docker Swarm service monitoring
Version: 1.0.1

Usage:
python3 docker_swarm.py discovery
python3 docker_swarm.py <mode> --service <service>

Discover Docker Swarm services (with service data as an array):
python3 docker_swarm.py discovery

Retrieve service hostname, status or uptime:
python3 docker_swarm.py hostname --service <service_name>
python3 docker_swarm.py status --service <service_name>
python3 docker_swarm.py uptime --service <service_name>
"""

# Python imports
from argparse import ArgumentParser
import datetime
import json

# 3rd party imports
import dateutil.parser
import docker

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

# Parse system time from Docker
system_time = dateutil.parser.parse(client.info().get("SystemTime"))

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

        # Parse task creation date for comparison
        created_date = dateutil.parser.parse(task.get("CreatedAt"))

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
        "hostname": "",
        "nodes": nodes,
        "status": task_status,
        "uptime": uptime.total_seconds()
    }

# Loop services and nodes to retrieve additional information
for node in client.nodes.list():
    for name, service in services.items():

        # Match node ID to service's node IDs
        if node.attrs.get("ID") in service.get("nodes"):

            # Add comma if hostnames already have items
            if services[name].get("hostname"):
                services[name]["hostname"] += ", "

            # Add node hostname to services dictionary
            services[name]["hostname"] += "{}".format(
                node.attrs.get("Description").get("Hostname")
            )

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
