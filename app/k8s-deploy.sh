#!/bin/sh
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 3650 -nodeskubect
# kubectl create secret tls tlssecret --cert=./cert.pem --key=./key.pem
kubectl apply -f ./secret.yaml
kubectl apply -f ./k8s-public.yaml

