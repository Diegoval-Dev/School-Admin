# PyInstaller spec: build en modo carpeta (--onedir) sin consola.
import os

from PyInstaller.utils.hooks import collect_all, collect_submodules

RAIZ = os.path.abspath(SPECPATH)
PAQUETES_CON_RECURSOS = ("unfold", "simple_history", "whitenoise")

datas = [
    (os.path.join(RAIZ, "colegio", "templates"), os.path.join("colegio", "templates")),
    (os.path.join(RAIZ, "staticfiles"), "staticfiles"),
    (os.path.join(RAIZ, "assets"), "assets"),
    (os.path.join(RAIZ, "version.txt"), "."),
]
binaries = []
hiddenimports = ["waitress", "sqlite3", "openpyxl", "tkinter"]

for paquete in PAQUETES_CON_RECURSOS:
    datos, binarios, ocultos = collect_all(paquete)
    datas += datos
    binaries += binarios
    hiddenimports += ocultos

hiddenimports += collect_submodules("colegio") + collect_submodules("config")

analisis = Analysis(
    [os.path.join(RAIZ, "launcher.py")],
    pathex=[RAIZ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest"],
)
pyz = PYZ(analisis.pure)
exe = EXE(
    pyz,
    analisis.scripts,
    [],
    exclude_binaries=True,
    name="ColegioJGC",
    console=False,
    icon=os.path.join(RAIZ, "assets", "icono.ico"),
)
coleccion = COLLECT(exe, analisis.binaries, analisis.datas, name="ColegioJGC")
