#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${TOURISM_E2E_VENV:-/tmp/tourism-venv}"
PYTHON="${VENV}/bin/python"
REQ="${ROOT}/Tourism/requirement.txt"

if [ ! -x "${PYTHON}" ]; then
  python3 -m venv "${VENV}"
  "${VENV}/bin/pip" install -q -U pip
  if [ -f "${REQ}" ]; then
    "${VENV}/bin/pip" install -q -r "${REQ}" || \
      "${VENV}/bin/pip" install -q Django djangorestframework django-cors-headers \
        djangorestframework-simplejwt python-decouple Pillow
  fi
fi

cd "${ROOT}/Tourism"
"${PYTHON}" manage.py migrate --noinput
"${PYTHON}" manage.py seed_e2e_features
exec "${PYTHON}" manage.py runserver 0.0.0.0:8000
