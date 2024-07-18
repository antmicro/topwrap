# Deducing interfaces

This section describes how inferring interfaces works when using `topwrap parse` with `--iface-deduce`, `--iface` or `--use-yosys` options.

The problem can be described as follows: given a set of signals, infer what interfaces are present in this set and assign signals to appropriate interfaces.
Interface names and types (AXI4, AXI Stream, Wishbone, etc.) are, in the general case, not given in advance.
Algorithm implemented in topwrap works roughly as follows:

1. Split the given signal set into disjoint subsets of signals based on common prefixes in their names
2. For a given subset, try to pair each signal name (as it appears in the RTL) with the name of an interface signal (as it is defined in the specification of a particular interface).
This pairing is called "a matching".
Matching with signals from all defined interfaces is tried.
3. For a given subset and matched interface, infer the interface direction (master/slave) based on the direction of some signal in this set.
4. Compute score for each matching, e.g. if signal names contain `cyc`, `stb` and `ack` (and possibly more) it's likely that this set is a Wishbone interface.
Among all interfaces, interface that has the highest matching score is selected.

## Step 1. - splitting ports into subsets

First, all ports of a module are grouped into disjoint subsets. Execution of this step differs based on the options supplied to `topwrap parse`:
- with `--iface` the user supplies topwrap with interface names - ports with names starting with a given interface name will be put in the same subset.
- with `--use-yosys` grouping is done by parsing the RTL source with `yosys`, where ports have attributes in the form of `(* interface="interface_name" *)`.
Ports with the same `interface_name` will be put in the same subset.
- with `--iface-deduce` grouping is done by computing longest common prefixes among all ports.
This is done with the help of a [trie](https://en.wikipedia.org/wiki/Trie) and only allows prefixes that would split the port name on an underscore (e.g. in `under_score` valid prefixes are an empty string, `under` and `under_score`) or a camel-case word boundary (e.g. in `wordBoundary` valid prefixes are an empty string, `word` and `wordBoundary`).
As with user-supplied prefixes, ports with names starting with a given prefix will be put in the same subset.

## Step 2. - matching ports with interface signal names

Given a subset of ports from a previous step, this step tries to match a regexp from an interface definition YAML for a given interface signal to one of the port names and returns a collection of pairs: RTL port + interface port.
For example, when matching against AXI4, a port named `axi_a_arvalid` should match to an interface port named `ARVALID` in the interface definition YAML.

This operation is performed for all defined interfaces per a given subset of ports so the overall result of this step is a collection of matchings.
For most interfaces these matching will be poor - e.g. `axi_a_arvalid` or other AXI4 signals won't match to most Wishbone interface signals, but an interface that a human would usually assign to a given set of signals will have the most signals matched.

## Step 3. - inferring interface direction

This step picks a representative RTL signal from a single signal matching from the previous step and checks its direction against direction of the corresponding interface signal in interface definition YAML - if it's the same then it's a master interface (since the convention in interface description files is to describe signals from the master's perspective), otherwise it's a slave.

## Step 4. - computing interface matching score

This step computes a score for each matching returned by step 2.
This score is based on the number of matched/unmatched optional/required signals in each matching.

Not matching some signals in a given group (from step 1.) is heavily penalized to encourage selecting interface that "fits" a given group best.
For example, AXI Lite is a subset of AXI4, so a set of signals that should be assigned AXI4 interface could very well fit the description of AXI Lite, but this mechanism discourages selecting such matching in favor of selecting the other.

Not matching some signals of a given interface (from interface description YAML) is also penalized.
Inverting the previous example, a set of signals that should be assigned AXI Lite interface could very well fit the description of AXI4, but because it's missing a few AXI4 signals so selecting this matching is discouraged in favor of selecting the other.

### Good scoring function

A well-behaving scoring function should satisfy some properties to ensure that the best "fitting" interface is selected.
To describe these we introduce the following terminology:
* `>`/`>=`/`==` should be read as "must have a greater/greater or equal/equal score than".
* Partial matching means matching where some rtl signals haven't been matched to interface signals, full matching means matching where all have been matched.

Current implementation when used with default config values satisfies these properties:

1. full matching with N+1 signals matched (same type) == full matching with N signals matched (same type)
2. full matching with N signals matched (same type) > partial matching with N signals matched (same type)
3. partial matching with N+1 signals matched (same type) > partial matching with N signals matched (same type)
4. full matching with N+1 required, M+1 optional signals >= full matching with N+1 optional, M optional signals >= full matching with N required, M+1 optional signals >= full matching with N required, M optional signals

Properties 2-4 generally ensure that interfaces with more signals matched are favored more over those with less signals matched.
Property 1. follows from the current implementation and is not needed in all implementations.

Full details can be found in the implementation itself.
