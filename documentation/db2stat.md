
# DB2 Database Snapshot Statistics (db2stat)

This script generates database snapshots (i.e. get snapshot for database) from
DB2 and retrieves statistics from it.

Because DB2 install location varies by system and installation method, the path
to DB2 executable must be edited into PATH environment variable set up in the
script.

See the [script file](../scripts/db2stat) for detailed information.

## Item Configuration Examples

Note that each argument used to specify retrieved item must be placed within
double quotes to properly distinct between parameters.

Database status:
`db2stat[<dbname>,"Database status"]`

Current size of package cache heap for node 0:
`db2stat[<dbname>,"Node number" "0" "Memory Pool Type" "Package Cache Heap" "Current size (bytes)"]`
