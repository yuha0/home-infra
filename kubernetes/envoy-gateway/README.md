# Envoy Gateway

Gateway API implementation. **This is the only ingress path in the cluster** —
it replaced the (deprecated) ingress-nginx controllers, which were removed on
2026-09-13. The two GatewayClasses took over the old IngressClasses 1:1,
including their LB IPs:

| was (`IngressClass`) | now (`GatewayClass`) | LB IP         |
| -------------------- | -------------------- | ------------- |
| `nginx-internal`     | `envoy-internal`     | `10.200.0.1`  |
| `nginx-external`     | `envoy-external`     | `10.200.0.2`  |

`.3` and `.4` belong to the adguardhome DNS Service and the kube-system
apiserver Service respectively. `.5`/`.6` were the parallel IPs Envoy ran on
during the migration and are now free.

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

Data-plane customization lives in `gateways/`, split per gateway into
`internal/` and `external/`, each with:

- `gatewayclass.yaml` — the GatewayClass, `parametersRef`-ing its EnvoyProxy.
- `envoyproxy.yaml` — sets the Envoy Service `loadBalancerIP` (`.1` internal,
  `.2` external), the `cilium-bgp-advertise: default` label (so cilium
  advertises it via BGP, see `../cilium/bgp-advertisement.yaml`), the
  external-dns `*.internal.yuha0.com` wildcard (internal only), and
  `replicas: 2` for the data plane.
- `gateway.yaml` — listeners: one wildcard HTTPS listener plus a plain HTTP
  listener (which the catch-all redirect below upgrades to HTTPS). The
  **external** Gateway also carries
  `external-dns.kubernetes.io/target: ddns.yuha0.com` — see the Cutover notes
  for why that annotation belongs on the Gateway and not on the routes.
- `certificate.yaml` — the wildcard cert each HTTPS listener terminates with:
  `*.internal.yuha0.com` internally, `*.yuha0.com` externally.
  Both are DNS-01 issued by the `letsencrypt` ClusterIssuer.
- `redirect.yaml` — catch-all HTTPRoute on the HTTP listener, 301 to HTTPS.
  Both carry `gateway-hostname-source: defined-hosts-only` for external-dns;
  see Cutover.

Because both scopes terminate TLS with a wildcard, **migrating an app never
requires touching `gateways/`** — an app only needs its own `HTTPRoute`. Note
that `*.yuha0.com` covers `recipes.yuha0.com` but not the apex `yuha0.com` nor
`*.internal.yuha0.com`; wildcards match exactly one label.

## Migration status

**Done.** All 24 hostnames (23 former `Ingress` objects) now serve from Envoy
only; every `Ingress` in the cluster has been deleted and the `ingress-nginx`
ArgoCD app removed. Before cutover all 24 were checked against both data planes
(`curl --resolve` against the parallel IPs vs the nginx IPs) and every one
returned the same status code on both.

The table below is the current route inventory.

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

## Exposing an app

A route lives in the app's own directory/ArgoCD project (`HTTPRoute` is
namespaced, so no AppProject change is needed — except `hubble`, whose project
has a `namespaceResourceWhitelist`).

1. Add an `HTTPRoute` whose `parentRefs` point at
   `envoy-internal`/`envoy-external` in `envoy-gateway-system`.
2. Historical: how each app's nginx annotations were translated during the
   migration — useful as a precedent table when adding something similar.
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
3. For external apps set `external-dns.kubernetes.io/cloudflare-proxied: "true"`
   on the route. Do **not** put `target` on the route — external-dns's gateway
   source ignores it; the target comes from the Gateway annotation. TLS needs
   nothing, the wildcard listener already covers the host.
4. Test with a temporary host override before trusting DNS:

   ```sh
   curl -sSv --resolve grafana.internal.yuha0.com:443:10.200.0.1 \
     https://grafana.internal.yuha0.com/ -o /dev/null
   ```

Note that `sessionPersistence` and `rules[].timeouts` only exist because the
chart ships the **experimental** Gateway API channel (`helm template
--include-crds`; the live CRD carries
`gateway.networking.k8s.io/channel: experimental`, bundle `v1.5.1`). On the
standard channel the API server would silently prune those fields.

