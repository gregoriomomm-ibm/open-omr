#!/bin/sh
result=$(curl -s -X POST -F formImage=@${1} http://184.172.250.217:30000/api/omr/parseJSON/dialogo/1000)
echo  "${result}\n"
