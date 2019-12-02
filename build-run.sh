#!/bin/sh
# time /usr/bin/python3 /home/gregoriomomm/workspace/ias/omr-slim/app/grader.py --debug True --certfile ./cert.pem --keyfile ./key.pem 
docker run -p 0.0.0.0:5000:5000/tcp -it gmommoutlook/grader:slim-1.0 sh                                                  