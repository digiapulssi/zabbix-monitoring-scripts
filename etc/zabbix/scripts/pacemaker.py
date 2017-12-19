#!/usr/bin/python
# Version: 1.0
# Get Pacemaker status. Adding -v option to command prints a more verbose string
# Otherwise returns decimal or single word statuses.
#
# Get the cluster status in verbose format:
# 	pacemaker_status.py -i cluster -v
# Get the simple cluster status,  0 if no nodes, 1 if running ok, 2 if any in standby
# 3 if any in maintenance, 4 if any in shutdown
# 	pacemaker_status.py -i cluster
# Count the resources in given state. e.g. how many failed:
# 	pacemaker_status.py -i cluster -p failed
# Sum the failcount in cluster:
# 	pacemaker_status.py -i cluster -p fail-count
# Get status of the single resource. Returns count of resources running
# 	pacemaker_status.py -i resource -n Grafana
# Get the property value for single resource in given node. If node is not given
# returns true if all the nodes have the property set to "true".
# 	pacemaker_status.py -i resource -n Grafana -N application1 -p managed
# Get the status on node, returns count of services running
# 	pacemaker_status.py -i node -n application1
# Get the status on node, returns verbose string of resource status
# 	pacemaker_status.py -i node -n application1 -v
# Get the nodes where resource is active. Returns in format resource:node1,node2
# 	pacemaker_status.py -i resource -n Grafana -l
# Get all resources in the cluster and nodes where they are active. Returns each
# resource and the nodes, separated by space
#	pacemaker_status.py -i cluster -l
# Get last failure in cluster
#	pacemaker_status.py -i cluster -f


import argparse
import sys
import subprocess
from datetime import datetime
from lxml import etree

def process_xml():
	command = "sudo crm_mon -X"
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	xml, error = process.communicate()
	if error:
		print("Could not read command output:" + error)
		exit()
	try:
		root = etree.fromstring(xml)
	except Exception, e:
		if ("Connection to cluster failed: Transport endpoint is not connected" in xml):
			# cluster is not running, all queries default to 0
			print("0")
			exit()
		else:
			print("Could not get xml from crm_mon, check command righs.")
			print(xml)
			raise e
	return root

# simple check, return count of active nodes that are running
# or return true if property is true for the nodeset or node, otherwise false
# for fail-count, return the summed up fail-count
def resource_status_simple(args):
	root = process_xml()
	if args.property and args.property == "fail-count":
		xpath = "sum(/crm_mon/node_history/node/resource_history[@id = '" + args.name +"']/@fail-count)"
		if args.node:
			xpath = "sum(/crm_mon/node_history/node[@name='" + args.node + "']/resource_history[@id = '" + args.name +"']/@fail-count)"
		fail_count = root.xpath(xpath)
		print(fail_count)
	elif args.property:
		prop_status = "true"
		xpath = "/crm_mon/resources//resource[@id='" + args.name + "']/@" + args.property
		if args.node:
			# if a node was defined, check only that one with xpath, otherwise print false if
			# any of the nodes had false status
			xpath = "/crm_mon/resources//resource[node/@name = '" +args.node+ "'][@id='" + args.name + "']/@" + args.property
		props = root.xpath(xpath)
		for prop in props:
			if prop == "false":
				prop_status = "false"
		print(prop_status)
	else:
		xpath = "count(/crm_mon/resources//resource[@id='" + args.name + "' and (@role = 'Started' or 'Master')][@active='true'][@orphaned='false'][@managed='true'][@failed='false'][@failure_ignored='false'][@nodes_running_on > 0])"
		if args.node:
			# if a node was defined, check only that one with xpath
			xpath = "count(/crm_mon/resources//resource[node/@name = '" +args.node+ "'][@id='" + args.name + "' and (@role = 'Started' or 'Master')][@active='true'][@orphaned='false'][@managed='true'][@failed='false'][@failure_ignored='false'][@nodes_running_on > 0][node/@name = '" + args.node + "'])"
		count = root.xpath(xpath)
		print(count)

# check the status of given resource, return node:status for resources
def resource_status(args):
	root = process_xml()
	resource_status = ""
	if args.node:
		status = resource_verbose(root, args.node, args.name)
		xpath = "/crm_mon/resources//resource[@id='" + args.name + "'][node/@name = '" +args.node+ "']/@role"
		role_query = root.xpath(xpath)

		if role_query:
			role = role_query[0]
		else:
			role = "NotRunning"

		resource_status = args.node + ":" + role

		if status != "":
			resource_status += "[" + status + "]"

	else:
		# get list of nodes
		xpath = "/crm_mon/nodes/node/@name"
		nodes = root.xpath(xpath)

		# get status for each node
		for i in range(len(nodes)):
			if i > 0:
				resource_status += " "
			status = resource_verbose(root, nodes[i], args.name)
			xpath = "/crm_mon/resources//resource[@id='" + args.name + "'][node/@name = '" +nodes[i]+ "']/@role"
			role_query = root.xpath(xpath)
			if role_query:
				role = role_query[0]
			else:
				role = "NotRunning"

			resource_status += nodes[i] + ":" + role

			if status != "":
				resource_status += "[" + status + "]"

	print(resource_status)

