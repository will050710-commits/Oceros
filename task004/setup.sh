#!/usr/bin/env bash
set -euo pipefail
cd /workspace/Oceros
python3 -m venv /workspace/.venvs/oceros-task004
/workspace/.venvs/oceros-task004/bin/python -m pip install --disable-pip-version-check -r task004/requirements.txt
/workspace/.venvs/oceros-task004/bin/python -m task004.cli validate-config --config task004/mock_config.json
