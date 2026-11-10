#!/bin/sh
set -e
cd "$(dirname "$0")"
(cd code && python3 -m unittest discover -s tests)
(cd genie && python3 -m unittest)
echo "all tests passed"
