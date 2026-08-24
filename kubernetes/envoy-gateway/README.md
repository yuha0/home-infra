# Envoy Gateway

Gateway API implementation, intended to replace the (deprecated) ingress-nginx
controllers. The two GatewayClasses map 1:1 onto the existing IngressClasses:

| ingress-nginx        | Envoy Gateway     | LB IP (parallel) | LB IP (cutover) |
| -------------------- | ----------------- | ---------------- | --------------- |
| `nginx-internal`     | `envoy-internal`  | `10.200.0.5`     | `10.200.0.1`    |
| `nginx-external`     | `envoy-external`  | `10.200.0.6`     | `10.200.0.2`    |

Envoy Gateway runs in parallel with ingress-nginx on fresh BGP IPs so apps can be
migrated one at a time, then cut over (or switched back). `.3` and `.4` are not
free — they belong to the adguardhome DNS Service and the kube-system apiserver
Service respectively.

## Rendering `generated.yaml`

Envoy Gateway is published only as an **OCI** chart
(`oci://docker.io/envoyproxy/gateway-helm`). `helm.py` detects OCI repos by URL
scheme, so the standard flow applies — run from `helm/`:

```sh
cd helm && python3 ../../../helm.py
```

Versions are discovered from the registry's tags-list API. As with every chart,
upstream default values come from the packaged chart (`helm show values`) —
which also sidesteps upstream's git values file being a Go template
(`values.tmpl.yaml`); the packaged copy has the placeholders rendered.

`--include-crds` (in `extraTemplateArgs`) is required: the chart bundles both
the Gateway API CRDs and the Envoy Gateway CRDs (`EnvoyProxy`,
`BackendTrafficPolicy`, `ClientTrafficPolicy`, …) under `crds/`, which
`helm template` skips by default. This makes the app self-contained — it does
not depend on kubespray's `gateway_api_enabled`.

## Customization

Chart values (`helm/values.yaml`) are at upstream defaults except
`config.envoyGateway.extensionApis.enableBackend`, which turns on the `Backend`
API that scrypted's self-signed HTTPS upstream needs.

> **The controller reads that config once, at startup.** It comes from the
> `envoy-gateway-config` ConfigMap and the chart puts no checksum annotation on
> the Deployment's pod template, so an ArgoCD sync updates the ConfigMap without
> restarting anything and the flag silently stays off (`extensionApis: {}` in the
> live config). After syncing a `config:` change, run:
>
> ```sh
> kubectl rollout restart deploy/envoy-gateway -n envoy-gateway-system
> ```
>
> Until then the scrypted route has no reachable backend.

Data-plane customization lives in `gateways/`, split per
gateway into `internal/` and `external/` (mirroring `../ingress-nginx/`), each
with:

- `gatewayclass.yaml` — the GatewayClass, `parametersRef`-ing its EnvoyProxy.
- `envoyproxy.yaml` — sets the Envoy Service `loadBalancerIP`, the
  `cilium-bgp-advertise: default` label (so cilium advertises it via BGP, see
  `../cilium/bgp-advertisement.yaml`), the external-dns wildcard (internal), and
  `replicas: 2` for the data plane. Both scopes are live on their parallel IPs
  alongside ingress-nginx; only the DNS records still point at nginx.
- `gateway.yaml` — listeners: one wildcard HTTPS listener plus a plain HTTP
  listener (which the catch-all redirect below upgrades to HTTPS).
- `certificate.yaml` — the wildcard cert each HTTPS listener terminates with:
  `*.internal.yuha0.com` internally (mirrors
  `../ingress-nginx/internal/certificate.yaml`), `*.yuha0.com` externally.
  Both are DNS-01 issued by the `letsencrypt` ClusterIssuer.
- `redirect.yaml` — catch-all HTTPRoute on the HTTP listener, 301 to HTTPS.

Because both scopes terminate TLS with a wildcard, **migrating an app never
requires touching `gateways/`** — an app only needs its own `HTTPRoute`. Note
that `*.yuha0.com` covers `recipes.yuha0.com` but not the apex `yuha0.com` nor
`*.internal.yuha0.com`; wildcards match exactly one label.

## Migration status

**Every `Ingress` in the cluster now has a route counterpart** — 24 hostnames
across 23 `Ingress` objects. Routes were *added alongside* the Ingresses rather
than replacing them, so both paths serve traffic until cutover; DNS still
resolves to ingress-nginx.

