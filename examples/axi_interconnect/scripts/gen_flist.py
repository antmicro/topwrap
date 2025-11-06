import sys

import topwrap_axi_core_plugin

if len(sys.argv) <= 2:
    print(f"Usage: {sys.argv[0]} source_flist include_flist")
    sys.exit(0)


with open(sys.argv[1], "w") as f:
    f.write("\n".join(topwrap_axi_core_plugin.get_dependencies()))

with open(sys.argv[2], "w") as f:
    f.write("\n".join(topwrap_axi_core_plugin.get_includes()))
