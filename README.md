# Zabbix Monitoring Scripts

This project contains various custom Zabbix monitoring scripts used as user parameters by Zabbix agent.

## Installation

The repository includes ready-to-install files for Zabbix Agent.

* Copy the files under [etc/zabbix/scripts](etc/zabbix/scripts) to `/etc/zabbix/scripts`
* Copy the files under [etc/zabbix/zabbix_agentd.d](etc/zabbix/zabbix_agentd.d) to `/etc/zabbix/zabbix_agentd.d`

## Templates

Each monitoring script has a corresponding template that can be imported to Zabbix Server. Templates can be found under [templates](templates).

## Usage

See the below documentation for each monitoring script.

- [DB2 database snapshot statistics](documentation/db2stat.md)
- [Docker discovery and monitoring](documentation/docker.md)
- [Process discovery and monitoring](documentation/process.md)
- [Pacemaker monitoring](documentation/pacemaker.md)