| App (dir) | Host(s) | Route | Source |
| --- | --- | --- | --- |
| `adguardhome/adguardhome/internal` | `adguard.internal` | `HTTPRoute` | kustomize |
| `adguardhome/adguardhome/external` | `adguard` (`/dns-query` only) | `HTTPRoute` | kustomize |
| `adguardhome/pauser` | `adguard-pauser.internal` | `HTTPRoute` | kustomize |
| `argocd` | `argocd.internal` | `HTTPRoute` | kustomize |
| `argocd` | `argocd` | `HTTPRoute` | **helm** (`server.httproute`) |
| `grafana/internal` | `grafana.internal` | `HTTPRoute` | kustomize |
| `grafana/external` | `grafana` | `HTTPRoute` | kustomize |
| `homebridge` | `homebridge.internal`, `homebridge-webhook.internal` | 2× `HTTPRoute` | kustomize |
| `hubble` | `hubble.internal` | `HTTPRoute` | kustomize |
| `invidious/app` | `invidious.internal` | `HTTPRoute` | kustomize |
| `karakeep/web` | `karakeep.internal` | `HTTPRoute` | kustomize |
| `logging/loki` | `loki-gateway.internal` | `HTTPRoute` | **helm** (`gateway.route.main`) |
| `plex` | `plex.internal` | `HTTPRoute` | kustomize |
| `pocket-id/app` | `oidc.internal`, `oidc` | 2× `HTTPRoute` | kustomize |
| `prometheus/thanos` | `thanos.internal` | `HTTPRoute` | kustomize |
| `scrypted` | `scrypted.internal` | `HTTPRoute` + `Backend` | kustomize |
| `seaweedfs` | `seaweedfs-{admin,filer,s3}.internal` | 3× `HTTPRoute` | kustomize (chart has no GWAPI support) |
| `tandoor/app` | `recipes.internal`, `recipes` | 2× `HTTPRoute` | kustomize |
| `unifi/logging/vector` | `vector.internal` | `GRPCRoute` | kustomize |

Two apps drive their route from the chart instead of a hand-written file, since
both charts template Gateway API natively — see `gateway.route.main` in
`../logging/loki/helm/values.yaml` and `server.httproute` in
`../argocd/helm/values.yaml`. Note the argo-cd chart's `httproute.hostnames` does
**not** fall back to `global.domain` the way `ingress.hostname` does, so the host
is spelled out there.

## Timeouts

**No timeout configuration anywhere — deliberately.** No `BackendTrafficPolicy`,
no `HTTPRoute.timeouts`. Everything runs on stock Envoy defaults.

