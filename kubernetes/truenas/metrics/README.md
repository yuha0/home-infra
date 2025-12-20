# Collect TrueNAS metrics

Follow the guide in [Supporterino/truenas-graphite-to-prometheus](https://github.com/Supporterino/truenas-graphite-to-prometheus):

## Steps:

### 1. Run `graphite_exporter` on TrueNAS

Graphite plaintext protocol doesn't work very well over long-lived TCP connections behind
Cilium BGP LB, likely ECMP causing partial writes and reconnects and netdata complains `netdata ERROR : MAIN : EXPORTING: failed to write data to '10.200.0.5:9109'. Willing to write 34496 bytes, wrote 8286 bytes. Will re-connect. (errno 11, Resource temporarily unavailable)`.

Just run the exporter on TrueNAS for simplicity:

https://github.com/Supporterino/truenas-graphite-to-prometheus/blob/v2.2.1/TRUENAS.md

In the future, if this is fixed, the example manifest can be retrived from commit dfd61569857cb746f76250c629704c1410fec4bc.

### 2. Configure a TrueNAS exporter from UI:

https://github.com/Supporterino/truenas-graphite-to-prometheus/tree/v2.2.1?tab=readme-ov-file#getting-started

### 3. Reconfigure netdata

This has to be the last step because TrueNAS resets netdata config on step 2.

Run ansible playbook role [truenas-exporter](../../../ansible/roles/truenas-exporter).
