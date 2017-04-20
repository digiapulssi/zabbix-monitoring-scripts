#!/usr/bin/python
import os
import json
import argparse
import sys
import time
import re
import subprocess
import tempfile
from datetime import datetime
import glob

_STAT_RE = re.compile("(\w+)\s(\w+)")
# check debug mode given in container startup
_DEBUG = os.getenv("DEBUG", False)
# Set working dir, and create it if it does not exist via exception.
# The script assumes that the folders exists, and creates them
# in bootstrap when the script is run for the first time. This
# is to avoid having to check folder existing every time item is
# updated. User uid is used so that different users do not mixup the status
# files
_WRK_DIR=tempfile.gettempdir() + "/zabbix_discover_docker_" + str(os.getuid())
try:
	os.chdir(_WRK_DIR)
except Exception, e:
	if not os.path.isdir(_WRK_DIR):
		os.mkdir(_WRK_DIR)
	os.chdir(_WRK_DIR)

# discover containers
def discover():
	d = {}
	d["data"] = []

	command = "docker ps --format \"{{.Names}} {{.ID}}\""
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	dockerps, error = process.communicate()

	# test that the docker command succeeded, otherwise exit
	if len(error) > 0:
		print(error)
		sys.exit(1)

	for line in dockerps.splitlines():
		ps = {}
		ps["{#CONTAINERNAME}"] = line.strip().split()[0]
		ps["{#CONTAINERID}"] = line.strip().split()[1]
		d["data"].append(ps)

	print(json.dumps(d))

def count_running():
	command = "docker ps -q | wc -l"
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	output, error = process.communicate()

	if len(error) > 0:
		print(error)
		sys.exit(1)

	print(output.strip())

# status: 0 = no container found, 1 = running, 2 = closed, 3 = abnormal
def status(args):
	command = "docker inspect -f '{{json .State}}' " + args.container
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	status, error = process.communicate()

	# test that the docker command succeeded, otherwise exit
	if len(error) > 0:
		print(error)
		sys.exit(1)

	statusjs = json.loads(status)
	if statusjs["Running"]:
		print("1")
	elif statusjs["ExitCode"] == 0:
		print("2")
	else:
		print("3")

# get the uptime in seconds, if the container is running
def uptime(args):
	command = "docker inspect -f '{{json .State}}' " + args.container
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	status, error = process.communicate()

	# test that the docker command succeeded, otherwise exit
	if len(error) > 0:
		print(error)
		sys.exit(1)

	statusjs = json.loads(status)
	if statusjs["Running"]:
		uptime = statusjs["StartedAt"]
		start = time.strptime(uptime[:19], "%Y-%m-%dT%H:%M:%S")
		print(int(time.time() - time.mktime(start)))
	else:
		print("0")

# get the approximate disk usage
# alt docker inspect -s -f {{.SizeRootFs}} 49219085bdaa
# alt docker exec " + args.container + " du -s -b / 2> /dev/null
def disk(args):
	command = "docker inspect -s -f {{.SizeRootFs}} " + args.container
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	stat, error = process.communicate()

	# test that the docker command succeeded, otherwise exit
	if len(error) > 0:
		print(error)
		sys.exit(1)

	print(stat.strip())

def cpu(args):
	container_dir = "/sys/fs/cgroup/cpuacct"
	# cpu usage in nanoseconds
	cpuacct_usage_last = single_stat_check(args, "cpuacct.usage")
	cpuacct_usage_new = single_stat_update(args, container_dir, "cpuacct.usage")
 	last_change = update_stat_time(args, "cpuacct.usage.utime")
	# handle empty result, container not running anymore
	if cpuacct_usage_new == "":
		print("0")
		sys.exit(0)

	# time used in division should be in nanoseconds scale, but take into account
	# also that we want percentage of cpu which is x 100, so only multiply by 10 million
	time_diff = (time.time() - float(last_change)) * 10000000

	cpu = (int(cpuacct_usage_new) - int(cpuacct_usage_last)) / time_diff
	print("{:.2f}".format(cpu))

