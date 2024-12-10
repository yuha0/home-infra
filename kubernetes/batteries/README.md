# Monitor a bunch of batteries

I have a few batteries around the house:

- UPS in server rack
- A Ugreen PowerRoam 2200 connected to the above UPS for extended runtime during outage.
- Some smaller EcoFlow batteries for all kinds of appliance around the house (Apple Home hubs, garage door opener, ONT from ISP...etc)

I consolidate their monitoring systems all in the `batteries` namespace.

## UPS

Standard UPS devices should all be connected to cluster nodes via USB and monitored by Network UPS Tools (NUT).

## Ugreen

Ugreen PowerRoam batteries sends telemetry data over bluetooth. The following project use host's bluetooth adapter to discover and pair with their batteries and expose metrics in Prometheus format:

https://github.com/ilya-zlobintsev/proam-cli

## [WIP] EcoFlow

Sadly, this dumb battery phones home over internet. I see there are some folks try to reverse-engineer the bluetooth protocol but none of them is reliable. For now, the plan is to pull metrics from mothership over internet with:

https://github.com/berezhinskiy/ecoflow_exporter
