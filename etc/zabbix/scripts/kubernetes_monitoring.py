#!/usr/bin/python

"""
Kubernetes monitoring
Version: 1.0

Usage:
python3 kubernetes_monitoring.py pods
python3 kubernetes_monitoring.py nodes
"""

# Python imports
from argparse import ArgumentParser
import json
import os
import sys

# 3rd party imports
from kubernetes import client, config

# Declare variables
modes = ["pods", "nodes"] # Available modes
output = [] # List for output data

# Parse command-line arguments
parser = ArgumentParser(
    description="Discover or retrieve metrics from Kubernetes pods and nodes."
)
parser.add_argument("mode", choices=modes, help="Discovery or metric: " + \
                    ", ".join(modes))

parser.add_argument("-c", "--config", default="", type=str,
                    help="Filter results by namespace.")

parser.add_argument("-n", "--namespace",
                    default="metadata.namespace!=kube-system", type=str,
                    help="Filter results by namespace.")

parser.add_argument("-s", "--status", default="status.phase=Running", type=str,
                    help="Filter results by status phase.")

args = parser.parse_args()

# Declare variables
filters = [] # Filters for pods/nodes listings

# Check configuration file
if args.config != "":
    if not os.path.isfile(args.config):
        print("Configuration file is not valid.")
        sys.exit()

# Load kubernetes configuration
try:
    if args.config != "":
        config.load_kube_config(config_file=args.config)
    else:
        config.load_kube_config()
except Exception as e:
    print("Unable to load Kubernetes configurations. Error: {}".format(e))
    sys.exit()

# Initialize client using environment settings
v1 = client.CoreV1Api()

# Loop pods and create discovery
if args.mode == "pods":

    # Append command-line arguments to filters
    if args.namespace:
        filters.append(args.namespace),
    if args.status:
        filters.append(args.status)

    pods = v1.list_pod_for_all_namespaces(
        watch=False,
        field_selector="{},{}".format(
            args.status,
            args.namespace
        )
    )

    # Check pods before listing
    if pods:
        for item in pods.items:
            output.append({
                "{#POD}": item.metadata.name,
                "namespace": item.metadata.namespace,
                "ip": item.status.pod_ip
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Loop nodes and create discovery
elif args.mode == "nodes":
    nodes = v1.list_node()
    for item in nodes.items:
        output.append({
            "{#NODE}": item.status.node_info.system_uuid
        })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))
