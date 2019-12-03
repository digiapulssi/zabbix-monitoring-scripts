# How to test db2stat.pl in a docker container

IBM Db2 docker container URL
https://hub.docker.com/r/ibmcom/db2

Download and run docker container
```
docker run -itd --name mydb2 --privileged=true -p 50000:50000 -e LICENSE=accept -e DB2INST1_PASSWORD=root -e DBNAME=testdb -v /tmp/database:/database ibmcom/db2
```

Log on to the container
```
docker exec -ti mydb2 bash
```

Set correct rights for database configurations
```
groupadd sysmon
usermod -a -G sysmon db2inst1
```

Install nano and perl
```
yum install -y nano perl
```

Switch to user db2inst1
```
su - db2inst1
```

Modify database configuration file
```
db2 update dbm cfg using sysmon_group sysmon
```

Start the Db2 command line application
```
db2
```

Connect to database
```
connect to testdb user db2inst1 using root
```

Create table and insert test data into it
```
CREATE TABLE test (sarake1 INT PRIMARY KEY NOT NULL);
INSERT INTO test VALUES (1);
INSERT INTO test VALUES (2);
INSERT INTO test VALUES (3);
```

Test database snapshot
```
get snapshot for database on testdb
```

Exit db2 command line
```
CTRL+D
```

Change directory to /tmp
```
cd /tmp
```

Create db2stat.pl using nano
- Change the db2 application path to the script into "/opt/ibm/db2/V11.5/bin/db2"
```
nano db2stat.pl
```

Test db2stat script
```
perl -T ./db2stat.pl 60 db2inst1 /opt/ibm/db2/V11.5/ testdb "Database status"
```

The script should return the output:
```
Active
```


## Alternative way using a docker with multiple Db2 instances

Angoca's Db2 docker container URL
https://github.com/angoca/db2-docker/tree/master/db2-install/expc

Download and run docker container
```
sudo docker run -i -t --privileged=true --name="db2inst1" -p 50000:50000 angoca/db2-install
```

Change directory to /tmp/db2_conf
```
cd /tmp/db2_conf
```

Update apt lists
```
apt update
```

Download and install nano and perl
```
apt install -y nano perl
```

Create a new database instance
```
./createInstance db2inst1
```

Create a new user for second instance
(User db2inst1 exists in docker container already)
```
useradd -g db2grp1 -m db2inst2
```

Set db2inst2 user password**
```
passwd db2inst2
```

Create new Db2 instance
```
./createInstance db2inst2
```

(If you received an error about invalid GUID for user "db2inst2", just change
the user GUID value to file "/tmp/db2_conf/db2expc_instance.rsp". The value is
set at the line "DB2_INST.UID". You can check the user GUID by running command
"id db2inst2".

Change directory to /tmp
```
cd /tmp
```

Create db2stat.pl using nano
- Change the db2 application path to the script into "/opt/ibm/db2/V11.5/bin/db2"
- Change the cp and touch command paths to "/bin/cp" and "/bin/touch".
```
nano db2stat.pl
```

Change group and permissions for db2stat.pl file
```
chgrp db2grp1 db2stat.pl
chmod 770 db2stat.pl
```

Switch user
```
su - db2inst1
```

Start the database manager
```
db2start
```

Start the Db2 command line application
```
db2
```

Create a new database
```
create database testdb1 using codeset UTF-8 territory en
```

Connect to database
```
connect to testdb1 user db2inst1 using db2inst1
```

Create table and insert test data into it
```
CREATE TABLE test (sarake1 INT PRIMARY KEY NOT NULL)
INSERT INTO test VALUES (1)
INSERT INTO test VALUES (2)
INSERT INTO test VALUES (3)
```

Exit db2 command line
```
CTRL+D
```

Test db2stat.pl script
```
perl -T ./db2stat.pl 60 db2inst1 /opt/ibm/db2/V11.5/ testdb1 "Database status"
```

The script should return the output:
```
Active
```

Exit db2inst1 user shell
```
exit
```

Switch user
```
su - db2inst2
```

Start the database manager
```
db2start
```

Start the Db2 command line application
```
db2
```

Create a new database
```
create database testdb2 using codeset UTF-8 territory en
```

Connect to database
```
connect to testdb2 user db2inst2 using db2inst2
```

Create table and insert test data into it
```
CREATE TABLE test (sarake1 INT PRIMARY KEY NOT NULL)
INSERT INTO test VALUES (1)
INSERT INTO test VALUES (2)
INSERT INTO test VALUES (3)
```

Exit db2 command line
```
CTRL+D
```

Test db2stat.pl script
```
perl -T ./db2stat.pl 60 db2inst2 /opt/ibm/db2/V11.5/ testdb2 "Database status"
```

The script should return the output:
```
Active
```

Exit db2inst2 user shell
```
exit
```
