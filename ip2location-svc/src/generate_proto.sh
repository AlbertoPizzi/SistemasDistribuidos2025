#!/usr/bin/env bash
set -euo pipefail
python -m grpc_tools.protoc \
-I../protos \
--python_out=. \
--grpc_python_out=. \
../protos/weatherapp.proto