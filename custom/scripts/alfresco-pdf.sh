#!/bin/bash
# Takes IP and port as an argument.
# Script gets content from given url. Returns lines only with "SUMMARY".
set -e
url='http://'${1}':'${2}'/alfresco/s/enterprise/admin/admin-testtransform-test?operation=getTransformationStatistics&arg1=&arg2=&arg3=pdf'

curl -v -s -H "OAM_REMOTE_USER:admin" $url --stderr - | grep SUMMARY