# verbose resource printout, used for node and cluster also
def resource_verbose(root,node,resource):
	resource_status = ""
	resource_statuses = []

	xpath = "/crm_mon/resources//resource[@id='" + resource + "'][node/@name = '" + node + "']/@active"
	active = root.xpath(xpath)
	xpath = "/crm_mon/resources//resource[@id='" + resource + "'][node/@name = '" + node + "']/@orphaned"
	orphaned = root.xpath(xpath)
	xpath = "/crm_mon/resources//resource[@id='" + resource + "'][node/@name = '" + node + "']/@managed"
	managed = root.xpath(xpath)
	xpath = "/crm_mon/resources//resource[@id='" + resource + "'][node/@name = '" + node + "']/@failed"
	failed = root.xpath(xpath)
	xpath = "/crm_mon/resources//resource[@id='" + resource + "'][node/@name = '" + node + "']/@failure_ignored"
	failure_ignored = root.xpath(xpath)
	xpath = "/crm_mon/resources//resource[@id='" + resource + "'][node/@name = '" + node + "']/@nodes_running_on"
	nodes_running = root.xpath(xpath)
	xpath = "/crm_mon/node_history/node[@name='" + node + "']/resource_history[@id = '" + resource +"']/@fail-count"
	fail_count = root.xpath(xpath)


	if "false" in active:
		resource_statuses.append("inactive")
	if "false" in managed:
		resource_statuses.append("unmanaged")
	if "true" in orphaned:
		resource_statuses.append("orphaned")
	if "true" in failed:
		resource_statuses.append("failed")
	if "true" in failure_ignored:
		resource_statuses.append("failure_ignored")
	if "0" in nodes_running:
		resource_statuses.append("nodes_running_on=0")
	if fail_count:
		resource_statuses.append("fail-count=" + fail_count[0])

	resource_status += ",".join(resource_statuses)

	return resource_status

def node_status_simple(args):
	root = process_xml()
	xpath = "/crm_mon/nodes/node[@name='" + args.name + "']/@resources_running"
	count = root.xpath(xpath)
	if len(count) > 0:
		print(count[0])
	else:
		print("0")

# used also in cluster status
def node_verbose(root,node):
	xpath = "/crm_mon/nodes/node[@name='" + node + "']/@online"
	online = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node[@name='" + node + "']/@standby"
	standby = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node[@name='" + node + "']/@maintenance"
	maintenance = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node[@name='" + node + "']/@resources_running"
	resource_count = root.xpath(xpath)
	node_status = node

	if not(online):
		node_status += ":Not found"
	else:
		if (online[0] == 'true'):
			node_status += ":online"
		if (standby[0] == 'true'):
			node_status += ":standby"
		if (maintenance[0] == 'true'):
			node_status += ":maintenance"

		# prepare resources dict
		resources_status = {}
		xpath = "/crm_mon/resources//resource[node/@name = '" + node + "']/@id"
		resources = root.xpath(xpath)
		for resource in resources:
			resources_status[resource] = []

		# include also node history
		xpath = "/crm_mon/node_history/node[@name='"+node+"']/resource_history/@id"
		resources_history = root.xpath(xpath)
		for resource in resources_history:
			resources_status[resource] = []

		for resource in resources_status:
			status = resource_verbose(root,node,resource)
			if len(status) > 0:
				node_status += ":" + resource + "[" + status + "]"

		node_status += ":resources_running=" + resource_count[0]

	return node_status

def node_status(args):
	root = process_xml()
	node_status = node_verbose(root,args.name)
	print(node_status)

# print cluster status in a string of data
# includes resources information
def cluster_status():
	root = process_xml()
	cluster_status = ""

	xpath = "/crm_mon/nodes/node/@name"
	nodes = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node/@resources_running"
	res_running = root.xpath(xpath)
	xpath = "/crm_mon/summary/resources_configured/@number"
	res_configured = root.xpath(xpath)
	res_running_total = 0

	# gather a string of status data
	for i in range(len(nodes)):
		res_running_total += int(res_running[i])
		if i > 0:
			cluster_status += " "
		cluster_status += node_verbose(root,nodes[i])

	cluster_status += " resources=" + str(res_running_total) + "/" + str(res_configured[0])
	print(cluster_status)


