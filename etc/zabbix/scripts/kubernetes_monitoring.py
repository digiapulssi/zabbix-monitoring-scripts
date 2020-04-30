#!/usr/bin/python

"""
Kubernetes monitoring
Version: 1.0

Usage:
python kubernetes_monitoring.py pods
python kubernetes_monitoring.py pods -c <config_file> -f <field_selector>
python kubernetes_monitoring.py nodes
python kubernetes_monitoring.py services
"""

# Python imports
from argparse import ArgumentParser
import datetime
import json
import os
import sys

# Retrieve timezone aware system time
if sys.version_info[0] < 3:
    import pytz
    system_time = datetime.datetime.now(pytz.utc)
else:
    system_time = datetime.datetime.now(datetime.timezone.utc)

# 3rd party imports
from kubernetes import client, config

# Loop pods and create discovery
def pods(args, v1):

    pods = v1.list_pod_for_all_namespaces(
        watch=False,
        field_selector=args.field_selector
    )

    # Check pods before listing
    if pods:
        for pod in pods.items:

            # Retrieve container's restart counts
            container_started = None # Container's start time
            kind = None # Pod's kind found under metadata.owner_references
            restart_count = 0 # Container's restart count
            started_at = None # Latest start time
            uptime = datetime.timedelta() # A datetime object for latest uptime

            # Loop possible owner_references and retrieve "kind"-field
            if pod.metadata.owner_references:
                for ref in pod.metadata.owner_references:
                    kind = ref.kind

                # Pods that are identified as "Job" are skipped
                if kind == "Job":
                    continue

            # Check if container_statuses is available
            if pod.status.container_statuses:

                # Loop containers and retrieve information
                for container in pod.status.container_statuses:
                    restart_count = int(container.restart_count)

                    # Check "running"-state first, then "terminated"-state
                    if container.state.running is not None:
                        container_started = container.state.running.started_at
                    elif container.state.terminated is not None:
                        container_started = container.state.terminated.started_at
                    else:
                        continue

                    # First time around, grab the first start time
                    if not started_at:
                        started_at = container_started
                    # Compare previous container's start time to current one
                    elif started_at < container_started:
                        started_at = container_started

                # Count uptime
                if started_at:
                    uptime = system_time - started_at

            # Append information to output list
            output.append({
                "{#POD}": pod.metadata.name,
                "restart_count": restart_count,
                "ip": pod.status.pod_ip,
                "namespace": pod.metadata.namespace,
                "pod": pod.metadata.name,
                "uptime": uptime.total_seconds()
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))


# Loop nodes and create discovery
def nodes(args, v1):
    nodes = v1.list_node(
        watch=False,
        field_selector=args.field_selector
    )

    # Check nodes before listing
    if nodes:
        for node in nodes.items:

            # Node status is retrieved from node's conditions. Possible
            # conditions are: Ready, MemoryPressure, PIDPressure, DiskPressure
            # and NetworkUnavailable. We are interested only in the main one,
            # "Ready", which describes if the node is healthy and ready to
            # accept pods.
            status = ""
            for condition in node.status.conditions:
                if condition.type == "Ready":
                    status = condition.status

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
def services(args, v1):
    services = v1.list_service_for_all_namespaces(
        watch=False,
        field_selector=args.field_selector
    )

    # Check services before listing
    if services:
        for service in services.items:

            # Append information to output list
            output.append({
                "{#SERVICE}": service.metadata.name,
                "namespace": service.metadata.namespace,
                "service": service.metadata.name,
                "uid": service.metadata.uid
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))


if __name__ == "__main__":

    # Declare variables
    output = [] # List for output data

    # Parse command-line arguments
    parser = ArgumentParser(
        description="Discover and retrieve metrics from Kubernetes.",
    )

    # Use sub-parsers run functions using mandatory positional argument
    subparsers = parser.add_subparsers()
    parser_pods = subparsers.add_parser("pods")
    parser_pods.set_defaults(func=pods)
    parser_services = subparsers.add_parser("services")
    parser_services.set_defaults(func=services)
    parser_nodes = subparsers.add_parser("nodes")
    parser_nodes.set_defaults(func=nodes)

    # Each subparser has the same optional arguments. For now.
    for item in [parser_pods, parser_nodes, parser_services]:
        item.add_argument("-c", "--config", default="", dest="config",
                            type=str,
                            help="Configuration file for Kubernetes client.")
        item.add_argument("-f", "--field-selector", default="",
                            dest="field_selector", type=str,
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
        print("Unable to load Kubernetes configuration file. Error: {}".format(
            e
        ))
        sys.exit()

    # Initialize Kubernetes client
    v1 = client.CoreV1Api()

    # Run specified mode
    args.func(args, v1)
