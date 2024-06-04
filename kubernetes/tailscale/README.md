# Tailscale Subrouter

Run a Tailscale Subrouter in Kubernetes.

The manifest files are based on [upstream example directory](https://github.com/tailscale/tailscale/tree/bc4c8b65c7a7c161ad81ee4b1a82af3f529e710b/docs/k8s), with a few changes. Most significantly:

- debug server is enabled to get prometheus metrics
- auth key and app states are split into two different secret objects.
- pod is managed by a statefulset with a consistent hostname.
