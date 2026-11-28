#!/usr/bin/env bash

VERSION=$1
wget -O multus-daemonset.yml https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/v${VERSION}/deployments/multus-daemonset.yml
sed -i.bak "s|ghcr.io/k8snetworkplumbingwg/multus-cni:snapshot|ghcr.io/k8snetworkplumbingwg/multus-cni:v${VERSION}|g" multus-daemonset.yml
rm -f multus-daemonset.yml.bak
