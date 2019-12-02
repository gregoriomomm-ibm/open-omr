#!/bin/sh
result=$(curl -s -X POST -F formImage=@${1} http://localhost:5000/api/omr/parseJSON/dialogo/1000)
echo  "${result}\n"
