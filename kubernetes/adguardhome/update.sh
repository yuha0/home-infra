#!/usr/bin/env bash

export ADGUARD_VERSION=$1
export EXPORTER_VERSION=$2

if [[ -z "$ADGUARD_VERSION" ]]; then
  echo 'first argument not defined. skip updating ADGUARD_VERSION'
else
  yq -i '.images[0].newTag=strenv(ADGUARD_VERSION)' kustomization.yaml
fi

if [[ -z "$EXPORTER_VERSION" ]]; then
  echo 'second argument not defined. skip updating EXPORTER_VERSION'
else
  yq -i '.images[1].newTag=strenv(EXPORTER_VERSION)' kustomization.yaml
fi
