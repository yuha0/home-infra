# AdGuard Home dashboards

`adguardhome.json` shows a global view of every AdGuard Home replica. The metrics come from the vector sidecar described in [the AdGuard Home README](../../../adguardhome/README.md#metrics), and the per-domain and per-client panels come from the query log in VictoriaLogs.

## Data sources

Prometheus, for everything with a bounded set of values:

- Status: online instances, protection state and remaining pause, running version, filter rule count and filter list freshness.
- Totals for the selected time range: queries, blocked queries, blocked ratio, cache hit ratio, SERVFAIL ratio and p95 latency, all computed with `increase(...[$__range])` on real counters.
- Rates by instance, query type, response code, protocol, filtering reason, filter list and blocked service.
- Latency percentiles, overall, cached vs not cached, and per upstream.

VictoriaLogs, for anything that identifies a domain or a client:

- Top allowed and blocked domains. The `Domain grouping` variable switches between full names and second-level domains, which are extracted at query time, so `<random-string>.siteintercept.qualtrics.com` is counted as `qualtrics.com`. The extraction takes the last two labels, so it is wrong for public suffixes like `co.uk`.
- Top clients and top clients by blocked queries. A client is its ClientID when it sends one, otherwise its IP.
- A table of the latest filtered queries.

The `Instance` variable limits every panel to the internal or external deployment.
