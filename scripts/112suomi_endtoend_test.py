#!/usr/bin/python
import sys
import os
import datetime
import re
import json
import subprocess
from time import time, sleep

CLIENT="112suomi"
STATUS_FILE="endtoend_test_status"
#_WRK_DIR="/etc/zabbix/scripts/" + CLIENT
WRK_DIR="./"+CLIENT
TIMEOUT=3
POST_USER="mobile"
POST_PASS="Mi5HfJSigqk9_-FmZzmIxeSZd"
POST_URL="https://cloud-staging.112suomi.fi/v1/positions/"
#POST_URL="http://localhost:8082/v1/positions/"
GET_USER="hake"
GET_PASS="mlzRm7_c1JZwQTQcUhPGlhgHo"
GET_URL="https://cloud-staging.112suomi.fi/v1/event_logs/5551234567"
#GET_URL="http://localhost:8082/v1/event_logs/5551234567"

post_time=str(int(time() * 1000))
#post_time=1488961057630
post_data={}
post_data["mobile"] = "5551234567"
post_data["location"] = [23.764931,61.497978]
post_data["accuracy"] = 10
post_data["timestamp"] = post_time
POST_PAYLOAD = json.dumps(post_data)

# create workdir if it is not present
try:
	os.chdir(WRK_DIR)
	# clear the status file if it exists
	if os.path.isfile(STATUS_FILE):
		os.remove(STATUS_FILE)
except Exception, e:
	if not os.path.isdir(WRK_DIR):
		os.mkdir(WRK_DIR)
		os.chdir(WRK_DIR)

#curl -u mobile:Mi5HfJSigqk9_-FmZzmIxeSZd -H "Content-Type: application/json" -X POST -d @put "https://cloud-staging.112suomi.fi/v1/positions/"
#curl -u hake:mlzRm7_c1JZwQTQcUhPGlhgHo "https://cloud-staging.112suomi.fi/v1/event_logs/5551234567"



resp = ""
resp_data = {}
curl="curl -s -u "+POST_USER+":"+POST_PASS+" -H \"Content-Type: application/json\" -X POST -d \'" + POST_PAYLOAD +"\' \""+POST_URL+"\" --max-time " + str(TIMEOUT)

try:
	time_post_start=time()
	process = subprocess.Popen(curl, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	resp, error = process.communicate()
	time_post_end=time()

except Exception, e:
	print("Could not POST to " + POST_URL + "\n" + repr(e))
	exit()

if resp == "":
	print("Could not connect to server for POST: " + POST_URL)
	exit()

resp_data = json.loads(resp)
timestamp_post = resp_data['timestamp']

time_get_start=0
time_get_end=0

respg = ""
respg_data = {}

curl="curl -s -u "+GET_USER+":"+GET_PASS+ " " +  GET_URL + " --max-time " + str(TIMEOUT)
for i in range(3):
	time_get_start = time()
	try:
		process = subprocess.Popen(curl, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		respg, error = process.communicate()
		respg_data = json.loads(respg)
		time_get_end = time()
		timestamp_get=respg_data["events"][-1]["position"]["timestamp"]
		# if the timestamp matches the one which was sent, we have correct data
		if (timestamp_post == timestamp_get):
			break
		else:
			sleep(0.5)
	except Exception, e:
		print("Could not GET data from " + GET_URL + "\n" + repr(e))
		exit()


time_post_elapsed = int((time_post_end - time_post_start) * 1000 )

# if we did not get the timestamp, exit
if (timestamp_post != timestamp_get):
	print("Could not GET latest data!\n")
	f = open(STATUS_FILE,"w")
	f.write("POST=" + str(time_post_elapsed) + "\n")
	f.close()
	exit()


time_get_elapsed = int((time_get_end - time_get_start) * 1000 )
time_between_elapsed = int((time_get_start - time_post_end) * 1000 )
time_total_elapsed = time_post_elapsed + time_get_elapsed + time_between_elapsed

f = open(STATUS_FILE,"w")
f.write("POST=" + str(time_post_elapsed) + "\n")
f.write("GET=" + str(time_get_elapsed) + "\n")
f.write("BETWEEN=" + str(time_between_elapsed) + "\n")
f.write("TOTAL=" + str(time_total_elapsed) + "\n")
f.close
print time_total_elapsed
