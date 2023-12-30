#!/usr/bin/env bash

VERSION=${1#"v"}
echo $VERSION
wget -O cnpg.yaml https://github.com/cloudnative-pg/cloudnative-pg/releases/download/v${VERSION}/cnpg-${VERSION}.yaml
