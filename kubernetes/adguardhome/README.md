# Highly Available Ad Blocking with AdGuard Home

The setup in this directory allows you to run multiple AdGuard Home instances behind a load balancer, making your DNS service "highly available".

What I get from this setup:

- HA AdGuard Home deployment, no single point of failure.
- Combined TCP + UDP DNS service on port 53 (thanks to metallb).
- Configuration as code and GitOps.
- Prometheus metrics (thanks to [ebrianne/adguard-exporter](https://github.com/ebrianne/adguard-exporter).
- DoH.

## TODOs

- An easy-to-trigger adhoc job to temporarily disable filter for a given period of time.
- Forward query logs to loki

## Details

Before getting too excided, you should be aware that AdGguard Home seems to be a stateful, centralized singleton application. It does not support HA out of box. It requires dedicated storage on filesystem, a writable config file and it has no concept of clustering built-in.

My current approach to HA includes the following weird dances, which come at some cost:

### Configuraion:

You lose the ability to configure AdGuard Home via their nice web GUI:

To make configuration consistent across multiple instances, I use a configmap to manage the config file. This configmap is mounted on each instance as read-only. Currently AdGuard requires write permission to the config file (see https://github.com/AdguardTeam/AdGuardHome/issues/1964), so I did a little trick: First, Run an `initContainer` and mount both the configmap and AdGuard's conf volume, `cp` the configmap to the conf volume. And then, start AdGuard with the copy of configmap.

Now whenever you change the configmap and do a `kubectl apply -k .`, All AdGuard instances will be bounced and receive the change, in a rolling update fashion with zero downtime. Note that this approach does not prevent an admin user from making changes on the web GUI, but if you do, you will face some weirdness because the change is only applied to one of the many instances.

## Secret Generation

For the following reasons, the configuration file has to be a secret instead of a configmap:

- Although the password is BCrypt-encrypted in config file, it needs to be consumed by the exporter as plaintext. I don't want to define the same password in two different places.
- My DOH bootstrap DNS are paid NextDNS account, which I agree to not to expose to the public when I signed up. In my area it is faster than CloudFlare, Google, or Quad9.

Obviously, I can't check in my secret as base64 encoded plaintext. All the secrets in my cluster are encrypted by sealed secrets controller. Here's how I managed to check in nonsensitive information as plaintext, while still keep sensitive information encrypted:

1. Make a sealed secret template file, `sealed-config.yaml`, write all the non-sensitive config fields in the template:
    ```yaml
    apiVersion: bitnami.com/v1alpha1
    kind: SealedSecret
    metadata:
      creationTimestamp: null
      name: config
      namespace: adguardhome
    spec:
      encryptedData:
        nextdns-bootstrap-1:
        nextdns-bootstrap-2:
        password:
        username:
      template:
        data:
          AdGuardHome.yaml: |
            bind_host: 0.0.0.0
            ...
    ```
2. Create a `config.yaml` and write sensitive fields in it as plaintext (this filename has been excluded by `./.gitignore`):
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: config
      namespace: adguardhome
    stringData:
      nextdns-bootstrap-1: 1.2.3.4
      nextdns-bootstrap-2: 5.6.7.8
      password: plaintext-password
      username: custom-username
    ```
3. Generate the final SealedSecret object:
    ```bash
    $ kubeseal < config.yaml --merge-into sealed-config.yaml
    ```

### Query logs:

The web GUI's query log page no long makes sense.

There's a load balancer that round-robins your reuqest to a random instance, and each instance manages its own query log file.

However, you can run a log forwarder as a sidecar container, and forward query logs to an Elasticsearch instance. I might implement this one day, because visualize my queries on a [geo map](https://www.elastic.co/guide/en/kibana/current/maps.html) is interesting.

## Result

Now at this point, because of the above two shortcomings, your AdGuard Home effectively becomes stateless. Any internal state does not make sense at all. But anyway, go ahead and change the replica count in the `Deployment` and enjoy a more reliable Ad blocking!
