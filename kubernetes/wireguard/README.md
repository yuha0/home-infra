# To Add New Client

First, run this to generate the client public key and private key:

```bash
$ docker run --rm -it yuha0/wireguard bash -c 'wg genkey | tee private.key | wg pubkey && cat private.key'
4xcxhI49sgcwst/xSHGzY8284SO3hgVVrzV9E/Ehclo=
uG9zZTLtMerXqVCoOzokZpMUINr21dwIfMDdWRpPEnE=
```

Apend the new client config in `wg0.conf`:

```
[Peer]
PublicKey = 4xcxhI49sgcwst/xSHGzY8284SO3hgVVrzV9E/Ehclo=
AllowedIPs = <client-ip>/32
```

Update the configmap and DaemonSet.

Generate client config:

```
[Interface]
PrivateKey = uG9zZTLtMerXqVCoOzokZpMUINr21dwIfMDdWRpPEnE=
Address = <client-ip>/32
DNS = <pihole-ip>

[Peer]
# Server public key. Can be retrieved from configmap:
# kubectl get -n wireguard cm wg0-public-<object-hash> -ojsonpath='{.data.wg0-public\.key}'
PublicKey = STxgSJv/SH25kIept1NIhAEAu7vLwGMQIRNz2luFQhg=
Endpoint = <public-ip>:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
```
