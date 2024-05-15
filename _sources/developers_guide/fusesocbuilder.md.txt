#  FuseSocBuilder

Topwrap has support for generating FuseSoC's core files with {class}`~topwrap.fuse_helper.FuseSocBuilder`.
Such core file contains information about source files and synthesis tools.
Generation is based on a jinja template that defaults to `topwrap/templates/core.yaml.j2` but can be overridden.

Here's an example of how to generate a simple project:

```python
from topwrap.fuse_helper import FuseSocBuilder
fuse = FuseSocBuilder()

# add source of the IPs used in the project
fuse.add_source('DMATop.v', 'verilogSource')

# add source of the top file
fuse.add_source('top.v', 'verilogSource')

# specify the names of the Core file and the directory where sources are stored
# generate the project
fuse.build('build/top.core', 'sources')
```

:::{warning}
Default template in `topwrap/templates/core.yaml.j2` does not make use of resources added with {meth}`~topwrap.fuse_helper.FuseSocBuilder.add_dependency` or {meth}`~topwrap.fuse_helper.FuseSocBuilder.add_external_ip`, i.e. they won't be present in the generated core file.
:::


```{eval-rst}
.. autoclass:: topwrap.fuse_helper.FuseSocBuilder
   :members:

   .. automethod:: __init__
```
