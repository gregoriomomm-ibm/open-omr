#!/bin/sh
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodes
openssl x509 -inform PEM -in cert.pem -outform DER -out cert.cer
openssl x509 -inform PEM -in key.pem -outform DER -out key.cer
# kubectl create secret tls tlssecret --cert=./cert.pem --key=./key.pem
