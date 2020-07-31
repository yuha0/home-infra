# Highly Available Ad Blocking with AdGuard Home

The setup in this directory allows you to run multiple AdGuard Home instances behind a load balancer, making your DNS service "highly available".

## Details

Before getting too excided, you should be aware that AdGguard Home seems to be a stateful, centralized singleton application. It does not support HA out of box. It requires dedicated storage on filesystem, a writable config file and it has no concept of clustering built-in.

My current approach to HA includes the following weird dances, which come at some cost:

### Configuraion:

You lose the ability to configure AdGuard Home via their nice web GUI:

To make configuration consistent across multiple instances, I use a configmap to manage the config file. This configmap is mounted on each instance as read-only. Currently AdGuard requires write permission to the config file (see https://github.com/AdguardTeam/AdGuardHome/issues/1964), so I did a little trick: First, Run an `initContainer` and mount both the configmap and AdGuard's conf volume, `cp` the configmap to the conf volume. And then, start AdGuard with the copy of configmap.

Now whenever you change the configmap and do a `kubectl apply -k .`, All AdGuard instances will be bounced and receive the change, in a rolling update fashion with zero downtime. Note that this approach does not prevent an admin user from making changes on the web GUI, but if you do, you will face some weirdness because the change is only applied to one of the many instances.

### Query logs:

The web GUI's query log page no long makes sense.

There's a load balancer that round-robins your reuqest to a random instance, and each instance manages its own query log file.

However, you can run a log forwarder as a sidecar container, and forward query logs to an Elasticsearch instance. I might implement this one day, because visualize my queries on a [geo map](https://www.elastic.co/guide/en/kibana/current/maps.html) is interesting.

Now at this point, because of the above two shortcomings, your AdGuard Home effectively becomes stateless. Any internal state does not make sense at all. But anyway, go ahead and change the replica count in the `Deployment` and enjoy a more reliable Ad blocking!