def net_received(args):
	container_dir = "/sys/devices/virtual/net/eth0/statistics"
	eth_last = single_stat_check(args, "rx_bytes")
	eth_new = single_stat_update(args, container_dir, "rx_bytes")
	if eth_new == "":
		print("0")
		sys.exit(0)
	last_change = update_stat_time(args, "rx_bytes.utime")
	# we are dealing with seconds here, so no need to multiply
	time_diff = (time.time() - float(last_change))
	eth_bytes_per_second = (int(eth_new) - int(eth_last))/ time_diff
	print(int(eth_bytes_per_second))

def net_sent(args):
	container_dir = "/sys/devices/virtual/net/eth0/statistics"
	eth_last = single_stat_check(args, "tx_bytes")
	eth_new = single_stat_update(args, container_dir, "tx_bytes")
	if eth_new == "":
		print("0")
		sys.exit(0)
	last_change = update_stat_time(args, "tx_bytes.utime")
	# we are dealing with seconds here, so no need to multiply
	time_diff = (time.time() - float(last_change))
	eth_bytes_per_second = (int(eth_new) - int(eth_last))/ time_diff
	print(int(eth_bytes_per_second))

# helper, fetch and update the time when stat has been updated
# used in cpu calculation
def update_stat_time(args, filename):
	try:
		with open(args.container + "/" + filename, "r+") as f:
			stat_time = f.readline()
			f.seek(0)
			curtime = str(time.time())
			f.write(curtime)
			f.truncate()
	except Exception, e:
		# When script is run for item needing the time of check, bootstrap it
		# with 1
		if not os.path.isfile(args.container + "/" + filename):
			debug(args.container + ": stat time file does not exist, creating " + filename)
			if not os.path.isdir(args.container):
				os.mkdir(args.container)
			# bootstrap with one second (epoch), which makes sure we dont divide
			# by zero and causes the stat calcucation to start with close to zero value
			stat_time = 1
			f = open(args.container + "/" + filename,"w")
			f.write(str(stat_time))
			f.close()
		else:
			debug(str(e))
			raise e
	return stat_time

# helper function to gather single stats
def single_stat_check(args, filename):

	try:
		with open(args.container + "/" + filename, "r") as f:
			stat = f.read().strip()
	except Exception, e:
		# When script is run for the first time, create directory.
		# this avoids having to check the directory every time for item.
		if not os.path.isfile(args.container + "/" + filename):
			debug(args.container + ": stat location does not exist, creating " + filename)
			if not os.path.isdir(args.container):
				os.mkdir(args.container)
			# first time running for this container, bootstrap with empty zero
			stat = "0"
			f = open(args.container + "/" + filename,"w")
			f.write(str(stat) + '\n')
			f.close()
		else:
			debug(str(e))
			raise e
	return stat

# helper function to update single stats
def single_stat_update(args, container_dir, filename):

	command = "docker exec " + args.container + " cat " + container_dir + "/" + filename
	process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
	stat, error = process.communicate()

	# test that the docker command succeeded, otherwise exit
	if len(error) > 0:
		print(error)
		sys.exit(1)
	try:
		f = open(args.container + "/" + filename,"w")
		f.write(stat)
		f.close()
	except Exception, e:
		# When script is run for the first time, create directory.
		# this avoids having to check the directory every time for item.
		if not os.path.isfile(args.container + "/" + filename):
			debug(args.container + ": stat location does not exist, creating " + filename)
			if not os.path.isdir(args.container):
				os.mkdir(args.container)
			open(args.container + "/" + filename,"w").write(stat)
		else:
			# This error should not happen, since updating happens after the check
			debug(args.container + ": could not update single stat file " + filename)
			debug(str(e))
			raise e
	return stat

# helper function to gather stat type data (multiple rows of key value pairs)
def multi_stat_check(args, filename):
	dict = {}
	try:
		with open(args.container + "/" + filename, "r") as f:
			for line in f:
				m = _STAT_RE.match(line)
				if m:
					dict[m.group(1)] = m.group(2)
	except Exception, e:
		# When script is run for the first time, create directory.
		# this avoids having to check the directory every time for item.
		if not os.path.isfile(args.container + "/" + filename):
			debug(args.container + ": stat location does not exist, creating " + filename)
			if not os.path.isdir(args.container):
				os.mkdir(args.container)
			# first time running for this container create empty file
			open(args.container + "/" + filename,"w").close()
		else:
			debug(str(e))
			raise e
	return dict

