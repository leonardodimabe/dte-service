#!/usr/bin/env bash
# Vendoriza el motor dte_chile en ./vendor/dte_chile para el build de Docker.
# Uso: bash scripts/vendor_engine.sh [ruta_al_motor]   (default: ../dte_chile)
set -euo pipefail

SRC="${1:-../dte_chile}"
DEST="vendor/dte_chile"

if [ ! -f "$SRC/pyproject.toml" ]; then
  echo "No encuentro el motor en '$SRC' (falta pyproject.toml)." >&2
  exit 1
fi

rm -rf "$DEST"
mkdir -p "$DEST"
cp "$SRC/pyproject.toml" "$DEST/"
cp -r "$SRC/src" "$DEST/"
[ -f "$SRC/README.md" ] && cp "$SRC/README.md" "$DEST/" || true

echo "Motor vendorizado en $DEST"