# simple status, return 0 if no nodes, 1 if at running, 2 if any in standby
# 3 if any in maintenance, 4 if any in shutdown. 5 if status cannot be determined
# Does not care about resource level statuses.
def cluster_status_simple():
	root = process_xml()

	# if no nodes are found, or all nodes are offline
	cluster_status = "5"
	xpath = "/crm_mon/nodes/node/@online"
	online = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node/@maintenance"
	maintenance = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node/@standby"
	standby = root.xpath(xpath)
	xpath = "/crm_mon/nodes/node/@shutdown"
	shutdown = root.xpath(xpath)

	# any one node causes the status to increase
	for state in online:
		if state == "true":
			cluster_status = "1"
	for state in standby:
		if state == "true":
			cluster_status = "2"
	for state in maintenance:
		if state == "true":
			cluster_status = "3"
	for state in shutdown:
		if state == "true":
			cluster_status = "4"

	print(cluster_status)

# count statuses from all resources for given property
# e.g. how many failed, how many managed.
def cluster_statuses_simple(args):
	root = process_xml()

	if args.property == "nodes_running_on":
		print("Nonsensical parameter for cluster proprety count.")
		exit()
	elif args.property == "fail-count":
		xpath = "sum(/crm_mon/node_history/node/resource_history/@fail-count)"
		property_count = root.xpath(xpath)

	else:
		xpath = "count(/crm_mon/resources//resource[@" + args.property + " = 'true'])"
		property_count = root.xpath(xpath)

	print(property_count)

# print the resource locations where resources are active
def resource_location(args):
	root = process_xml()

	resource_locations = {}
	locations = ""
	xpath = "/crm_mon/resources//resource[@active = 'true']/@id"
	resources = root.xpath(xpath)

	for resource in resources:
		xpath = "/crm_mon/resources//resource[@active = 'true'][@id = '"+resource+"']/node/@name"
		nodes = root.xpath(xpath)
		resource_locations[resource] = nodes


	if (args.item == "cluster"):
		for resource in resource_locations:
			locations += resource + ":" + ",".join(resource_locations[resource]) + " "

	else:
		if len(resource_locations) == 0:
			print(args.name+":Not found")
			exit()
		locations = args.name +":"+ ",".join(resource_locations[args.name])

	print(locations)

# print last failures
def cluster_failures():
	root = process_xml()

	xpath = "/crm_mon/failures/failure/@op_key"
	failures = root.xpath(xpath)
	# get the latest failure
	if len(failures) > 0:
		failure_info = ""
		newest = datetime(1970, 1, 1, 0, 0)
		for failure in failures:

			xpath = "/crm_mon/failures/failure[@op_key = '"+failure+"']"
			element = root.xpath(xpath)
			#Sun Apr 16 21:46:27 2017
			failure_time = datetime.strptime(element[0].get("last-rc-change"), "%a %b %d %H:%M:%S %Y")
			if failure_time > newest:
				newest = failure_time
				failure_info += element[0].get("node")
				failure_info += ":" + element[0].get("op_key")
				failure_info += ":" + element[0].get("status")
				failure_info += ":" + element[0].get("last-rc-change")

		print(failure_info)

	else:
		# no failures
		exit()



if __name__ == "__main__":

	parser = argparse.ArgumentParser(prog="pacemaker_status.py", description="Check the pacemaker cluster status")
	parser.add_argument("-i", "--item", help="Item type to check", choices=["resource", "node", "cluster"])
	parser.add_argument("-n", "--name", help="Resource or node name to check.")
	parser.add_argument("-l", "--location", help="Return the node where is running.", action="store_true")
	parser.add_argument("-N", "--node", help="Node to check the resource in. Default checks all nodes.")
	parser.add_argument("-p", "--property", help="Check status of resource property", choices=["active","orphaned","managed","failed","failure_ignored","nodes_running_on","fail-count"])
	parser.add_argument("-v", "--verbose", help="Verbose status", action="store_true")
	parser.add_argument("-f", "--failures", help="Failures", action="store_true")

	if len(sys.argv) > 1:

		args = parser.parse_args()

		if (args.item == "resource"):
			if not(args.name):
				print("Must define resource name.")
			elif (args.verbose):
				resource_status(args)
			elif (args.location):
				resource_location(args)
			else:
				resource_status_simple(args)
		elif (args.item == "node"):
			if not(args.name):
				print("Must define node name.")
			elif (args.verbose):
				node_status(args)
			else:
				node_status_simple(args)
		elif (args.item == "cluster"):
			if (args.property):
				cluster_statuses_simple(args)
			elif (args.failures):
				cluster_failures()
			elif (args.verbose):
				cluster_status()
			elif (args.location):
				resource_location(args)
			else:
				cluster_status_simple()
	else:
		print("No arguments given. Nothing to do.")
		parser.print_help()
