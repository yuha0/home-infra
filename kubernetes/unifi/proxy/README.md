# Use cluster ingress as the reverse proxy for accessing Unifi console

This gives me proper HTTPS access to the console. Leaving only one HTTPS exception to manage in the whole home infrastructure, which is on the nginx ingress controller. Everything else should strictly verify server certificate issued by cert manager.
