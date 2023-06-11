#!/usr/bin/env bash

export GRAFANA_VERSION=$1
export SIDECAR_VERSION=$2

if [[ -z "$GRAFANA_VERSION" ]]; then
  echo 'first argument not defined. skip updating GRAFANA_VERSION'
else
  yq -i '.images[0].newTag=strenv(GRAFANA_VERSION)' kustomization.yaml
fi

if [[ -z "$SIDECAR_VERSION" ]]; then
  echo 'second argument not defined. skip updating SIDECAR_VERSION'
else
  yq -i '.images[1].newTag=strenv(SIDECAR_VERSION)' kustomization.yaml
fi
