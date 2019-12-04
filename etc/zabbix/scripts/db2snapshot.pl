#!/usr/bin/perl -wT
# Version: 1.0
# Usage: db2snapshot <dbname> <lines>
#
# dbname    - Name of db2 database
# lines     - How many lines to output

use File::Spec;

# Directory where snapshots are cached.
my $SNAPSHOT_DIR = File::Spec->tmpdir();

# Get database path, name and timeout args
my $dbname = shift @ARGV;
my $lines = shift @ARGV;

# Untaint
if ($lines =~ /^(\d+)$/) {
  $lines = $1;
} else {
  die "Bad lines value";
}

if ($dbname =~ /^([-\w.]+)$/) {
  $dbname = $1;
} else {
  die "Bad dbname argument";
}

# Generate stat file name
my $statfile = "$SNAPSHOT_DIR/$dbname.txt";

# Open db2 snapshot file and output x lines
my $i=1;
open FILE, "<$statfile";
while (<FILE>) {
  if ($i >$lines) {
    last;
  }
  print $_;
  $i++;
}
