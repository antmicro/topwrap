# Hierarchies

Hierarchies allow for creating designs with subgraphs in them.
Subgraphs can contain multiple IP-cores and other subgraphs.
This allows creating nested designs in topwrap.

## Format

All information about hierarchies is specified in [design description](description_files.md).
`hierarchies` key must be a direct descendant of the `design` key.
Format is as follows:

```yaml
hierarchies:
    {hierarchy_name_1}:
      ips: # ips that are used on this hierarchy level
        {ip_name}:
          ...

      design:
        parameters:
          ...
        ports: # ports connections internal to this hierarchy
          # note that also you have to connect port to it's external port equivalent (if exists)
          {ip1_name}:
              {port1_name} : [{ip2_name}, {port2_name}]
              {port2_name} : {port2_external_equivalent} # connection to external port equivalent. Note that it has to be to the parent port
            ...
        hierarchies:
          {nested_hierarchy_name}:
            # structure here will be the same as for {hierarchy_name_1}
            ...
      external:
        # external ports and/or interfaces of this hierarchy; these can be
        # referenced in the upper-level `ports`, `interfaces` or `external` section
        ports:
            in:
              - {port2_external_equivalent}
        ...
    {hierarchy_name_2}:
      ...
```

More complex hierarchy example can be found in [examples/hierarchies](https://github.com/antmicro/topwrap/tree/main/examples/hierarchy).
