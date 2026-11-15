#!/usr/bin/env bash
# Instala el proyecto Space Apps 2026 en ~/proyectos/spaceapps-2026
# Uso (desde la carpeta descomprimida):  bash instalar.sh
set -e

DESTINO=~/proyectos/spaceapps-2026
ORIGEN="$(cd "$(dirname "$0")" && pwd)"

echo "==> Copiando proyecto a $DESTINO"
mkdir -p ~/proyectos
if [ "$ORIGEN" != "$DESTINO" ]; then
  if [ -d "$DESTINO" ]; then
    echo "   $DESTINO ya existe: copio sin sobrescribir archivos tuyos"
    cp -rn "$ORIGEN"/. "$DESTINO"/
  else
    cp -r "$ORIGEN" "$DESTINO"
  fi
fi
cd "$DESTINO"

echo "==> Creando entorno virtual (.venv)"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q

echo "==> Instalando librerias (tarda unos minutos)"
pip install -r requirements.txt -q

echo "==> Comprobando"
python - << 'EOF'
import importlib
mods = ["asf_search","earthaccess","h5py","xarray","rioxarray","rasterio",
        "skimage","geopandas","pandas","yaml","dotenv","matplotlib"]
falta = []
for m in mods:
    try:
        importlib.import_module(m)
    except Exception as e:
        falta.append(f"{m}: {e}")
print("OK: todas las librerias instaladas" if not falta else "FALTAN:\n" + "\n".join(falta))
EOF

[ -f .env ] || cp .env.example .env
echo
echo "==> Listo."
echo "   Activar entorno:  source $DESTINO/.venv/bin/activate"
echo "   Completa tu FIRMS_MAP_KEY en $DESTINO/.env"
echo "   Credenciales Earthdata en ~/.netrc (ver .env.example)"
echo "   NO crees el repo publico en GitHub hasta el sabado 14/11 09:00 (ver docs/project_plan.md)"
