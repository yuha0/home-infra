# Tailscale Subrouter

Run a Tailscale Subrouter in Kubernetes.

The manifest files are based on [upstream example directory](https://github.com/tailscale/tailscale/tree/9cbb0913bec6b37c019357a8e05b461ee1917a69/docs/k8s), with a few changes. Most significantly:

- debug server is enabled to get prometheus metrics
- auth key and app states are split into two different secret objects.
- pod is managed by a statefulset with a consistent hostname.
