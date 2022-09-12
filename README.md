# Zabbix Monitoring Scripts

This project contains various custom Zabbix monitoring scripts used as user parameters by Zabbix agent.

## Installation

The repository includes ready-to-install files for Zabbix Agent.

* Copy the files under [etc/zabbix/scripts](etc/zabbix/scripts) to `/etc/zabbix/scripts`
* Copy the files under [etc/zabbix/zabbix_agentd.d](etc/zabbix/zabbix_agentd.d) to `/etc/zabbix/zabbix_agentd.d`

## Templates

Each monitoring script has a corresponding template that can be imported to Zabbix Server. Templates can be found under [templates](templates).

## Version Numbering Scheme

Each script has version information at the beginning of the script.
[Semantic versioning](https://semver.org/) scheme is used with major.minor syntax

* Major version changes when you make incompatible changes with existing items / configuration syntax
* Minor version changes when you add functionality or bug-fixes in backwards-compatible manner

## Usage

See the below documentation for each monitoring script.

- [DB2 database snapshot statistics](documentation/db2stat.md)
- [Docker discovery and monitoring](documentation/docker.md)
- [Docker Swarm service discovery and monitoring](documentation/docker_swarm.md)
- [Process discovery and monitoring](documentation/process.md)
- [Pacemaker monitoring](documentation/pacemaker.md)
- [PEM file certificate monitoring](documentation/certificates.md)
- [Kontena grid monitoring](documentation/kontena_grid.md)
- [Kubernetes monitoring](documentation/kubernetes_monitoring.md)
- [MySQL & Galera monitoring](documentation/mysql-galera.md)