## Cutover (done 2026-09-13)

Kept as a record, because the external-dns traps below are not obvious and the
first attempt at step 1 took all five public hostnames down.

1. **Teach external-dns about routes.** It ran with only
   `--source=service --source=ingress` (see `sources` in
   `../external-dns/helm/values.yaml`), so the
   `external-dns.kubernetes.io/*` annotations on the external `HTTPRoute`s
   were **inert** — every public record was published from the
   `Ingress`. Deleting those Ingresses before adding `--source=gateway-httproute`
   would strip the records (the `upsert-only` policy delays but does not prevent
   this once ownership changes). Add the source first, confirm the records are
   unchanged, then remove the Ingresses.

   The source alone is not enough: external-dns is scoped to the *external*
   controller by `--ingress-class=nginx-external`, and that flag does not apply
   to routes. Without a route-side equivalent the new source would pick up all
   ~17 internal `HTTPRoute`s and publish each host as its own A record at
   `10.200.0.5`, on top of the `*.internal.yuha0.com` wildcard. The counterpart
   is `--gateway-name` / `--gateway-namespace`; both are set in `extraArgs`
   alongside `ingress-class`. Note `--gateway-name` filters the *Gateway* a
   route attaches to, not the route's namespace, so it stays correct after
   step 2.

   The second trap is the catch-all redirect routes. They deliberately carry no
   `hostnames`, and external-dns treats an empty route hostname as "inherit the
   parent listener's" — `gwMatchingHost("*.yuha0.com", "")` returns
   `("*.yuha0.com", true)` ([source/gateway.go#L865-L886]) — so
   `external-https-redirect` alone would publish `*.yuha0.com` → `10.200.0.6`,
   a wildcard pointing at an RFC1918 address, public and unproxied. Both
   `redirect.yaml`s therefore carry
   `external-dns.kubernetes.io/gateway-hostname-source: defined-hosts-only`,
   which restricts them to hostnames spelled out on the route (none), so they
   generate no records.

   Adding the source also widens the chart's `ClusterRole` automatically
   (`gateways`, `httproutes`, `namespaces`) — no manual RBAC edit.

   `vector.internal` is a `GRPCRoute` but internal-only, so it is covered by the
   wildcard and `gateway-grpcroute` is not needed.

   The third trap is the one that actually took the public records down on the
   first attempt (2026-09-13, ~05:31 UTC). **The gateway source ignores the
   route's `external-dns.kubernetes.io/target` annotation.** Targets come from
   the *Gateway*: `overrides` is `TargetsFromTargetAnnotation(gw.Annotations)`
   ([source/gateway.go#L666]), and if the Gateway has no `target` annotation the
   source falls back to the Gateway's `status.addresses`
   ([source/gateway.go#L537-L543]). So the five external routes — each carrying
   `target: ddns.yuha0.com` — emitted `A → 10.200.0.6` instead of
   `CNAME → ddns.yuha0.com`.

   That is a record-*type* conflict with the Ingress candidate, and
   `PerResource.ResolveRecordTypes` resolves it by **discarding the CNAME**
   ([plan/conflict.go#L59-L97]). external-dns therefore deleted the five CNAMEs
   and tried to create A records, which Cloudflare rejected
   (`9003: Target 10.200.0.6 is not allowed for a proxied record`) because the
   routes also set `cloudflare-proxied: "true"`. Deletes succeeded, creates
   failed, and all five hostnames went NXDOMAIN.

   The fix is `external-dns.kubernetes.io/target: ddns.yuha0.com` on the
   **`envoy-external` Gateway** (`gateways/external/gateway.yaml`). Then both
   sources emit an identical `CNAME → ddns.yuha0.com` and there is no conflict
   at all. `cloudflare-proxied` still comes from the route annotations, via
   `ProviderSpecificAnnotations`, so those stay where they are.

   With the targets matched, this step *is* a no-op for the record values, and
   ownership stays with the `Ingress`: `PerResource.ResolveUpdate` prefers the
   candidate whose `resource` label equals the current TXT's
   ([plan/conflict.go#L46-L57]). Ownership only moves to `httproute/...` at
   step 4, when the Ingresses go away and the route becomes the sole candidate.

   The general lesson: **a route is not a drop-in for its Ingress
   annotation-for-annotation.** `target` moves to the Gateway,
   `cloudflare-proxied` stays on the route. Check where each annotation is read
   from before assuming it carries over.

   With the Ingresses gone, `--source=ingress` and `--ingress-class` were
   dropped too; external-dns now runs `service` + `gateway-httproute` only.

[source/gateway.go#L537-L543]: https://github.com/kubernetes-sigs/external-dns/blob/v0.22.0/source/gateway.go#L537-L543
[source/gateway.go#L666]: https://github.com/kubernetes-sigs/external-dns/blob/v0.22.0/source/gateway.go#L666
[source/gateway.go#L865-L886]: https://github.com/kubernetes-sigs/external-dns/blob/v0.22.0/source/gateway.go#L865-L886
[plan/conflict.go#L46-L57]: https://github.com/kubernetes-sigs/external-dns/blob/v0.22.0/plan/conflict.go#L46-L57
[plan/conflict.go#L59-L97]: https://github.com/kubernetes-sigs/external-dns/blob/v0.22.0/plan/conflict.go#L59-L97
2. **Move the IPs.** The Envoy Services took `10.200.0.1`/`.2` in
   `envoyproxy.yaml`, and the `*.internal.yuha0.com` external-dns annotation
   moved onto the internal Envoy Service. Because the internal wildcard is
   published from the *Service* (`--source=service`), not from any route, it had
   to land on the Envoy Service in the same change that removed the nginx one.
3. **Per-app TLS.** Nothing had to be deleted by hand: the five per-app
   `Certificate`s (`adguard-server-tls`, `argocd-server-tls`,
   `grafana-tls-certificate`, `pocket-id-tls-certificate`,
   `recipes-tls-certificate`) are cert-manager **ingress-shim** objects,
   `ownerReferences`-d to their `Ingress`, so they were garbage-collected with
   it. The only hand-written one went with the app in step 5.
4. **`CiliumNetworkPolicy` cleanup.** The Envoy selectors had been added
   alongside the nginx ones, so the nginx clauses were simply dropped
   (adguardhome, pauser, karakeep, plex).

   `../unifi/networkpolicies.yaml` looked like an exception — it let `unpoller`
   *egress* to the nginx-internal controller on 443 — but that rule was dead
   twice over and was deleted rather than translated. unpoller talks to
   `https://unifi.core.yuha0.com` (`10.106.0.1`, the UniFi gateway appliance),
   never to an ingress; and the policy's `endpointSelector`
   (`component: exporter, name: unpoller`) matches no pod — the deployment
   labels it `component: unpoller, name: unifi`. **That CNP has selected nothing
   for its whole life, so unpoller has no network policy at all.** Unrelated to
   this migration, but worth fixing deliberately rather than by accident.
5. **Removed the `ingress-nginx` ArgoCD app**, its AppProject, and the
   `kubernetes/ingress-nginx/` tree.

   > Deletion cascades on its own: `applications/kustomization.yaml` patches
   > `resources-finalizer.argocd.argoproj.io` onto every `argoproj.io` object,
   > so pruning the Application takes its namespaces, Services, ClusterRoles,
   > IngressClasses and webhooks with it. Note the finalizer is **only in the
   > rendered output** — the per-app `ingress-nginx.yaml` does not show it.
   >
   > The one thing to watch is the `10.200.0.1`/`.2` handover: Envoy cannot
   > claim an IP the nginx Service still holds, so its Service may sit
   > `<pending>` until the cascade finishes. If one is still pending once the
   > old namespaces are gone, delete it and let Envoy Gateway recreate it.

The ingress-nginx Grafana dashboards (`../grafana/dashboards/kubernetes/`) were
left in place and now have no data source. Harmless; delete when convenient.

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
