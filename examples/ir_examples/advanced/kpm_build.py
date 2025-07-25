import json

from ir.design import module

from topwrap.backend.kpm.backend import KpmBackend

out = KpmBackend(depth=-1).represent(module)

with open("./kpm_spec.json", "w") as s, open("./kpm_dataflow.json", "w") as d:
    json.dump(out.dataflow, d)
    json.dump(out.specification, s)
