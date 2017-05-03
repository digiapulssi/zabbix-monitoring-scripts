#!/usr/bin/perl -wT
################################################################################
# Discovery script for top processes, based on CPU and memory consumption
# Designed to be usable in both Linux and AIX systems. Generates process status
# files under the workdir configured in beginning of the script that needs to
# have write permissions. Files are cleaned when their age exceeds 1 day.
# Uses ps command for all functionality.
#
# Usage:
# Without parameters:
# - will print the JSON for discovered processes for Zabbix to use
# With parameters: cpu|mem|time <command_name> <ppid> filter
# - cpu -> gives the summed cpu percentage from child threads
# - mem -> gives the summed memory in bytes from child threads
# - time -> gives the time in seconds for longest running thread matching
# - <command_name> as seen by the ps command
# - <ppid> -> optional parameter for the main pid, to return stats only for
#   the child processes of the given ppid. Without it will give summed stats
#   for all processes based on <command_name> only.
# - filter -> will filter calculation based on command name and ignores
#   sub processes that are spawned with different command
#
# Example commands:
#   zabbix_discover_processes.pl cpu java
#    -> summed up cpu of java processes and their children since last check
#   zabbix_discover_processes.pl cpu java 1564
#    -> the cpu for java thread 1564 and all it's children
#   zabbix_discover_processes.pl cpu java 1564 filter
#    -> the cpu of the children of java thread 1564, but only ones
#       where the command is "java"
#   zabbix_discover_processes.pl mem java filter
#    -> summed up memory for processes where command is "java", but not their
#       children
#   zabbix_discover_processes.pl time java
#    -> the longest running java process elapsed time
#   zabbix_discover_processes.pl time java 1564
#    -> the elapsed time for java thread 1564
#
# The discovery sensitivity can be adjusted with the CPU_THRESHOLD (in
# percentage) and MEMORY_THRESHOLD (in Kb). These are used per thread, and not
# summed up. If either threshold is exceeded, the process is picked up for
# discovery. The discover will find the main command for the thread in
# question and report it to Zabbix in the returned JSON.
#
# E.g. setting CPU value to 1.0 means that threads that exceed or equal 1.0%
# CPU usage will be noticed and reported to Zabbix. Percentage is calculated
# based on last values when the script was run, so it depends on how often the
# discovery is run in Zabbix. When running for the first time, script counts
# the CPU usage using the whole thread lifetime as basis.
#
# Memory is reported as the current memory usage in Kb per thread, so setting
# this to E.g. 200000 would mean that any thread using more than 200 Mb memory
# will get monitored.
#
# Setting either of the variables to 0 means that all processes will be
# monitored.
#
# NOTE: The CPU is more accurate when check is done in larger intervals.
# The sum is given as total across multiple threads that may span multiple CPU's
# in multi core environment, and can be more than 100%.
#
# NOTE: The memory reported does not take into account shared memory between
# threads, and can exceed the real amount used and even the maximum memory in
# the system in some special cases.
################################################################################
$ENV{PATH} = "/bin";
use strict;
use warnings;
use File::Spec;
use Digest::MD5 qw(md5 md5_hex md5_base64);

my $WORKDIR = File::Spec->tmpdir();

