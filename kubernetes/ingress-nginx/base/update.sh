#!/usr/bin/env bash

VERSION=$1
wget -O deploy.yaml https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-${VERSION}/deploy/static/provider/cloud/deploy.yaml
