#!/bin/sh -eu

pip install notebook pytest
pip install -r $@

pip install -e .