def multi_stat_update(args, container_dir, filename):
	dict = {}
	try:

		command = "docker exec " + args.container + " cat " + container_dir + "/" + filename
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		stat, error = process.communicate()

		# test that the docker command succeeded, otherwise exit
		if len(error) > 0:
			print(error)
			sys.exit(1)

		for line in stat.splitlines():
			m = _STAT_RE.match(line)
			if m:
				dict[m.group(1)] = m.group(2)
		f = open(args.container + "/" + filename,"w")
		for key in dict.keys():
			f.write(key + " " + dict[key] + "\n")
		f.close()
	except Exception, e:
		# When script is run for the first time, create directory.
		# this avoids having to check the directory every time for item.
		if not os.path.isfile(args.container + "/" + filename):
			debug(args.container + ": stat location does not exist, creating " + filename)
			if not os.path.isdir(args.container):
				os.mkdir(args.container)
			f = open(args.container + "/" + filename,"w")
			for key in dict.keys():
				f.write(key + " " + dict[key] + "\n")
			f.close()
		else:
			debug(args.container + ": could not update multi stat file " + filename)
			debug(str(e))
			raise e
	return dict


def memory(args):
	container_dir = "/sys/fs/cgroup/memory"

	memory_usage_last = single_stat_update(args, container_dir, "memory.usage_in_bytes")
	if memory_usage_last == "":
		print("0")
		sys.exit(0)

	print(memory_usage_last.strip())



def debug(output):
	if _DEBUG:
		if not "debuglog" in globals():
			global debuglog
			debuglog = open("debuglog","a")
		timestamp = time.strftime("%Y-%m-%d %H:%M:%S : ", time.gmtime())
		debuglog.write(timestamp + str(output)+"\n")


if __name__ == "__main__":


	if len(sys.argv) > 2:

		parser = argparse.ArgumentParser(prog="discover.py", description="discover and get stats from docker containers")
		parser.add_argument("container", help="container id")
		parser.add_argument("stat", help="container stat", choices=["status", "uptime", "cpu","memory", "disk", "netin", "netout"])
		args = parser.parse_args()

		# validate the parameter for container
		m = re.match("(^[a-zA-Z0-9-_]+$)", args.container)
		if not m:
			print("Invalid parameter for container id detected")
			debug("Invalid parameter for container id detected" + str(args.container))
			sys.exit(2)

		# stats that can be reported without container running
		if args.stat == "disk":
			debug("calling disk for " + args.container)
			disk(args)
			sys.exit(0)
		elif args.stat == "status":
			debug("calling status for " + args.container)
			status(args)
			sys.exit(0)
		elif args.stat == "uptime":
			debug("calling uptime for " + args.container)
			uptime(args)
			sys.exit(0)

		# check which containers are running, and print zero default value if not
		command = "docker ps --format \"{{.Names}} {{.ID}}\""
		process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		output,error = process.communicate()
		if len(error) > 0:
			print(error)
			sys.exit(1)
		out = re.findall(r"(?:^|[\s]+)("+args.container+")(?:[\s|$])+", output,re.DOTALL)
		if (not re.search(r"(?:^|[\s]+)("+args.container+")(?:[\s|$])+", output,re.DOTALL)):
			print("0")
			sys.exit(0)

		# call the correct function to get the stats
		elif args.stat == "cpu":
			debug("calling cpu for " + args.container)
			cpu(args)
		elif args.stat == "memory":
			debug("calling memory for " + args.container)
			memory(args)
		elif args.stat == "netin":
			debug("calling net_received for " + args.container)
			net_received(args)
		elif args.stat == "netout":
			debug("calling net_sent for " + args.container)
			net_sent(args)
	elif len(sys.argv) == 2:
		if sys.argv[1] == "count":
			debug("calling count")
			count_running()
	else:
		debug("discovery called.")
		discover()

	if "debuglog" in globals():
		debuglog.close()
