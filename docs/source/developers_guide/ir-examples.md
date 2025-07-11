# Examples for Internal Representation

There are four examples in `examples/ir_examples` showcasing specific features of Topwrap which we want to take into consideration while creating the new internal representation.

## Simple

This is a simple non-hierarchical example that uses two IPs. Inside, there are two LFSR RNGs constantly generating pseudorandom numbers on their outputs. They are both connected to a multiplexer that selects which generator's output should be passed to the `rnd_bit` external output port. The specific generator is selected using the `sel_gen` input port.

This example features:
- IP core parameters
- variable width ports

```{kpm_iframe}
:dataflow: ../../build/kpm_jsons/data_ir_examples_simple.json
:spec: ../../build/kpm_jsons/spec_ir_examples_simple.json
```

## Interface

This is another simple example using two IPs, this time with an interface. The design consists of a streamer IP and a receiver IP. They both are connected using the AXI4Stream interface. The receiver then passes the data to an external inout port.

This example features:
- usage of interface ports
- port slicing
- constant value connected to a port
- an Inout port

```{kpm_iframe}
:dataflow: ../../build/kpm_jsons/data_ir_examples_interface.json
:spec: ../../build/kpm_jsons/spec_ir_examples_interface.json
```

## Hierarchical

This is an example of a hierarchical design. The top-level features standard external ports `clk` and `rst`, a `btn` input that represents an input from a physical button, and `disp0..2` outputs that go to an imaginary 3-wire-controlled display. All these ports are connected to a processing hierarchy `proc`. Inside this hierarchy we can see the `btn` input going into a "debouncer" IP, its output going into a 4-bit counter, the counter's sum arriving into an encoder as the input number, and the display outputs from the encoder further lifted to the parent level. The encoder itself is a hierarchy, though an empty one with only the ports defined. The 4-bit counter is also a hierarchy that can be further explored. It consists of a variable width adder IP and a flip-flop register IP.

This example features:
- hierarchies of more than one depth

```{kpm_iframe}
:dataflow: ../../build/kpm_jsons/data_ir_examples_hierarchical.json
:spec: ../../build/kpm_jsons/spec_ir_examples_hierarchical.json
```

:::{note}
No KPM examples for below ones since they use features incompatible with old KPM handling code.
They should be added when IR is fully supported throughout the codebase.
:::

## Interconnect

This is an example of our interconnect generation feature. The design features 3 IP cores: a memory core (`ips/mem.yaml`), a digital signal processor (`ips/dsp.yaml`) and a CPU (`ips/cpu.yaml`). All of them are connected to a wishbone interconnect where both the CPU and an external interface `ext_manager` act as managers and drive the bus. DSP and MEM are subordinates, one available at address 0x0, the other at 0x10000.

Note that while this specific example uses a "Wishbone Round-Robin" interconnect, we still aim to support other types of them in the future.
Each one will have its own schema for the "params" section so make sure not to hardcode the parameters' keys or values.

This example features:
- usage of interface ports
- interconnect usage

## Advanced

This example was created some time after the previous ones and it uses features that the IR did not have yet by then. It's main purpose is to demonstrate and use in tests:
- Multidimensional bit arrays
- Named vs anonymous `BitStructs`
- Arbitrarily sliced port connections (more complex than just a bit-vector slice)
- Partially inferred interfaces (some of their signals are realized using sliced external ports while some signals come from a "real" interface IO)
- Interface signals having types just like ports
- Interface signals having default values
- Complex interface mode configurations:
  - Signals optional for the subordinates or masters
  - Signals legal only for one side of the interface


## Other

Something that was not taken into account previously, because we don't support it yet, and it's impossible to represent in either format, is a feature/syntax that would allow us to dynamically change the collection of ports/interfaces an IP/hierarchy has. Similarly to how we can control the width of a port using a parameter (like in the "simple" example).
