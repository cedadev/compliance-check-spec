# compliance-check-spec

Write HTML specifications for AMF check suites generated from YAML files.

**Note:** This is a work in progress and has not been thoroughly tested.

## Installation

Use a Python 2.7 virtual environment:

```
virtualenv -p python2.7 venv
source activate venv

pip install -e ./compliance-check-spec

# Make sure compliance-check-lib is present at the same level as this repo
git clone https://github.com/cedadev/compliance-check-lib ../compliance-check-lib
pip install -e ../compliance-check-lib
```

## Usage

See `write-spec --help` for full usage instructions. Basic use is as follows:

```
write-spec -p PROJECT_METADATA.yml -o spec.html /path/to/yaml/AMF_*.yml
```

### Project metadata

The `PROJECT_METADATA.yml` file contains some project-level data used in the
output HTML file. It **must** have the following keys:

* canonicalName
* label
* description
* vocab_authority
* vocab_scope
* checks_version

It may **optionally** include

* url

### YAML files

The YAML files should be created with
[amf-check-writer](https://github.com/ncasuk/amf-check-writer).
