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
field_selectors = [] # Field selectors to filter results.
modes = ["pods", "nodes", "services"] # Available modes
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

# Loop pods and create discovery
if args.mode == "pods":

    # Default field selectors for pods when no field selectors are given.
    # Possible status phase values are: Pending, Running, Succeeded,
    # Failed or Unknown.
    if args.field_selector is None:
        field_selectors.append("metadata.namespace!=kube-system")
        field_selectors.append("status.phase=Running")
    else:
        field_selectors.append(args.field_selector)

    pods = v1.list_pod_for_all_namespaces(
        watch=False,
        field_selector=",".join(field_selectors)
    )

    # Check pods before listing
    if pods:
        for item in pods.items:
            output.append({
                "{#POD}": item.metadata.name,
                "ip": item.status.pod_ip,
                "namespace": item.metadata.namespace,
                "pod": item.metadata.name
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Loop nodes and create discovery
elif args.mode == "nodes":
    nodes = v1.list_node()
    if nodes:
        for item in nodes.items:
            output.append({
                "{#NODE}": item.status.node_info.machine_id,
                "node": item.status.node_info.machine_id,
                "architecture": item.status.node_info.architecture,
                "kernel_version": item.status.node_info.kernel_version,
                "machine_id": item.status.node_info.machine_id,
                "operating_system": item.status.node_info.operating_system,
                "os_image": item.status.node_info.os_image,
                "system_uuid": item.status.node_info.system_uuid
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))

# Loop services and create discovery
elif args.mode == "services":
    services = v1.list_service_for_all_namespaces()
    if services:
        for item in services.items:
            output.append({
                "{#SERVICE}": item.metadata.name
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))
