
# DB2 Database Snapshot Statistics (db2stat)

This script generates database snapshots (i.e. get snapshot for database) from
DB2 and retrieves statistics from it.

Because DB2 install location varies by system and installation method, the path
to DB2 executable must be edited into PATH environment variable set up in the
script.

Zabbix agent user must also have permission to create database snapshots. See
below on how to do this.

See the [script file](../scripts/db2stat) for detailed information.

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

## Item Configuration Examples

Note that each argument used to specify retrieved item must be placed within
double quotes to properly distinct between parameters.

Database status:
`db2stat[<dbname>,"Database status"]`

Current size of package cache heap for node 0:
`db2stat[<dbname>,"Node number" "0" "Memory Pool Type" "Package Cache Heap" "Current size (bytes)"]`
