# Monitoring Scripts for Zabbix Agents

This project contains various custom monitoring scripts for Zabbix agents.

## Using Individual Scripts

With usual Zabbix agent setup each script can be copied individually to
/etc/zabbix/scripts folder and enable respective UserParameter by copying
accompanying Zabbix agent configuration file from config folder to
/etc/zabbix/zabbix_agent.d folder.

Scripts may require additional setup or modification which is documented in
each script's own documentation.

## Provided Scripts

- [DB2 database snapshot statistics](documentation/db2stat.md)
- [Docker discovery and monitoring](documentation/zabbix_discover_docker.md)
- [Process discovery and monitoring](documentation/zabbix_discover_processes.md)
- [Pacemaker monitoring](documentation/pacemaker_status.md)
