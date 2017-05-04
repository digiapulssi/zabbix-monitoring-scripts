Discovery script for top processes, based on CPU and memory consumption
Designed to be usable in both Linux and AIX systems. Generates process status
files under the workdir configured in beginning of the script that needs to
have write permissions. Files are cleaned when their age exceeds 1 day.
Uses ps command for all functionality.

# Usage:
# Without parameters:
- will print the JSON for discovered processes for Zabbix to use
# With parameters: cpu|mem|time <command_name> <ppid> filter
- cpu -> gives the summed cpu percentage from child threads
- mem -> gives the summed memory in bytes from child threads
- time -> gives the time in seconds for longest running thread matching
- \<command_name\> as seen by the ps command
- \<md5\> -> optional parameter, md5 sum returned by discovery which is
  calculated with from full command arguments. Prevents losing process history
  due to new ppid
- \<ppid\> -> optional parameter for the main pid, to return stats only for
  the child processes of the given ppid. Without it will give summed stats
  for all processes based on <command_name> only.
- filter -> will filter calculation based on command name and ignores
  sub processes that are spawned with different command

# Example commands:
    zabbix_discover_processes.pl cpu java
    -> summed up cpu of java processes and their children since last check
    zabbix_discover_processes.pl cpu java 9691f8c443d519f7eada3c646dc42fed
    -> the cpu for java process which md5 is given in parameter and it's
      children. MD5 is calculated from full command arguments as seen by
      ps command
    zabbix_discover_processes.pl cpu java 1564
    -> the cpu for java thread 1564 and all it's children
    zabbix_discover_processes.pl cpu java 1564 filter
    -> the cpu of the children of java thread 1564, but only ones
       where the command is "java"
    zabbix_discover_processes.pl mem java filter
    -> summed up memory for processes where command is "java", but not their
       children
    zabbix_discover_processes.pl time java
    -> the longest running java process elapsed time
    zabbix_discover_processes.pl time java 1564
    -> the elapsed time for java thread 1564

The discovery sensitivity can be adjusted with the CPU_THRESHOLD (in
percentage) and MEMORY_THRESHOLD (in Kb). These are used per thread, and not
summed up. If either threshold is exceeded, the process is picked up for
discovery. The discover will find the main command for the thread in
question and report it to Zabbix in the returned JSON.

E.g. setting CPU value to 1.0 means that threads that exceed or equal 1.0%
CPU usage will be noticed and reported to Zabbix. Percentage is calculated
based on last values when the script was run, so it depends on how often the
discovery is run in Zabbix. When running for the first time, script counts
the CPU usage using the whole thread lifetime as basis.

Memory is reported as the current memory usage in Kb per thread, so setting
this to E.g. 200000 would mean that any thread using more than 200 Mb memory
will get monitored.

Setting either of the variables to 0 means that all processes will be
monitored.

# Installation:
Put the script into /etc/zabbix/scripts folder and the configuration file
into /etc/zabbix/zabbix_agentd.d/ folder. Import the template into Zabbix.
After enabling the discovery template, process statistics should appear into 
Zabbix. 


NOTE: The CPU is more accurate when check is done in larger intervals.
The sum is given as total across multiple threads that may span multiple CPU's
in multi core environment, and can be more than 100%.

NOTE: The memory reported does not take into account shared memory between
threads, and can exceed the real amount used and even the maximum memory in
the system in some special cases.

NOTE: The md5 sum is preferred in the examples to prevent losing process
history when ppid changes due to process restart. Since the process parameters
can be same for two parallel processes, this will cause them to be detected
as one process in zabbix. If this reduction in accuracy is not acceptable,
ppid should be used instead, but it will generate more items in Zabbix.

