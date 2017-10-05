
# DB2 Database Snapshot Statistics (db2stat)

This script generates database snapshots (i.e. get snapshot for database) from
DB2 and retrieves statistics from it.

Because DB2 install location varies by system and installation method, the path
to DB2 executable must be edited into PATH environment variable set up in the
script.

Zabbix agent user must also have permission to create database snapshots. See
below on how to do this.

See the [script file](../etc/zabbix/scripts/db2stat.pl) for detailed information.

## Enabling DB2 Snapshots for Zabbix User

To allow Zabbix agent user to create snapshots it must have capability in DB2
to do that. For monitoring purposes the best match is the SYSMON permission. The
operating system group for this is set via DB2 configuration parameters.

To enable snapshots:

1. Create sysmon group in operating system and add zabbix agent user to it (Zabbix agent must be installed so that zabbix user is present).
   - Linux systems: `groupadd sysmon && usermod -a -G sysmon zabbix`
   - AIX systems: `mkgroup sysmon && chgrpmem -m + zabbix sysmon`
2. Configure sysmon group have SYSMON permission in database execute following *as db2 user*:
   - Configure sysmon group: `db2 update dbm cfg using sysmon_group sysmon`
   - Restart databse: `db2stop && db2start`

To test taking the snapshot with zabbix user in Linux as root:
`su -s /bin/bash -c "<path-to-db2dir>/bin/db2 get snapshot for database on <db>" zabbix`

## Installing Items from Template

Zabbix template for all items supported in configuration is
[included](../templates/db2stat.xml). To configure it, at least macro
value for DATABASE_NAME must be updated.

## Manual Item Configuration

Provided user parameter configuration contains several parameters. Consult the
[configuration file](../etc/zabbix/zabbix_agentd.d/db2stat.conf) for a full list.

Simple statistics can be retrieved with two paramters, maximum snapshot age in seconds and database:

`db2stat.database_status[60,SAMPLE]`

Retrieving memory statistics additionally requires node number:

`db2stat.package_cache_heap_size[60,SAMPLE,0]`
