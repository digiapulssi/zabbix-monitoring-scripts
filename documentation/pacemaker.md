# Pacemaker Monitoring

Get Pacemaker status. Adding -v option to command prints a more verbose string. Otherwise the script returns decimal or single word statuses.

See [user parameter configuration file](../etc/zabbix/zabbix_agentd.d/pacemaker.conf) for Zabbix item format.

## Script Usage

| Command | Description | Units |
| ------- | ----------- | ----- |
pacemaker_status.py -i cluster -v | Get the cluster status in verbose format | text |
pacemaker_status.py -i cluster | Cluster status in integer format | 0 if no nodes, 1 if running ok, 2 if any in standby 3 if any in maintenance, 4 if any in shutdown |
pacemaker_status.py -i cluster -p failed | Count the resources in given state. e.g. how many failed | number |
pacemaker_status.py -i resource -n Grafana | Get status of the single resource. Returns count of resources running | number |
pacemaker_status.py -i resource -n Grafana -N application1 -p managed | Get the property value for single resource in given node. | If node is not given returns true if all the nodes have the property set to "true" |
pacemaker_status.py -i node -n application1 | Get the status on node | returns count of services running |
pacemaker_status.py -i node -n application1 -v | Get the status on node | returns verbose string of resource status |
pacemaker_status.py -i resource -n Grafana -l | Get the nodes where resource is active. | Text format resource:node1,node2 |
pacemaker_status.py -i cluster -l | Get all resources in the cluster and nodes where they are active. | Returns each resource and the nodes, separated by space |
	
## Example verbose output

`application1:online:standby:resources_running=0 application2:online:resources_running=10 resources=10/12`
