#!/usr/bin/python

"""
Kubernetes monitoring
Version: 1.0

Usage:
python3 kubernetes_monitoring.py pods
python3 kubernetes_monitoring.py nodes
python3 kubernetes_monitoring.py services
"""

# Python imports
from argparse import ArgumentParser
import json
import os
import sys

# 3rd party imports
from kubernetes import client, config

# Declare variables
field_selector = "" # Field selector filter for results.
modes = ["pod", "node", "service"] # Available modes
output = [] # List for output data

# Parse command-line arguments
parser = ArgumentParser(
    description="Discover or retrieve metrics from Kubernetes pods and nodes."
)
parser.add_argument("mode", choices=modes, help="Discovery or metric: " + \
                    ", ".join(modes))

parser.add_argument("-c", "--config", default="", type=str,
                    help="Configuration file for Kubernetes client connection.")

parser.add_argument("-f", "--field-selector", dest="field_selector", type=str,
                    help="Filter results using field selectors.")

parser.add_argument("-m", "--metric", type=str,
                    help="Metric to retrieve when using metric mode.")

args = parser.parse_args()

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

# Default field selectors for pods when keyword is given. Possible status
# phase values are: Pending, Running, Succeeded, Failed or Unknown.
if args.mode == "pod" and args.field_selector == "default":
    field_selector = "metadata.namespace!=kube-system,status.phase=Running"
elif args.field_selector is None:
    pass
elif len(args.field_selector) > 3:
    field_selector = args.field_selector

# Loop pods and create discovery
if args.mode == "pod":
    pods = v1.list_pod_for_all_namespaces(
        watch=False,
        field_selector=field_selector
    )

    # Check pods before listing
    if pods:
        for pod in pods.items:

            # Retrieve container's restart counts
            restart_count = []
            for container in pod.status.container_statuses:
                restart_count.append("{}: {}".format(
                    container.name,
                    container.restart_count
                ))

            # Append information to output list
            output.append({
                "{#POD}": pod.metadata.name,
                "restart_count": ", ".join(restart_count),
                "ip": pod.status.pod_ip,
                "namespace": pod.metadata.namespace,
                "pod": pod.metadata.name
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Loop nodes and create discovery
elif args.mode == "node":
    nodes = v1.list_node()
    if nodes:
        for node in nodes.items:

            # Node status is retrieved from node's conditions. Possible
            # conditions are: Ready, MemoryPressure, PIDPressure, DiskPressure
            # and NetworkUnavailable. We are interested only in the main one,
            # "Ready", which describes if the node is healthy and ready to
            # accept pods.
            status = False
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    status = bool(condition.status)

            # Append information to output list
            output.append({
                "{#NODE}": node.status.node_info.machine_id,
                "node": node.status.node_info.machine_id,
                "machine_id": node.status.node_info.machine_id,
                "status": status,
                "system_uuid": node.status.node_info.system_uuid
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Loop services and create discovery
elif args.mode == "service":
    services = v1.list_service_for_all_namespaces()
    if services:
        for service in services.items:

            # Append information to output list
            output.append({
                "{#SERVICE}": service.metadata.name
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))