This is a real behaviour change worth understanding, not an oversight. Envoy
applies a **15s total-request timeout** when a route sets none (verified against
the live `invidious` route: `timeout` is absent from the Envoy route config, and
Envoy's default for an absent `RouteAction.timeout` is 15s), whereas nginx has no
total-request cap at all. Envoy's FAQ suggests disabling it:

> "This timeout defaults to 15 seconds. This is typically a problem for streaming
> responses ... and will need to be disabled by setting to 0."
> — <https://www.envoyproxy.io/docs/envoy/latest/faq/configuration/timeouts>

That advice was **not** followed, because the access logs show the affected
clients all recover on their own. Idle timeouts need nothing either: Envoy's
`stream_idle_timeout` defaults to 5m against nginx's 60s `proxy_read_timeout`, so
most apps *gain* headroom by migrating.

### What the access logs actually show

Internal controller, 23 days, 13,145 requests — only 9 exceeded 15s. External
controller, 4.5 days, 14,781 requests — **none** exceeded 15s (argocd peaked at
1.1s, grafana at 0.6s).

| Duration | Endpoint | Recovers because |
| --- | --- | --- |
| 29,469s / 22.8 GB | plex `/downloadQueue/.../media` | `206 Partial Content` — client uses Range requests and re-fetched the same item at 11.6 MB / 1.01 GB / 1.20 GB / 22.8 GB, i.e. it already resumes |
| 8,818s, 4,987s | plex `/:/eventsource/notifications` | SSE — auto-reconnect is part of `EventSource` |
| 3,840s, 2,791s | grafana `/api/live/ws` | Grafana Live websocket reconnects |
| 89s | plex `/:/websockets/notifications` | client reconnects |

Two intuitive assumptions turned out to be false, so don't re-derive from them:
**video streaming is not long-lived here** (plex playback is segmented HLS, p99
0.51s; invidious peaked at 0.02s and its playback never touches the ingress), and
**"nginx had no timeout" does not mean these clients can't survive a cut** — the
`206`s prove Plex's downloader already resumes.

The cost of stock defaults is churn, not breakage: a plex SSE channel or Grafana
Live socket will now reconnect every 15s while open, and a large plex sync becomes
many range requests instead of one. If that churn ever becomes annoying, the fix
is per-app and one line — no global policy needed:

```yaml
rules:
- backendRefs: [...]
  timeouts:
    request: 0s   # 0s disables it, per the Gateway API spec
```

Watch-items with no traffic in the sampled window, so no evidence either way:
`seaweedfs-{s3,filer}` (large uploads via the ingress hostnames) and
`vector.internal` (gRPC streams are long-lived by nature; a cut would force the
shipper to reconnect). Both were previously carrying nginx timeout annotations
that the logs show nothing has exercised.

## Migrating an app off ingress-nginx

Per-app `Ingress` → `HTTPRoute` lives in each app's own directory/ArgoCD project
(`HTTPRoute` is namespaced, so no AppProject change is needed — except `hubble`,
whose project has a `namespaceResourceWhitelist`). For each app:

1. Add an `HTTPRoute` whose `parentRefs` point at
   `envoy-internal`/`envoy-external` in `envoy-gateway-system`, keeping the same
   hostname/paths/backend.
2. Translate any live nginx annotations to Gateway API policies:
   - `proxy-read/send-timeout` (hubble, seaweedfs) → usually **nothing**; these are
     idle timeouts and Envoy's 5m default already beats nginx's 60s default. See
     "Timeouts" below.
   - cookie session affinity (tandoor) → `HTTPRoute` `sessionPersistence`
   - `backend-protocol: HTTPS` (scrypted) → `Backend` with `tls.insecureSkipVerify`
     (`BackendTLSPolicy` cannot skip verification)
   - `backend-protocol: GRPC` (unifi vector) → `GRPCRoute`
   - streaming / `proxy-buffering: off` (seaweedfs) → Envoy streams by default; tune
     body limits via `ClientTrafficPolicy` if needed
   - `limit-connections` (tandoor external) → **no equivalent**; see the comment in
     `../tandoor/app/httproute.yaml`
   - `proxy-buffer-size` &co. (pocket-id) → nothing to translate; see the comment in
     `../pocket-id/app/httproute.yaml`
3. For external apps, carry the DNS annotations over from the `Ingress` onto the
   `HTTPRoute` (`external-dns.alpha.kubernetes.io/target: ddns.yuha0.com`,
   `cloudflare-proxied: "true"`). TLS needs nothing — the wildcard listener
   already covers the host — and the old per-app `Certificate` can be dropped
   once the app is cut over.
4. Test against the parallel IP (`10.200.0.5/.6`) via a temporary host override,
   then leave the route in place:

   ```sh
   curl -sSv --resolve grafana.internal.yuha0.com:443:10.200.0.5 \
     https://grafana.internal.yuha0.com/ -o /dev/null
   ```

Note that `sessionPersistence` and `rules[].timeouts` only exist because the
chart ships the **experimental** Gateway API channel (`helm template
--include-crds`; the live CRD carries
`gateway.networking.k8s.io/channel: experimental`, bundle `v1.5.1`). On the
standard channel the API server would silently prune those fields.

## Cutover

Once everything is migrated:

1. **Teach external-dns about routes.** It currently runs with only
   `--source=service --source=ingress` (see `sources` in
   `../external-dns/helm/values.yaml`), so the
   `external-dns.alpha.kubernetes.io/*` annotations on the external `HTTPRoute`s
   are **inert today** — every public record is still published from the
   `Ingress`. Deleting those Ingresses before adding `--source=gateway-httproute`
   would strip the records (the `upsert-only` policy delays but does not prevent
   this once ownership changes). Add the source first, confirm the records are
   unchanged, then remove the Ingresses.
2. Point `*.internal.yuha0.com` at Envoy: move the Service to `10.200.0.1` (or
   move the `external-dns` wildcard annotation off ingress-nginx-internal and
   enable it in `envoyproxy.yaml`) and `10.200.0.2` for external.
3. Drop the now-redundant per-app `Certificate`s / `tls:` blocks — the wildcard
   listener certs replace them.
4. Update the remaining ingress-nginx references in `CiliumNetworkPolicy`s. The
   Envoy selectors were added *alongside* the nginx ones, so the nginx clauses
   are safe to delete only at this point. One is not a route at all:
   `../unifi/networkpolicies.yaml` lets `unpoller` *egress* to the
   ingress-nginx-internal controller on 443 and will need the Envoy equivalent.
5. Scale down / remove the `ingress-nginx` ArgoCD app.

### Gotcha: kustomize and Gateway API name references

kustomize follows Service name references inside an `Ingress` but not inside
Gateway API CRDs, so in overlays that apply a `nameSuffix` (adguardhome and
grafana, `-internal`/`-external`) a `backendRefs.name` would be left pointing at
the unsuffixed Service. Each such overlay carries a `gwapi-namerefs.yaml`
registered under `configurations:` to teach kustomize the extra field path.

ingress-nginx's global `force-ssl-redirect` is covered by the catch-all
`redirect.yaml` HTTPRoute on each gateway's HTTP listener (301 to https). An
app that needs plain HTTP can opt out by attaching its own route to the `http`
listener — more specific matches outrank the catch-all.
