#!/bin/sh
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodes
# openssl x509 -inform PEM -in cert.pem -outform DER -out cert.cer
# openssl x509 -inform PEM -in key.pem -outform DER -out key.cer
#docker build . --squash -t gmommoutlook/grader:slim-1.0
#docker build . -f ./Dockerfile-flask -t gmommoutlook/grader:slim-flask-1.0
# kubectl create secret tls tlssecret --cert=./cert.pem --key=./key.pem
#docker push gmommoutlook/grader:slim-flask-1.0
docker build . -t gmommoutlook/grader:slim-1.0
docker push gmommoutlook/grader:slim-1.0
