This documentation is for configurating mysql and galera monitoring permissions.

1. Install Zabbix agent and MySQL client. If necessary, add the path to the mysql and mysqladmin utilities to the global environment variable PATH.
2. Create a MySQL user for monitoring (<password> at your discretion):
```
CREATE USER 'zbx_monitor'@'%' IDENTIFIED BY '<password>';
GRANT REPLICATION CLIENT,PROCESS,SHOW DATABASES,SHOW VIEW ON *.* TO 'zbx_monitor'@'%';
```
For more information, please see MySQL documentation https://dev.mysql.com/doc/refman/8.0/en/grant.html

3. Create .my.cnf in the home directory of Zabbix agent for Linux (/var/lib/zabbix by default ) or my.cnf in c:\ for Windows. The file must have three strings:
```
[client]
user='zbx_monitor'
password='<password>'
```

NOTE: Use systemd to start Zabbix agent on Linux OS. For example, in Centos use "systemctl edit zabbix-agent.service" to set the required user to start the Zabbix agent.

Add the rule to the SELinux policy (example for Centos):
```
# cat <<EOF > zabbix_home.te

module zabbix_home 1.0;

require {
        type zabbix_agent_t;
        type zabbix_var_lib_t;
        type mysqld_etc_t;
        type mysqld_port_t;
        type mysqld_var_run_t;
        class file { open read };
        class tcp_socket name_connect;
        class sock_file write;
}

============= zabbix_agent_t ==============

allow zabbix_agent_t zabbix_var_lib_t:file read;
allow zabbix_agent_t zabbix_var_lib_t:file open;
allow zabbix_agent_t mysqld_etc_t:file read;
allow zabbix_agent_t mysqld_port_t:tcp_socket name_connect;
allow zabbix_agent_t mysqld_var_run_t:sock_file write;
EOF
# checkmodule -M -m -o zabbix_home.mod zabbix_home.te
# semodule_package -o zabbix_home.pp -m zabbix_home.mod
# semodule -i zabbix_home.pp
# restorecon -R /var/lib/zabbix
```
  
4. To test mysql connection, run
  ```
  zabbix_agentd -t mysql.version
  zabbix_agentd -t mysql.get_status_variables
  ``` 
5. To test galera connection, run
  ```
  zabbix_agentd -t galera.cluster_status
  ```
