#!/usr/bin/python2

"""
Kubernetes monitoring
Version: 1.2

Usage:
python kubernetes_monitoring.py pods
python kubernetes_monitoring.py pods -c <config_file> -f <field_selector>

python kubernetes_monitoring.py nodes

python kubernetes_monitoring.py services

python kubernetes_monitoring.py cronjobs
python kubernetes_monitoring.py cronjobs -c <config_file> -f <field_selector>
python kubernetes_monitoring.py cronjobs -c <config_file> -f <field_selector>
                                         --instance-name <instance-name>
                                         --host-name <host-name>
"""

# Python imports
from argparse import ArgumentParser
import datetime
import json
import os
import sys

# Iiris imports
# from iiris_support.zabbix_api import ZabbixAPI
from zabbix_api import ZabbixAPI

# Retrieve timezone aware datetime objects
if sys.version_info[0] < 3:
    import pytz
    epoch_start = datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)
    system_time = datetime.datetime.now(pytz.utc)
else:
    epoch_start = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    system_time = datetime.datetime.now(datetime.timezone.utc)

# 3rd party imports
from kubernetes import client, config


# Loop cron jobs and create discovery
def cronjobs(args, v1):

    # Retrieve cron jobs from Kubernetes API v1
    api_client = client.ApiClient()
    api_instance = client.BatchV1Api(api_client)
    api_response = api_instance.list_job_for_all_namespaces(
        watch=False,
        field_selector=args.field_selector
    )

    # Declare variables
    cronjobs = {}
    start_interval = system_time - datetime.timedelta(minutes=args.minutes)

    # Check API response before listing
    if not api_response:
        raise Exception("Unable to retrieve API response.")

    # Loop API response items
    for item in api_response.items:

        # Reset loop variables
        completion_time = None
        job_length = 0
        job_name = None
        job_status = 0
        start_time = None

        # Discard active cron jobs
        if item.status.active is not None:
            continue

        # Check and convert completion time to epoch
        if item.status.completion_time:
            completion_time = int(
                (item.status.completion_time - epoch_start).total_seconds()
            )

        # Skip completed jobs that are outside the interval range
        if completion_time < start_interval:
            continue

        # Check and convert start time to epoch
        if item.status.start_time:
            start_time = int(
                (item.status.start_time - epoch_start).total_seconds()
            )

        # Calculate cron job length
        if completion_time and start_time:
            job_length = int(completion_time - start_time)

        # Only retrieve data from cron jobs
        for owner_reference in item.metadata.owner_references:
            if owner_reference.kind != "CronJob":
                continue

            # Retrieve job name
            job_name = owner_reference.name

        # If job name was not retrieved, kind was not CronJob
        if not job_name:
            continue

        # Check job status comparing succeeded and status fields
        if item.status.succeeded > 0 and item.status.failed is None:
            job_status = 1

        # Set job data to dictionary
        cronjobs[job_name] = {
            "{#CRONJOB}": job_name,
            "completion_time": completion_time,
            "length": job_length,
            "name": job_name,
            "start_time": start_time,
            "status": job_status,
            "uid": item.metadata.uid
        }

    # If instance name is not set, we output discovery
    if not args.instance_name:

        # Loop and append jobs to output list
        for cron_job in cronjobs:
            output.append(cronjobs[cron_job])

        # Dump discovery
        discovery = {"data": output}
        print(json.dumps(discovery))

    else:
        items = []

        # Append item data to list
        for cron_job in cronjobs:
            items.append([
                args.host_name,
                "kubernetes.cronjob[{}]".format(cronjobs[cron_job].get("name")),
                json.dumps(cronjobs[cron_job]),
                cronjobs[cron_job].get("completion_time")
            ])

        # Create ZabbixAPI class instance
        zapi = ZabbixAPI()

        # Try to login and send trapper data
        zapi.login(args.instance_name)
        result = zapi.send_multiple_trapper_data(args.instance_name, items)
        print(result)


# Loop pods and create discovery
def pods(args, v1):

    # Retrieve pods from Kubernetes API v1
    pods = v1.list_pod_for_all_namespaces(
        watch=False,
        field_selector=args.field_selector
    )

    # Check pods before listing
    if pods:
        for pod in pods.items:

            # Retrieve container's restart counts
            container_started = None  # Container's start time
            kind = None  # Pod's kind found under metadata.owner_references
            restart_count = 0  # Container's restart count
            started_at = None  # Latest start time
            uptime = datetime.timedelta()  # Datetime object for latest uptime

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

    # Retrieve nodes from Kubernetes API v1
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
                "node": next((i.address for i in node.status.addresses if i.type == "Hostname"), node.status.node_info.machine_id),
                "allocatable_cpu": node.status.allocatable.get("cpu"),
                "allocatable_storage": node.status.allocatable.get("ephemeral-storage"),
                "allocatable_memory": node.status.allocatable.get("memory"),
                "capacity_cpu": node.status.capacity.get("cpu"),
                "capacity_storage": node.status.capacity.get("ephemeral-storage"),
                "capacity_memory": node.status.capacity.get("memory"),
                "external_ip": next((i.address for i in node.status.addresses if i.type == "ExternalIP"), ""),
                "machine_id": node.status.node_info.machine_id,
                "status": status,
                "system_uuid": node.status.node_info.system_uuid
            })

    # Dump discovery
    discovery = {"data": output}
    print(json.dumps(discovery))


# Loop services and create discovery
def services(args, v1):

    # Retrieve services from Kubernetes API v1
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
    output = []  # List for output data

    # Parse command-line arguments
    parser = ArgumentParser(
        description="Discover and retrieve metrics from Kubernetes.",
    )

    # Use sub-parsers run functions using mandatory positional argument
    subparsers = parser.add_subparsers()
    parser_cronjobs = subparsers.add_parser("cronjobs")
    parser_cronjobs.set_defaults(func=cronjobs)
    parser_pods = subparsers.add_parser("pods")
    parser_pods.set_defaults(func=pods)
    parser_services = subparsers.add_parser("services")
    parser_services.set_defaults(func=services)
    parser_nodes = subparsers.add_parser("nodes")
    parser_nodes.set_defaults(func=nodes)

    # Each subparser has the same optional arguments. For now.
    for item in [parser_cronjobs, parser_pods, parser_nodes, parser_services]:
        item.add_argument("-c", "--config", default="", dest="config",
                          type=str,
                          help="Configuration file for Kubernetes client.")
        item.add_argument("-f", "--field-selector", default="",
                          dest="field_selector", type=str,
                          help="Filter results using field selectors.")
        item.add_argument("-i", "--instance-name", default="",
                          dest="instance_name", type=str,
                          help="Zabbix instance name for sending item data.")
        item.add_argument("-hn", "--host-name", default="",
                          dest="host_name", type=str,
                          help="Zabbix host name for sending item data.")
        item.add_argument("-m", "--minutes", default="",
                          dest="minutes", type=str,
                          help="Interval for cron job retrieval.")

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
