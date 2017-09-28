Get Pacemaker status. Adding -v option to command prints a more verbose string. Otherwise the script returns decimal or single word statuses.

# Script Usage

Get the cluster status in verbose format:
	pacemaker_status.py -i cluster -v
Get the simple cluster status,  0 if no nodes, 1 if running ok, 2 if any in standby 3 if any in maintenance, 4 if any in shutdown:
	pacemaker_status.py -i cluster
Count the resources in given state. e.g. how many failed:
	pacemaker_status.py -i cluster -p failed
Get status of the single resource. Returns count of resources running:
	pacemaker_status.py -i resource -n Grafana
Get the property value for single resource in given node. If node is not given returns true if all the nodes have the property set to "true":
	pacemaker_status.py -i resource -n Grafana -N application1 -p managed
Get the status on node, returns count of services running:
	pacemaker_status.py -i node -n application1
Get the status on node, returns verbose string of resource status:
	pacemaker_status.py -i node -n application1 -v
Get the nodes where resource is active. Returns in format resource:node1,node2
	pacemaker_status.py -i resource -n Grafana -l
Get all resources in the cluster and nodes where they are active. Returns each resource and the nodes, separated by space
	pacemaker_status.py -i cluster -l
	
# Example verbose output

	application1:online:standby:resources_running=0 application2:online:resources_running=10 resources=10/12
