# AI-assisted: written with Claude (Anthropic) from the author’s specifications; reviewed and run by the author. See docs/ai_use.md
"""
Verificacion de descargas NISAR GCOV (preparacion, NO procesa datos).

Para cada .h5 de la carpeta revisa:
  - que el archivo abra (no este corrupto)
  - tamano y CRID (del nombre del archivo)
  - que existan HHHH y HVHV en frequencyA
  - que la grilla cubra el recuadro del proyecto (config/aoi.geojson)

Uso (desde la raiz del proyecto, con el .venv activado):
    python scripts/verificar_descargas.py data/raw/nisar_gcov
"""
import json
import re
import sys
from pathlib import Path

import h5py
import numpy as np
from pyproj import Transformer

RAIZ = Path(__file__).resolve().parents[1]
AOI_FILE = RAIZ / "config" / "aoi.geojson"


def aoi_lonlat():
    gj = json.loads(AOI_FILE.read_text())
    coords = np.array(gj["features"][0]["geometry"]["coordinates"][0])
    return coords[:, 0], coords[:, 1]


def buscar(h5, nombre, dentro_de="frequencyA"):
    hallados = []
    def ver(ruta, obj):
        if ruta.split("/")[-1] == nombre and dentro_de in ruta:
            hallados.append(ruta)
    h5.visititems(ver)
    return hallados


def epsg_de(h5, grupo):
    # Busca un dataset/atributo de proyeccion cerca de la grilla
    for ruta in buscar(h5, "projection", dentro_de=grupo.split("/")[0] or ""):
        ds = h5[ruta]
        for clave in ("epsg_code", "epsg", "spatial_ref"):
            if clave in ds.attrs:
                val = ds.attrs[clave]
                try:
                    return int(np.asarray(val).ravel()[0])
                except Exception:
                    pass
        try:
            return int(np.asarray(ds[()]).ravel()[0])
        except Exception:
            pass
    return None


def cobertura(h5, ruta_banda):
    grupo = ruta_banda.rsplit("/", 1)[0]
    xs = buscar(h5, "xCoordinates", dentro_de=grupo)
    ys = buscar(h5, "yCoordinates", dentro_de=grupo)
    if not xs or not ys:
        return None, "sin xCoordinates/yCoordinates"
    x = h5[xs[0]][()]
    y = h5[ys[0]][()]
    epsg = epsg_de(h5, grupo)
    if epsg is None:
        return None, "no encontre el EPSG"
    lon, lat = aoi_lonlat()
    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    ax, ay = tr.transform(lon, lat)
    # fraccion del bbox del AOI dentro de la grilla
    gx0, gx1 = min(x[0], x[-1]), max(x[0], x[-1])
    gy0, gy1 = min(y[0], y[-1]), max(y[0], y[-1])
    ax0, ax1, ay0, ay1 = ax.min(), ax.max(), ay.min(), ay.max()
    ix = max(0, min(gx1, ax1) - max(gx0, ax0))
    iy = max(0, min(gy1, ay1) - max(gy0, ay0))
    frac = (ix * iy) / ((ax1 - ax0) * (ay1 - ay0))
    paso = abs(x[1] - x[0])
    return frac, f"EPSG:{epsg}, pixel {paso:.0f} m"


def main():
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "data/raw/nisar_gcov"
    archivos = sorted(carpeta.glob("*.h5"))
    if not archivos:
        print(f"No hay .h5 en {carpeta}")
        return
    print(f"{'fecha':10s} {'GB':>5s} {'CRID':7s} {'HH':3s} {'HV':3s} {'AOI%':>5s}  notas")
    for f in archivos:
        nombre = f.name
        fecha = re.search(r"_(\d{8})T", nombre)
        fecha = fecha.group(1) if fecha else "?"
        fecha = f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:]}" if fecha != "?" else fecha
        crid = re.search(r"_(P\d{5})_", nombre)
        crid = crid.group(1) if crid else "?"
        gb = f.stat().st_size / 1e9
        try:
            with h5py.File(f, "r") as h5:
                hh = buscar(h5, "HHHH")
                hv = buscar(h5, "HVHV")
                frac, nota = (None, "sin HHHH")
                if hh:
                    frac, nota = cobertura(h5, hh[0])
                aoi = f"{100 * frac:5.1f}" if frac is not None else "  ?  "
                print(f"{fecha:10s} {gb:5.2f} {crid:7s} {'si' if hh else 'NO':3s} "
                      f"{'si' if hv else 'NO':3s} {aoi}  {nota}")
        except Exception as e:
            print(f"{fecha:10s} {gb:5.2f} {crid:7s} ERROR al abrir: {e}")
    print("\nAOI% = parte del recuadro dentro de la grilla del archivo. Lo esperado es ~100.")
    print("Ojo: la grilla es un rectangulo que incluye bordes sin dato (NoData),")
    print("asi que la esquina que vimos fuera del frame puede contar como 'cubierta'.")
    print("Si un archivo da mucho menos de 100, esa fecha no cubre el recuadro.")


if __name__ == "__main__":
    main()
