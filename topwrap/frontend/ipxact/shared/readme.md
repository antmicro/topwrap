## Introduction

`xml_schema.py` was generated using generateDS and the IP-XACT 2022 schema.

It was necessary to patch generateDS and modify some tags in the IP-XACT schema.

## How to generate

Clone the generateDS and IP-XACT schema repositories into the same directory using the following commands:

```bash
git clone TODO generateDS
git clone TODO ipxact-schema
```

Go to the `ipxact-schema/ieee-1685-2022/` directory:

```bash
cd ipxact-schema/ieee-1685-2022/
```

Create the `out` directory. This is necessary because generateDS will not create it automatically:

```bash
mkdir out
```

Run generateDS with `--no-pattern-validator`. This option disables regex pattern validation, which is necessary because the regex patterns used in the IP-XACT schema are incompatible with Python's `re` module:

```bash
python3 ../../generateDS/generateDS.py -o "out/ipxact.py" --no-pattern-validator index.xsd
```

