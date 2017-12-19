#!/usr/bin/perl -wT
# Version: 1.0
# Usage: db2stat <timeout> <dbname> [<key> <value> ...] <stat>
#
# timeout   - Timeout of snapshot in seconds (new snapshot will be taken if
#             previous is older than timeout)
# dbname    - Name of db2 database
# key/value - Key value pairs to match (e.g. "Node number" "0")
# stat      - Actual stat to search for (e.g. "Database status")
#
# Generates snapshot from db2 into file in tmpdir directory if one does not
# already exist. The file is updated if it is older than specified timeout by
# taking new snapshot.
#
# After that searches for named stat line from generated file and returns its
# value. If key value pairs are specified, those must be found preceding the
# stat line in specified order and not have empty line in between.
#
# Note that key, value and stat are case sensitive and the way db2 uses
# capitalization is quite inconsistent.
#
# Examples:
#
# Retrieve simple stat "Database status" that is at most 10 seconds old:
# db2stat mydb 10 "Database status"
#
# Retrieve current size of package cache heap on node 0 at most 60 seconds old:
# db2stat mydb 60 "Node number" "0" "Memory Pool Type" "Package Cache Heap"
# "Current size (bytes)"

use File::Spec;

# Set this to path of db2 executable
$ENV{'PATH'} = "/usr/bin";

# Directory where snapshots are cached.
my $SNAPSHOT_DIR = File::Spec->tmpdir();

# Get database name and timeout args
my $timeout = shift @ARGV;
my $dbname = shift @ARGV;

# Untaint
if ($dbname =~ /^([-\w.]+)$/) {
  $dbname = $1;
} else {
  die "Bad dbname argument";
}

if ($timeout =~ /^(\d+)$/) {
  $timeout = $1;
} else {
  die "Bad timeout value";
}

# Generate stat file name
my $statfile = "$SNAPSHOT_DIR/$dbname.txt";

# Regenerate stats if file too old
if (! -f $statfile or (time - (stat($statfile))[10]) > $timeout) {
  system("db2 get snapshot for database on $dbname >$statfile");
}

# Generate regular expressions to match from args
while (@ARGV) {
  my $key = shift(@ARGV);
  my $value = shift(@ARGV);
  if (defined $value) {
    # Add preceding line match
    push(@RE, qr/\s*\Q$key\E\s*=\s*\Q$value\E\s*/);
  } else {
    # Add stat line match
    push(@RE, qr/\s*\Q$key\E\s*=\s*(.+)\s*/);
  }
}

# Try to find value with preceding line matches and stat line match
my $idx = 0;
open(DATA, "<$statfile");
while (<DATA>) {
  my $line = $_;
  if ($line =~ $RE[$idx]) {
    my $match = $1;

    # Return the match if all expressions have been matched
    $idx++;
    if ($idx == scalar @RE) {
      print "$match\n";
      exit 0;
    }
  }

  # Reset matches if empty line
  if ($line eq "") {
    $idx = 0;
  }
}
