Discover and monitoring script for docker containers.

Requirements: 
- Python 2.7.13

# Usage: 
# Without parameters:
- will print the JSON for discovered processes for Zabbix to use
- Returns names and short id of docker containers.
# With parameters: <container_name>|count uptime|cpu|memory|disk|netin|netout
- count -> gives the total amount of containers running in host
- uptime -> gives the uptime of container in seconds
- cpu -> gives the cpu usage of container, as seen by the container OS
- memory -> gives the free memory as seen by the container OS
- disk -> gives approximated container size in disk
- netin -> inbound network traffic to the container in bytes/second
- netout -> outbound network traffic from the containr in bytes/second

# Example commands:
    zabbix_discover_docker.py count
    zabbix_discover_docker.py my_container cpu
 
# Installation:
Put the script into /etc/zabbix/scripts folder and the configuration file
into /etc/zabbix/zabbix_agentd.d/ folder. Import the template into Zabbix.
After enabling the discovery template, docker container statistics should
appear into Zabbix.
 
NOTE: The monitored host needs to have read/write permission for zabbix agent 
in the /etc/zabbix/scripts folder. 
