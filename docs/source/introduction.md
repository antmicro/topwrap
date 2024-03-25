# Introduction

Topwrap is a tool for generating HDL wrappers for simple blocks as well as digital systems and can be used for creating complex SoCs from single blocks contained in wrappers.


## Wrappers
These wrappers standardize names of ports that belong to an interfaces (e.g. UART, AXI etc.)

```{image} img/wrapper.png
```
## Top module
Top modules connect IPs and/or Wrappers by either ports\` names or interfaces\` names to ease connecting multi-wire interfaces without the need to connect each wire separately.

```{image} img/ipconnect.png
```
