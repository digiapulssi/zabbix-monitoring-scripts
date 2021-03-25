# Zabbix Monitoring Scripts

This project contains various custom Zabbix monitoring scripts used as user parameters by Zabbix agent.

## Release Packaging

```
git checkout aix_version
git pull
cd etc/zabbix
tar czvf zabbix-monitoring-scripts-aix-<new version eg. 1.5>.tar.gz scripts zabbix_agentd
```

Next:
1. Unzip the package into a test directory (eg. /tmp) and check that all scripts have execute flag set.
2. Create a new version in github. Tag version: <new version eg. 1.5> @ aix-version. Attach the tar.gz file as a binary file to the release.

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
- [Process discovery and monitoring](documentation/process.md)
- [Pacemaker monitoring](documentation/pacemaker.md)
- [PEM file certificate monitoring](documentation/certificates.md)
- [Kontena grid monitoring](documentation/kontena_grid.md)
