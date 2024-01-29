# Unifi Network Controller

The manifests in this directory is modified based on manifests generated by helm chart `k8s-at-home/unifi` in https://k8s-at-home.com/charts. The chart was a great starting point, but I had to do a lot of tinkering to make it the way I want it to be and I reached a point that it was easier to do it myself than kustomizing the chart output.

## The extra song and dance

- The chart uses `NodePort` to expose ports for good reasons -- not everyone has loadblanacer implemented in their cluster, and Kubernetes load balancer API does not support multi-protocol(TCP + UDP) services. This is not an issue for me since Metallb allows the same IP address to be shared by multiple load balancers.
- The chart runs the unifi pod as root user. This is a convenient feature to map `host user <-> in-container unifi process user` in upstream container images, which changes file permissions. I did this myself in an initContainer, so that the main container can start without need to "fix" file permissions.
- gateway config file is managed in GitOps way.
- Extra cronjob to backup data

## Accept the risk and embrace GitOps

Running the network application from _inside_ the network it manages doesn't sound like a good idea because of the obvious chicken and eggs problem. However, the downsides appear to be trivial: you are going th have problems only when the network is not functioning correctly and the network application is not reachable from your unifi gears. And at that point, you will need wired connection to ssh into your unifi gears to fix stuff anyways.

But when the network is functioning correctly, running the network application in Kubernetes is much better than the alternatives:

- Configuration is predictable and easy to manage, because GitOps.
- The application is largely stateless (external MongoDB with active-passive backup, configuration as code, and the rest of data files on external NFS backed PVC) and can be moved from server to server with zero manual work.
- Application running 24/7 and metrics can be scraped and persistend for long term comsumption.
- Reliable backup

Now, in rare cases if the network application is not reachable, it is still trivial to temporarily migrate to an external network application running anywhere else: simply load the most recent backup there, and ssh to every Unifi gear to change the inform address manually to it.

## IP/port groups and firewall/port-forwarding rules

Ubiquiti does not recommend using `gateway.config.json`, because whatever custom fields defined in it are not captured in network application's database and is not displayed on UI. On provisioning, the network application merge the special custom configs into a base config on the router.

However, I have to use this file for managing IP/port groups and firewall/port-forwarding rules in order to open port 80 and 443 to cloudflare's IPs but shutdown other IP sources:

- The UI only allow configuring a single CIDR block to be whitelisted for a new port-forwarding rule. And it creates a new firewall rule for it automatically.
- If I don't whitelist any CIDR block, the port-forwarding rule will automatically create a firewall rule that allows source from anywhere. And this firewall rule cannot be deleted.
- Cloudflare's IP ranges are very long. So I'd like to be able to programmatically update the list in the firewall rule.

As a result, I provision the IP/port groups and firewall/port-forwarding rules via `gateway.config.json`. The final merged config file can be dumped from the router:

```bash
$ mca-ctrl -t dump-cfg > config-dump.json
```