my $CPU_THRESHOLD = 1.5; # percentage
my $MEMORY_THRESHOLD = 200000; # in Kb
my $ps_regex = qr/^(.+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+([\d\-:]+)\s+([\d\-:]+)\s+(.+)$/;
my $clean_regex = qr/[^0-9a-zA-Z_\-]/; # clean up regex
my $clean_file_regex = qr/[^0-9a-zA-Z_]/; # clean up regex for files
my $user = getlogin || getpwuid($<) || "tmpuser";
my $WORKDIR_USER = "${WORKDIR}/zabbix_discover_processes_${user}";

if (not -e "$WORKDIR_USER") {
  mkdir "$WORKDIR_USER";
  chdir "$WORKDIR_USER";
} else {
  chdir "$WORKDIR_USER";
}

# discovery only, get the list of processes
if (not @ARGV) {
  discover();
} else {
  my ($stat_arg, $pname_arg, $limit1_arg, $limit2_arg) = @ARGV;
  checkProcesses($stat_arg, $pname_arg, $limit1_arg, $limit2_arg);
}

sub discover {

  my $first = 1;
  # create hash to speed things up a bit
  my %ps_hash = ();

  for my $line (`ps -A -o comm,pid,ppid,user,pcpu,pmem,rssize,time,etime,command`) {
    # skip heading line
    if ($first)
    {
      $first = 0;
      next;
    }

    if ($line eq "") {
      next;
    }

    my ($comm, $pid, $ppid, $user, $pcpu, $pmem, $rss, $time, $etime, $full_command)
      = $line =~ m/$ps_regex/;

    # if for some reason we can't determine the command, skip
    # this is because AIX system ps command returns <defunct>, <exiting> and
    # <idle> processes with no valid data
    if (not defined $comm) {
      # print unsupported line to log
      open(my $fh, ">", "last_error")
        or die "Cannot update last_error file.\n";
      print $fh $line;
      chmod 0660, $fh;
      close $fh;
      next;
    }

    my $md5 = "";
    # fill the hash
    my %stat_hash = ();
    $stat_hash{"pid"} = $pid;
    $stat_hash{"ppid"} = $ppid;
    $stat_hash{"user"} = $user;
    $stat_hash{"pcpu"} = $pcpu;
    $stat_hash{"pmem"} = $pmem;
    $stat_hash{"rss"} = $rss;
    $stat_hash{"time"} = $time;
    $stat_hash{"etime"} = $etime;
    # special characters are always removed from command
    $comm =~ s/$clean_regex//g;
    $stat_hash{"comm"} = $comm;
    # calculate MD5 for the full command, to try to distinguish between
    # parallel main processes
    $md5 = md5_hex($full_command);
    $stat_hash{"md5"} = $md5;
    $ps_hash{$pid} = \%stat_hash;
  }


  my $cpu_tot = 0.0;
  my @processes = ();

  # for discovery, use only one stat file and don't touch process pid files
  my $discovery_file = "discovery_file";
  my %old_stats_hash = ();

  # untaint the file
  if ($discovery_file =~ /^(\w+)$/) {
    $discovery_file = $1;
  } else {
    print "Unsecure file variable: $discovery_file\n";
    die;
  }

  # read old ps output if the file exists
  if (-e $discovery_file) {
    open(my $fh, "<", $discovery_file)
      or die "Could not read $discovery_file";
    for my $line (<$fh>) {
      my ($pid) = $line =~ m/^\S+\s+(\d+)\s+\d+.*/;
      $old_stats_hash{$pid} = $line;
    }
    close $fh;
    # to update the discover_file, old one must be deleted
    unlink $discovery_file;
  }

  # iterate processes and check stats to detect which processes should be
  # discovered when comparing to threshold values
  for my $pid (keys %ps_hash) {

    my $comm = $ps_hash{$pid}{"comm"};
    my $ppid = $ps_hash{$pid}{"ppid"};
    my $user = $ps_hash{$pid}{"user"};
    my $pcpu = $ps_hash{$pid}{"pcpu"};
    my $pmem = $ps_hash{$pid}{"pmem"};
    my $rss = $ps_hash{$pid}{"rss"};
    my $time = $ps_hash{$pid}{"time"};
    my $etime = $ps_hash{$pid}{"etime"};
    my $md5 = $ps_hash{$pid}{"md5"};
    my $old_stat = "";

    # find out if this is the root process, safeguard against trying to
    # calculate it
    if (not exists $ps_hash{$ppid} or $pid eq $ppid) {
      next;
    }

    # check if the process can be found in the discovery_file
    if (defined $old_stats_hash{$pid}) {
        $old_stat = $old_stats_hash{$pid};
    }

    if ( $old_stat eq "") {
      # no old statistics found, means this is new process
      $old_stat = join " ", $comm, $pid, $ppid, $user, $pcpu, $pmem, $rss, "00:00:00", "00:00", $md5;
    }

    my ($time_old, $etime_old) = $old_stat =~ m/^$comm.+\s+([\d\-:]+)\s+([\d\-:]+)\s+.+$/;

    if (not defined($time_old) or not defined($etime_old)) {
      die "Error in determining process times.\n";
    }

    my $psec = seconds($time);
    my $psec_old = seconds($time_old);
    my $esec = seconds($etime);
    my $esec_old = seconds($etime_old);
    my $cpu = 0;

    if ($esec - $esec_old gt 0) {
      $cpu = (100 * ($psec - $psec_old)) / ($esec - $esec_old);
    }

    # only discover processes that have used cpu time
    # also use threshold memory in Kb for process detection
    if ($cpu >= $CPU_THRESHOLD or $rss >= $MEMORY_THRESHOLD) {
      push @processes, $pid;
    }

    # update the discovery_file
    open(my $fh, ">>", $discovery_file)
      or die "Cannot update $discovery_file\n";
    print $fh join " ", $comm, $pid, $ppid, $user, $pcpu, $pmem, $rss, $time, $etime, $md5;
    print $fh "\n";
    chmod 0660, $fh;
    close $fh;
  }

  # print the JSON for discovery
  $first = 1;
  print "{\n";
  print "\t\"data\":[\n\n";
  my @main_pids = ();
  my @main_md5s = ();
  for my $pid (@processes)  {
    my $comm = $ps_hash{$pid}{"comm"};
    my $user = $ps_hash{$pid}{"user"};


    # find the main pid for this command using subroutine
    my $main_pid = findMainProc($pid,$comm,\%ps_hash);


    # filter processes for which the main pid has already been found
    if ( grep( /^$main_pid$/, @main_pids ) ) {
      next;
    }

    # filter processes for which the main md5 has already been found
    my $main_md5 = $ps_hash{$pid}{"md5"};
    if ( grep( /^$main_md5$/, @main_md5s ) ) {
      next;
    }
    push @main_pids, $main_pid;
    push @main_md5s, $main_md5;

    if ($first)
    {
      $first = 0;
    } else {
      print "\t,\n";
    }

    print "\t{\n";
    print "\t\t\"{#PROCESSNAME}\":\"$comm\",\n";
    print "\t\t\"{#PID}\":\"$pid\",\n";
    print "\t\t\"{#MAIN_PID}\":\"$main_pid\",\n";
    print "\t\t\"{#MAIN_MD5}\":\"$main_md5\",\n";
    print "\t\t\"{#USER}\":\"$user\"\n";
    print "\t}\n";
  }
  print "\n\t]\n";
  print "}\n";

  # clean files that are older than one day
  foreach my $file (glob("${WORKDIR_USER}/*")) {
    my $age = -M $file;
    if ($age > 1) {
      unlink $file;
    }
  }
}

sub checkProcesses {
  my ($stat_arg, $pname_arg, $limit1_arg, $limit2_arg) = @_;

  # getting the stat for given process
  if (not defined($pname_arg)) {
    print "Command name required. Exiting.\n";
    exit 1;
  }


  if (not defined $stat_arg) {
    # require also stat as argument
    print "No stat argument given. One of cpu|mem|time required. Exiting.\n";
    exit 1;
  } elsif (not $stat_arg =~ m/^(cpu|mem|time)$/) {
    print "Invalid stat argument given, supported: cpu|mem|time\n";
    exit 2;
  } elsif (defined($limit1_arg) && $limit1_arg !~ m/^\S+|filter$/) {
    # optional ppid | md5 | filter argument
    print "Invalid PID or command filter argument given. Exiting.\n";
    exit 2;
  } elsif (defined($limit2_arg) && $limit2_arg !~ m/^\S+|filter$/) {
    print "Invalid PID or command filter argument given. Exiting.\n";
    exit 2;
  }

  # clean the command parameter of unwanted characters
  $pname_arg =~ s/$clean_regex//g;

  # set the limiting parameters according to the two limit arguments if defined
  my $command_filter = 0;
  my $main_pid_filter = 0;
  my $main_args_md5 = "";

  if ($limit1_arg && $limit1_arg =~ m/^filter$/) {
    $command_filter = 1;
  } elsif ($limit1_arg && $limit1_arg =~ m/^\d+$/) {
    $main_pid_filter = $limit1_arg; # pid given
  } elsif ($limit1_arg && $limit1_arg =~ m/^[0-9a-fA-F]+$/) {
    $main_args_md5 = $limit1_arg; # md5 arg filter given
  }

  if ($limit2_arg && $limit2_arg =~ m/^filter$/) {
    $command_filter = 1;
  } elsif ($limit2_arg && $limit2_arg =~ m/^\d+$/) {
    $main_pid_filter = $limit2_arg; # pid given
  } elsif ($limit2_arg && $limit2_arg =~ m/^[0-9a-fA-F]+$/) {
    $main_args_md5 = $limit2_arg; # md5 arg filter given
  }

  my $time_tot = 0, my $mem_tot = 0, my $cpu_tot= 0;

  # get the stats for all processes and sum them up
  my $first = 1;
  # create hash to speed things up a bit
  my %ps_hash = ();

  for my $line (`ps -A -o comm,pid,ppid,user,pcpu,pmem,rssize,time,etime,command`) {
    # skip heading line
    if ($first)
    {
      $first = 0;
      next;
    }

    if ($line eq "") {
      next;
    }

    my ($comm, $pid, $ppid, $user, $pcpu, $pmem, $rss, $time, $etime, $full_command) = $line
      =~ m/$ps_regex/;

    # if for some reason we can't determine the command, skip
    # this is because AIX system ps command returns <defunct>, <exiting> and
    # <idle> processes with no valid data
    if (not defined $comm) {
      # print unsupported line to log
      open(my $fh, ">", "last_error")
        or die "Cannot update last_error file.\n";
      print $fh $line;
      chmod 0660, $fh;
      close $fh;
      next;
    }

    # fill the hash
    my %stat_hash = ();
    my $md5 = "";
    $stat_hash{"pid"} = $pid;
    $stat_hash{"ppid"} = $ppid;
    $stat_hash{"user"} = $user;
    $stat_hash{"pcpu"} = $pcpu;
    $stat_hash{"pmem"} = $pmem;
    $stat_hash{"rss"} = $rss;
    $stat_hash{"time"} = $time;
    $stat_hash{"etime"} = $etime;
    $comm =~ s/$clean_regex//g;
    $stat_hash{"comm"} = $comm;
    # calculate MD5 for the full command, to try to distinguish between
    # parallel main processes
    $md5 = md5_hex($full_command);
    $stat_hash{"md5"} = $md5;
    $ps_hash{$pid} = \%stat_hash;
  }

  # 1. command given -> find each main process and go through all subs
  # 2. command and filter given -> find each main proc and sum only the named processes
  # 3. command and pid given -> find the one main process and go through all subs
  # 4. command pid and filter given -> find the main process, sum only the named processes
  # 5. command and md5 given -> find the one main process based on md5 calculated from command parameters

  my @main_pids = ();

  if ($main_args_md5) {
    for my $pid (keys %ps_hash) {
      my $md5 = $ps_hash{$pid}{"md5"};
      if ( $md5 eq $main_args_md5 ) {
        # this is the main proc we want to monitor
        push @main_pids, $pid;
      }
    }
  } elsif ($main_pid_filter) {
    push @main_pids, $main_pid_filter;
  }
  else {
    # sum based on command names
    # find the main pids
    my $main_pid;

    for my $pid (keys %ps_hash) {
      my $command = $ps_hash{$pid}{"comm"};
      if ($command eq $pname_arg) {

        $main_pid = findMainProc($pid,$command,\%ps_hash);
        # filter processes for which the main ppid has already been found
        if ( grep( /^$main_pid$/, @main_pids ) ) {
          next;
        }
        push @main_pids, $main_pid;
      }

    }
  }

  # loop through the selected PID:s
  for my $main_pid (@main_pids) {

    # and check every process against them
    for my $pid (keys %ps_hash) {
      my $comm = $ps_hash{$pid}{"comm"};
      my $ppid = $ps_hash{$pid}{"ppid"};

      # skip root process
      if (not exists $ps_hash{$ppid} or $pid eq $ppid) {
        next;
      }

      # if command_filter, skip all lines that are not for the defined command
      # skip other porcesses that are not being checked, if the limit filter is used
      if ($command_filter and $comm ne $pname_arg)
      {
        next;
      }

      my $is_child = isChildOrSelf($pid,$main_pid,\%ps_hash);

      # if this process is not child, skip it
      if (not $is_child) {
        next;
      }

      # gather remaining stats to variables for use
      my $user = $ps_hash{$pid}{"user"};
      my $pcpu = $ps_hash{$pid}{"pcpu"};
      my $pmem = $ps_hash{$pid}{"pmem"};
      my $rss = $ps_hash{$pid}{"rss"};
      my $time = $ps_hash{$pid}{"time"};
      my $etime = $ps_hash{$pid}{"etime"};
      my $md5 = $ps_hash{$pid}{"md5"};

      # calculate cpu percentage using elapsed time vs cpu time for each thread
      if ($stat_arg eq "cpu") {
        # get old stats for comparison, use current stats if they do not exist
        # which basically means that this is a new thread
        # use cleaned version of command for filename instead of command filter
        # this needs to be more strict because of perl taint rules
        (my $comm_file = $comm) =~ s/$clean_file_regex//g;

        my $stat_file = "${comm_file}.${pid}";
        my $old_stats = "";

        # untaint the file
        if ($stat_file =~ /^(\w+\.\d+)$/) {
          $stat_file = $1;
        } else {
          print "Unsecure file variable: $stat_file\n";
          die;
        }
        # read old stats from PID file if it exists
        if (-e $stat_file) {
          open(my $fh, "<", $stat_file)
            or die "Could not read '$stat_file'";
          $old_stats = <$fh>;
          close $fh;

        } else {
          # if stat file does not exist, this is a new thread without previous
          # measure point -> set time values to zero
          $old_stats = join " ", $comm, $pid, $ppid, $user, $pcpu, $pmem, $rss, "00:00:00", "00:00", $md5;
        }

        my ($time_old, $etime_old) = $old_stats =~ m/$comm.*\s+([\d\-:]+)\s+([\d\-:]+)\s+.*$/;
        if (not defined($time_old) or not defined($etime_old)) {
          die "Error in determining process times.\n";
        }

        my $psec = seconds($time);
        my $psec_old = seconds($time_old);
        my $esec = seconds($etime);
        my $esec_old = seconds($etime_old);
        my $cpu = 0;
        if ($esec - $esec_old gt 0) {
          $cpu = (100 * ($psec - $psec_old)) / ($esec - $esec_old);
        }

        $cpu_tot += $cpu;

        # update stats for this command.pid
        open(my $fh, ">", $stat_file)
          or die "Cannot update ${stat_file}\n";
        print $fh join " ",$comm, $pid, $ppid, $user, $pcpu, $pmem, $rss, $time, $etime, $md5;
        print $fh "\n";
        chmod 0660, $fh;
        close $fh;

      } elsif ($stat_arg eq "mem") {
        # use value returned by ps directly. This value does not account for
        # shared memory used between threads, so in multi thread application
        # the value will be larger than really used
        $mem_tot += ($rss * 1024);
      } elsif ($stat_arg eq "time") {
        # find the longest running thread and take time from it
        # does not take into difference between parallel processes that have
        my $runtime = seconds($etime);
        if ($runtime > $time_tot) {
          $time_tot = $runtime;
        }
      }
    }
  }

  if ($stat_arg eq "time") {
    print $time_tot;
    print "\n";
  } elsif ($stat_arg eq "cpu") {
    printf("%.2f", $cpu_tot);
    print "\n";
  } elsif ($stat_arg eq "mem") {
    print $mem_tot;
    print "\n";
  }
}

# convert the DD-hh:mm:ss format to seconds
sub seconds {
  my ($time) = shift;
  my $total = 0;
  if (not defined $time) {
    print "Cannot determine time!\n";
    die;
  }
  if ($time =~ m/^(\d+):(\d+)$/) {
    my ($min, $sec) = $time =~ m/^(\d+):(\d+)$/;
    $total = ($min * 60) + $sec;
  } elsif ($time =~ m/^(\d+):(\d+):(\d+)$/) {
    my ($hour, $min, $sec) = $time =~ m/^(\d+):(\d+):(\d+)$/;
    $total = ($hour * 3600) + ($min * 60) + $sec;
  } elsif ($time =~ m/^(\d+)-(\d+):(\d+):(\d+)$/) {
    my ($day, $hour, $min, $sec) = $time =~ m/^(\d+)-(\d+):(\d+):(\d+)$/;
    $total = ($day * 86400) + ($hour * 3600) + ($min * 60) + $sec;
  }
  return $total;
}


# helper to find the main process for given command
sub findMainProc {
  my ($check_pid,$find_comm,$ps_hash_ref) = @_;
  my %ps_hash = ();
  %ps_hash = %{$ps_hash_ref};
  my $main_pid = $check_pid;
  my $ppid = $ps_hash{$check_pid}{"ppid"};
  my $ppid_comm = $ps_hash{$ppid}{"comm"};

  if (not defined $ppid_comm or $check_pid eq $ppid) {
    # we went all the way to the root process, it is the parent
    $main_pid = $check_pid;
  } elsif ($ppid_comm eq $find_comm) {
    # check if the next parent is the main or does it also have matching parent
    $main_pid = findMainProc($ppid,$find_comm,\%ps_hash);
  }
  return $main_pid;
}

# helper to find out if the current PID is a descendant of given PPID
sub isChildOrSelf {
  my ($check_pid,$main_pid,$ps_hash_ref) = @_;
  my %ps_hash = ();

  %ps_hash = %{$ps_hash_ref};

  my $is_child = 0;

  # find out if the given pid is a child of the given ppid by iterating the
  # process chain upwards in from the ps output

  # get the ppid
  my $ppid = $ps_hash{$check_pid}{"ppid"};

  if ($check_pid eq $main_pid) {
    # the process being checked is the main process
    $is_child = 1;
  } elsif (not defined($ppid) or $ppid eq $check_pid) {
    # when the check goes all the way to 0 process, it has no parent
    $is_child = 0;
  } elsif ($ppid eq $main_pid) {
    $is_child = 1;
  } else {
    $is_child = isChildOrSelf($ppid,$main_pid,\%ps_hash);
  }
  return $is_child;
}
