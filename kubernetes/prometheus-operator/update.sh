#!/usr/bin/env bash

VERSION=$1
wget -O bundle.yaml https://github.com/prometheus-operator/prometheus-operator/releases/download/v${VERSION}/bundle.yaml
