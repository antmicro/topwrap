# IP-XACT format

This document is an exploration of the [IP-XACT format](https://www.accellera.org/images/downloads/standards/ip-xact/IPXACT-2022_user_guide.pdf).

All IP-XACT elements generated for the IR examples are located under `examples/ir_examples/[example]/ipxact/antmicro.com/[example]` where `antmicro.com/[example]` represents the [`vendor/library`](#vlnv).
They all conform to the 2022 version.

## General observations

### VLNV

The IP-XACT format enforces the usage of VLNV (vendor, library, name, version) for every single design and component.

```xml
<ipxact:vendor>antmicro.com</ipxact:vendor>
<ipxact:library>simple</ipxact:library>
<ipxact:name>lfsr_gen</ipxact:name>
<ipxact:version>1.2</ipxact:version>
```

For now, Topwrap can only reliably handle the `name` value, while `vendor` and `version` are not used anywhere and their concept is unrecognised in the codebase.
Arguably, `library` could be represented by the name of a user repository.

Special consideration needs to be taken for these values, as the XML schema defines specific allowed characters for some fields, while Topwrap doesn't sanity-check any fields that accept custom names.

:::{warning}
Later in this document this group of four tags will be represented by `<VLNV... />` to avoid repetition.
:::

### Multiple versions

There are many versions of the IP-XACT schema, as [visible here](http://www.accellera.org/XMLSchema/), on the official page of Accellera - developers of the format.

Version before 2014 and after 2014 use two different XML namespaces for the tags, respectively: `spirit:` and `ipxact:`.

Vivado seemingly only supports the 2009(!) specification version.

This means the discrepancies between different versions and incompatibilities between tools must be taken into account.

There are [official XSLT templates](https://www.accellera.org/downloads/standards/ip-xact) (bottom of the page) available that can convert any IP-XACT .xml file one version up, using an xslt tool like [`xsltproc`](https://linux.die.net/man/1/xsltproc).

### Design structure

The IP-XACT format revolves mainly around "components".
This is something that is closest to our `IPCoreDescription` class and its respective YAML schema:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ipxact:component>
    <VLNV... />
	<ipxact:model>
		<ipxact:instantiations>
			<ipxact:componentInstantiation>
				<ipxact:moduleParameters>
					...
				</ipxact:moduleParameters>
			</ipxact:componentInstantiation>
		</ipxact:instantiations>
		<ipxact:ports>
            ...
		</ipxact:ports>
	</ipxact:model>
	<ipxact:parameters>
		...
	</ipxact:parameters>
</ipxact:component>
```

A singular component represents a black-box, with the outside world seeing only its ports, buses and parameters.
In order to represent its inner design there needs to be a separate design XML file:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ipxact:design>
	<VLNV...  />
	<ipxact:componentInstances>
        ...
	</ipxact:componentInstances>
	<ipxact:adHocConnections>
		<ipxact:adHocConnection>
			<ipxact:name>gen2_gen_out_to_two_mux_gen2</ipxact:name>
			<ipxact:portReferences>
				<ipxact:internalPortReference componentInstanceRef="ip1" portRef="port1"/>
				<ipxact:internalPortReference componentInstanceRef="ip2" portRef="port1"/>
			</ipxact:portReferences>
		</ipxact:adHocConnection>
		...
	</ipxact:adHocConnections>
</ipxact:design>
```

which later *is attached* to the component description under the instantiations section, thus making the design an optional property of a module/component.

To describe a top-level wrapper you need both its description as a component, where the external IO is defined, and its design file that describes what other IPs are incorporated by this wrapper.

### Parameter passing

IP-XACT introduces a distinction between parameters of a component, and module parameters of the component's instantiation.

This allows most IP-XACT objects to accept parameters that are only internal to them and are unrelated to the potentially generated RTL.
In order to define RTL module parameters, you need to specify them under two separate sections.

Below is an example of defining a `paramWIDTH` parameter with default value of 64 in a component that gets realised in Verilog as `parameter WIDTH = 64;`:

Take note of the top-level `<ipxact:parameters>` tag and the `<ipxact:moduleParameters>` tag of the component instantiation.

```xml
<ipxact:instantiations>
    <ipxact:componentInstantiation>
        <ipxact:name>rtl</ipxact:name>
        <ipxact:displayName>rtl</ipxact:displayName>
        <ipxact:language>Verilog</ipxact:language>
        <ipxact:moduleParameters>
            <ipxact:moduleParameter>
                <ipxact:name>WIDTH</ipxact:name>
                <ipxact:displayName>WIDTH</ipxact:displayName>
                <ipxact:value>paramWIDTH</ipxact:value>
            </ipxact:moduleParameter>
        </ipxact:moduleParameters>
    </ipxact:componentInstantiation>
</ipxact:instantiations>
<ipxact:parameters>
    <ipxact:parameter parameterId="paramWIDTH" resolve="user" type="longint">
        <ipxact:name>paramWIDTH</ipxact:name>
        <ipxact:displayName>paramWIDTH</ipxact:displayName>
        <ipxact:value>64</ipxact:value>
    </ipxact:parameter>
</ipxact:parameters>
```

In Topwrap, all IP parameters do get realised in the generated Verilog and there is no notion of internal parameters.

### File sets

Each component in IP-XACT can contain an <ipxact:fileSets> section.
This is a very exhaustive section about one or more groups of *files* that this component depends on.
The type and purpose of every such file is marked, e.g: `verilogSource`.

```xml
<ipxact:fileSets>
    <ipxact:fileSet>
        <ipxact:name>fs-rtl</ipxact:name>
        <ipxact:file>
            <ipxact:name>../RTL/transmitter.v</ipxact:name>
            <ipxact:fileType>verilogSource</ipxact:fileType>
            <ipxact:logicalName>transmitter_lib</ipxact:logicalName>
        </ipxact:file>
    </ipxact:fileSet>
</ipxact:fileSets>
```

This concept currently only exists as a `--sources` CLI flag for `topwrap build` where all HDL sources are plainly forwarded to the FuseSoC .core.
There is no notion of other file dependencies inside IP Core description YAMLs.

### Vendor extensions

The IP-XACT format allows storing completely custom data inside most of the tags using the `<ipxact:vendorExtensions>` group. Topwrap could use them to store additional data about the IPs or designs.

Example theoretical vendor extensions:

```xml
<ipxact:vendorExtensions>
    <topwrap:interconnectType>wishbone</topwrap:interconnectType>
    <topwrap:kpm_position x="600" y="180" />
    <topwrap:repo>builtin</topwrap:repo>
</ipxact:vendorExtensions>
```

### Catalogs

Catalogs describe the location and the VLNV identifier of other IP-XACT elements such as components, designs, buses etc. in order to manage and allow access to collections of IP-XACT files.
In most cases defining a catalog is not required as all necessary files are automatically located by the used tool.

```xml
<ipxact:catalog>
    <VLNV... />
    <ipxact:components>
        <ipxact:ipxactFile>
            <ipxact:vlnv vendor="antmicro.com" library="simple" name="lfsr" version="1.0" />
            <ipxact:name>./antmicro.com/simple/lfsr/lfsr.1.0.xml</ipxact:name>
        </ipxact:ipxactFile>
    </ipxact:components>
    <ipxact:busDefinitions>
        ...
    </ipxact:busDefinitions>
    ...
</ipxact:catalog>
```

## [Simple example](./ir-examples.md#simple)

This is the simplest IP-XACT example as it contains only plain IP cores with standalone ports, and parameters.

### Instance names

Since Topwrap doesn't verify any user-defined names, an accidental creation of a `2mux.yaml` IP Core named `2mux_compressor` instantiated with a `2mux` name, was possible in the YAML format.
Many environments, IP-XACT included, don't actually allow users to start custom names with a number.
The instance name of `2mux` had to be changed to `two_mux` for this purpose.

### Parameters

The special syntax of IP-XACT parameters is mostly explained in the [](#parameter-passing) section.

#### Variable widths

If you look at either `ips/2mux.yaml` or `ips/lfsr_gen.yaml` you'll see that there are ports with widths defined by the parameters inside an arithmetic expression:

```yaml
# ips/2mux.yaml
out:
    - [out, OUT_WIDTH-1, 0]
```

This is easily realisable in IP-XACT because just like our port widths, they also accept arbitrary arithmetic expressions that can reference other parameters inside them:

(port-def)=
```xml
<ipxact:port>
    <ipxact:name>out</ipxact:name>
    <ipxact:wire>
        <ipxact:direction>out</ipxact:direction>
        <ipxact:vectors>
            <ipxact:vector>
                <ipxact:left>paramOUT_WIDTH - 1</ipxact:left>
                <ipxact:right>0</ipxact:right>
            </ipxact:vector>
        </ipxact:vectors>
    </ipxact:wire>
</ipxact:port>
```

### Duality of the design description

The design of the [](./ir-examples.md#simple) example is defined (from the Topwrap's perspective) purely in the `design.yaml` file. This is not so simple in IP-XACT, see [](#design-structure).

Mostly this means that the "external" section of our design YAML lands in its own component/IP file and the connections and module instances in a separate one that is attached to the component file as a "design instantiation".

The generated top-level component for this example and its design (`top.design.1.0.xml`) are located inside the `top` directory in the IP-XACT library.

Additionally a "design configuration" file is generated that contains additional configuration information for the main design file. Not much is specified there for this example though.

So finally the original `design.yaml` ends up becoming 3 interconnected .xml files in IP-XACT.

### Connections

Port connections between IP cores, and IP cores and externals are all specified in the XML design file.
There isn't much special about them, they are represented very similarly to our design description yaml connections:

```xml
<ipxact:adHocConnection>
    <ipxact:name>gen2_gen_out_to_two_mux_gen2</ipxact:name>
    <ipxact:portReferences>
        <ipxact:internalPortReference componentInstanceRef="gen2" portRef="gen_out"/>
        <ipxact:internalPortReference componentInstanceRef="two_mux" portRef="gen2"/>
    </ipxact:portReferences>
</ipxact:adHocConnection>
```

## [Interface example](./ir-examples.md#interface)

The key thing about this example is that it uses an interface connection (AXI 4 Stream) between two IPs, an inout port, a constant value supplied to a port and [](../description_files.md#port-slicing).

:::{info}
An interface is a named, predefined collection of logical signals used to transfer information between different IPs or other building blocks.
Common interface types include: Wishbone, AXI, AHB, and more.

Topwrap, like SystemVerilog, refers to this concept as an "interface".

IP-XACT refers to the same concept as a "bus".
:::

### Bus definitions

Custom interfaces in Topwrap are defined using [](../description_files.md#interface-description-files).

Custom interfaces are well recognized and supported in IP-XACT.
They are represented by two files, a "bus definition" that defines the existence of the interface/bus itself, its name and configurable parameters; and an "abstraction definition" that defines the logical signals of the interface.

It's possible to have more than one abstraction definition for a given bus definition.

Often times the necessary definitions for a given interface are already publicly available.
For example, the IP-XACT bus definitions of all ARM AMBA interfaces are available [here](https://developer.arm.com/Architectures/AMBA#Downloads) in the 2009 version of IP-XACT.
For this document, they were up-converted to the 2022 version with the help of [XSLT templates](#multiple-versions).

#### Format

If not, a custom definition has to be created.
Starting with the bus definition:

```xml
<ipxact:busDefinition>
  <VLNV... />
  <ipxact:description>This is the AXI4Stream stream bus definition.</ipxact:description>
  <ipxact:directConnection>true</ipxact:directConnection>
  <ipxact:isAddressable>false</ipxact:isAddressable>
</ipxact:busDefinition>
```

VLNV entries and description are both present at the start, like in all other IP-XACT definitions. Then there are two configuration bools:
- `<ipxact:directConnection>` decides if this bus allows direct connection between a manager/initiator and subordinate/targets. Important for "asymmetric buses such as AHB".
- `<ipxact:isAddressable>` decides if this bus is addressable using the address space of the manager side of the bus. e.g. `true` for AXI4, `false` for AXI4Stream.

Then to specify the logical signals of the interface, an abstraction definition has to be created:

```xml
<ipxact:abstractionDefinition>
	<VLNV... />
	<ipxact:description>This is an RTL Abstraction of the AMBA4/AXI4Stream</ipxact:description>
	<ipxact:busType vendor="amba.com" library="AMBA4" name="AXI4Stream" version="r0p0_1"/>
	<ipxact:ports>
		<ipxact:port>
			<ipxact:logicalName>TREADY</ipxact:logicalName>
			<ipxact:description>indicates that the Receiver can accept a transfer in the current cycle.</ipxact:description>
			<ipxact:wire>
				<ipxact:onInitiator>
					<ipxact:presence>optional</ipxact:presence>
					<ipxact:width>1</ipxact:width>
					<ipxact:direction>in</ipxact:direction>
				</ipxact:onInitiator>
				<ipxact:onTarget>
					<ipxact:presence>optional</ipxact:presence>
					<ipxact:width>1</ipxact:width>
					<ipxact:direction>out</ipxact:direction>
				</ipxact:onTarget>
				<ipxact:defaultValue>1</ipxact:defaultValue>
			</ipxact:wire>
		</ipxact:port>
    </ipxact:ports>
</ipxact:abstractionDefinition>
```

This is a fragment of the `TREADY` signal definition of the AXI 4 Stream interface.

There's the classic VLNV + Description combo at the start, then the associated bus definition is referenced and lastly the signals of the interface are defined.

In IP-XACT, unlike in Topwrap, you can specify different options for signals on both the manager and the subordinate separately, importantly a signal can be required on one side of the bus while being optional on the other. This is currently impossible to represent in Topwrap. The width specification and the default value are not supported either by Topwrap.

Moreover, unlike in Topwrap, in IP-XACT the clock and reset signals are also specified in the definition alongside other signals. They are however marked with special qualifiers that distinguish their roles and enforce certain behaviours.

Example qualifiers:

```xml
<ipxact:wire>
    <ipxact:qualifier>
        <ipxact:isClock>true</ipxact:isClock>
        <ipxact:isReset>true</ipxact:isReset>
    </ipxact:qualifier>
</ipxact:wire>
```

:::{info}
While Topwrap uses the `manager` and `subordinate` terms to refer to the roles an IP can assume in the bus connection, IP-XACT pre-2022 uses `master`, `slave` and IP-XACT 2022-onwards uses `initiator` and `target` respectively.
:::

#### Interface deduction

Topwrap supports specifying both a regex for each signal and the port prefix for the entire interface in order to [automatically group raw ports](../description_files.md#interface-deduction) from HDL sources into interfaces. None of that is possible to represent in IP-XACT, though this information can be stored anyways using [](#vendor-extensions).

### Bus instantiation

To use the bus inside a component definition you have to:
+ Add all the physical ports that will get used as the bus signals just like regular [ad-hoc ports](#port-def)
+ Map these physical ports to logical ports of the interface

#### The portMap format

```yaml
interfaces:
    io:
        type: AXI4Stream
        mode: subordinate
        signals:
            in:
                TDATA: [dat_i, 31, 0]
```

This fragment of [](../description_files.md#design-description) would translate to the below IP-XACT description, assuming the `dat_i` signal was previously defined in the ad-hoc ports section.

```xml
<ipxact:busInterfaces>
    <ipxact:busInterface>
        <ipxact:name>io</ipxact:name>
        <ipxact:busType vendor="amba.com" library="AMBA4" name="AXI4Stream" version="r0p0_1"/>
        <ipxact:abstractionTypes>
            <ipxact:abstractionType>
                <ipxact:abstractionRef vendor="amba.com" library="AMBA4" name="AXI4Stream_rtl" version="r0p0_1"/>
                <ipxact:portMaps>
                    <ipxact:portMap>
                        <ipxact:logicalPort>
                            <ipxact:name>TDATA</ipxact:name>
                        </ipxact:logicalPort>
                        <ipxact:physicalPort>
                            <ipxact:name>dat_i</ipxact:name>
                        </ipxact:physicalPort>
                    </ipxact:portMap>
                </ipxact:portMaps>
            </ipxact:abstractionType>
        <ipxact:abstractionTypes>
        <ipxact:target/>
    </ipxact:busInterface>
</ipxact:busInterfaces>
```

The `<ipxact:busInterfaces>` tag is a direct child of the top-level `<ipxact:component>` tag.

[](../description_files.md#port-slicing) is supported as well:

```xml
<ipxact:physicalPort>
    <ipxact:name>ctrl_i</ipxact:name>
    <ipxact:partSelect>
        <ipxact:range>
            <ipxact:left>4</ipxact:left>
            <ipxact:right>4</ipxact:right>
        </ipxact:range>
    </ipxact:partSelect>
</ipxact:physicalPort>
```

### Inout ports

This example contains an external inout port raised from one of the IPs.
While the [Topwrap syntax](../description_files.md#design-description) for specifying inout ports in a design is a bit awkward, in IP-XACT inout ports are represented just like ports with other directions.

### Constant assignments

This example also features a constant value (2888) assigned to the `noise` port of the `receiver` IP instead of any wire. In IP-XACT this is done similarly to [](#connections):

```xml
<ipxact:adHocConnection>
    <ipxact:name>receiver_0_noise_to_tiedValue</ipxact:name>
    <ipxact:tiedValue>2888</ipxact:tiedValue>
    <ipxact:portReferences>
        <ipxact:internalPortReference componentInstanceRef="receiver_0" portRef="noise"/>
    </ipxact:portReferences>
</ipxact:adHocConnection>
```

Additionally, the `tiedValue` can be given by an arithmetic expression that resolves to a constant value.


## [Hierarchical example](./ir-examples.md#hierarchical)

The hierarchical example features deeply nested hierarchies.
The purpose of a hierarchical design is to group together into separate levels/modules, connections that could just as well be realised flatly in the top-level.

In Topwrap, all hierarchies are specified in the respective [design description file](../description_files.md#hierarchies) YAML using a special syntax that allows multiple design descriptions to be nested together in a single file.

IP-XACT has no notion of any special syntax for hierarchies, because it doesn't need to. Due to the [architecture of design XMLs](#design-structure) being extensions to component XMLs, it's possible to just generate a component+design pair for every hierarchy and connect them just as if they were regular IPs that happen to have a design available alongside them. This is exactly what was done to represent this example.


## [Interconnect example](./ir-examples.md#interconnect)

This example features the [](../interconnect_gen.md) functionality of Topwrap.

Specifying interconnects in the Topwrap design description implies dynamic generation of necessary arbiters and bus components during build-time using parameters defined under the interconnect instance key.

IP-XACT doesn't support such functionality because it's just a file format and it doesn't necessarily have any dynamic code associated with it.

Conversion from Topwrap -> IP-XACT should probably just generate the interconnect bus component with the required amount of manager and subordinate ports and package it alongside the generated RTL implementation of routers and arbiters.

Reverse conversion (from the concrete generated IP-XACT interconnect to Topwrap's interconnect entry) is probably impossible, we can't know the interconnect specifics to know which type to pick after it's already generated.
However, all this necessary information could be stored in a vendor extension.

### The interconnect component

The generated interconnect is located in `./antmicro.com/interconnect/interconnect/wishbone_interconnect1.xml`.
As mentioned, it has just enough interface ports to connect the two specified managers and two subordinates.

The Wishbone interface definition from `opencores.org` was used.

The main difference that differentiates the interconnect component from raw interface connections like in the [](#interface-example) is the explicit definition and mapping of the address space with the `<ipxact:addressSpaces>` tag and assignment of each manager port to one or more subordinates.

The extensions used in the bus instance element in the component definition.
Focus on the `ipxact:addressSpaceRef` tag where the base address of this subordinate is specified:

```xml
<ipxact:busInterface>
    <ipxact:name>target_1</ipxact:name>
    <ipxact:busType vendor="opencores.org" library="interface" name="wishbone" version="b4"/>
    <ipxact:abstractionTypes>
        ...
    </ipxact:abstractionTypes>
    <ipxact:initiator>
        <ipxact:addressSpaceRef addressSpaceRef="address">
            <ipxact:baseAddress>'h10000</ipxact:baseAddress>
        </ipxact:addressSpaceRef>
    </ipxact:initiator>
</ipxact:busInterface>
```

The extension used at the top-level in the component definition to map the address space:

```xml
<ipxact:addressSpaces>
    <ipxact:addressSpace>
        <ipxact:name>address</ipxact:name>
        <ipxact:range>2**32/8-1</ipxact:range>
        <ipxact:width>8</ipxact:width>
        <ipxact:segments>
            <ipxact:segment>
                <ipxact:name>mem</ipxact:name>
                <ipxact:addressOffset>'h0</ipxact:addressOffset>
                <ipxact:range>'hFFFF+1</ipxact:range>
            </ipxact:segment>
            <ipxact:segment>
                <ipxact:name>dsp</ipxact:name>
                <ipxact:addressOffset>'h10000</ipxact:addressOffset>
                <ipxact:range>'hFF+1</ipxact:range>
            </ipxact:segment>
        </ipxact:segments>
        <ipxact:addressUnitBits>8</ipxact:addressUnitBits>
    </ipxact:addressSpace>
</ipxact:addressSpaces>
```

The assignment of a manager port to specified subordinates(targets):

```xml
<ipxact:busInterface>
    <ipxact:name>manager0</ipxact:name>
    <ipxact:busType vendor="opencores.org" library="interface" name="wishbone" version="b4"/>

    <ipxact:target>
        <ipxact:transparentBridge initiatorRef="target_0"/>
        <ipxact:transparentBridge initiatorRef="target_1"/>
    </ipxact:target>
</ipxact:busInterface>
```

### External interface

In the Topwrap definition of this example, a `wishbone_passthrough` IP core is used in order to allow the external interface to be connected as a manager to the interconnect. This is due to limitations of the schema and the fact that under the `managers` key Topwrap expects the IP instance name with the specified manager port, completely disregarding the possibility of it being external.

## [Other features](./ir-examples.md#other)

### Dynamic number of ports/interfaces based on a parameter

This is not possible in IP-XACT.
All ports/interfaces and connections need to be explicitly defined.
While the amount of bits in a port can vary based on a parameter value, as was presented in [](#variable-widths), higher level concepts such as the number of ports cannot.

## Conclusion

In most aspects IP-XACT is a superset of what's possible to describe in Topwrap, making the Topwrap -> IP-XACT conversion pretty trivial.

Syntax impossible to represent natively in IP-XACT such as:
- Abstract interconnects without concrete implementation
- Interface signal name regexes and port prefixes (see [](../description_files.md#interface-deduction))

can even if not implemented, be at least preserved using [](#vendor-extensions).

Other visible issue for this conversion are:
- [](#vlnv) being mandatory for IP-XACT files, but Topwrap containing only the name information
- Lack of input sanitization of string fields on Topwrap's side

On the other hand, the conversion from a generic IP-XACT file to Topwrap's internal representation may prove more tricky and definitely suffer from information loss as the IP-XACT format is packed with more features and elements that are not exactly useful for our purposes and were not even mentioned in this document at all.
