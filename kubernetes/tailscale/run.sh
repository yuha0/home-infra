# This file is modified based https://github.com/tailscale/tailscale/blob/3b55bf93062cc513a38a3dace3f49f48d3654202/docs/k8s/run.sh.
# The only modification is an added cli flag to enable debug server, in TAILSCALED_ARGS

# Copyright (c) 2022 Tailscale Inc & AUTHORS All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

#! /bin/sh

export PATH=$PATH:/tailscale/bin

TS_AUTH_KEY="${TS_AUTH_KEY:-}"
TS_ROUTES="${TS_ROUTES:-}"
TS_DEST_IP="${TS_DEST_IP:-}"
TS_EXTRA_ARGS="${TS_EXTRA_ARGS:-}"
TS_USERSPACE="${TS_USERSPACE:-true}"
TS_STATE_DIR="${TS_STATE_DIR:-}"
TS_ACCEPT_DNS="${TS_ACCEPT_DNS:-false}"
TS_KUBE_SECRET="${TS_KUBE_SECRET:-tailscale}"

set -e

TAILSCALED_ARGS="--socket=/tmp/tailscaled.sock --debug 0.0.0.0:8080"

if [[ ! -z "${KUBERNETES_SERVICE_HOST}" ]]; then
  TAILSCALED_ARGS="${TAILSCALED_ARGS} --state=kube:${TS_KUBE_SECRET}"
elif [[ ! -z "${TS_STATE_DIR}" ]]; then
  TAILSCALED_ARGS="${TAILSCALED_ARGS} --statedir=${TS_STATE_DIR}"
else
  TAILSCALED_ARGS="${TAILSCALED_ARGS} --state=mem:"
fi

if [[ "${TS_USERSPACE}" == "true" ]]; then
  if [[ ! -z "${TS_DEST_IP}" ]]; then
    echo "IP forwarding is not supported in userspace mode"
    exit 1
  fi
  TAILSCALED_ARGS="${TAILSCALED_ARGS} --tun=userspace-networking"
else
  if [[ ! -d /dev/net ]]; then
    mkdir -p /dev/net
  fi

  if [[ ! -c /dev/net/tun ]]; then
    mknod /dev/net/tun c 10 200
  fi
fi

echo "Starting tailscaled"
tailscaled ${TAILSCALED_ARGS} &
PID=$!

UP_ARGS="--accept-dns=${TS_ACCEPT_DNS}"
if [[ ! -z "${TS_ROUTES}" ]]; then
  UP_ARGS="--advertise-routes=${TS_ROUTES} ${UP_ARGS}"
fi
if [[ ! -z "${TS_AUTH_KEY}" ]]; then
  UP_ARGS="--authkey=${TS_AUTH_KEY} ${UP_ARGS}"
fi
if [[ ! -z "${TS_EXTRA_ARGS}" ]]; then
  UP_ARGS="${UP_ARGS} ${TS_EXTRA_ARGS:-}"
fi

echo "Running tailscale up"
tailscale --socket=/tmp/tailscaled.sock up ${UP_ARGS}

if [[ ! -z "${TS_DEST_IP}" ]]; then
  echo "Adding iptables rule for DNAT"
  iptables -t nat -I PREROUTING -d "$(tailscale --socket=/tmp/tailscaled.sock ip -4)" -j DNAT --to-destination "${TS_DEST_IP}"
fi

wait ${PID}
