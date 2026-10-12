import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SCRIPT_PREPARAR = """
import os
from pathlib import Path
import django
django.setup()
import launcher
launcher._preparar_base(Path(os.environ["COLEGIO_TEST_DB"]), Path(os.environ["COLEGIO_TEST_BK"]))
"""


def ejecutar_en_proceso(comando, datos: Path, *args) -> subprocess.CompletedProcess:
    entorno = {
        **os.environ,
        "COLEGIO_DATA_DIR": str(datos),
        "COLEGIO_TEST_DB": str(datos / "colegio.db"),
        "COLEGIO_TEST_BK": str(datos.parent / "respaldos"),
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "PYTHONUTF8": "1",
    }
    return subprocess.run([sys.executable, *comando, *args], cwd=RAIZ, env=entorno, capture_output=True, text=True)


def contar_respaldos_antes_de_migrar(carpeta: Path) -> int:
    if not carpeta.exists():
        return 0
    return len([archivo for archivo in carpeta.iterdir() if archivo.name.endswith("-antes-de-migrar.db")])


class RespaldoAntesDeMigrarTests(unittest.TestCase):
    def setUp(self):
        self._directorio = tempfile.TemporaryDirectory()
        self.raiz = Path(self._directorio.name)
        self.datos = self.raiz / "datos"
        self.datos.mkdir()

    def tearDown(self):
        self._directorio.cleanup()

    def test_primer_arranque_sin_base_no_crea_respaldo_previo(self):
        resultado = ejecutar_en_proceso(["-c", SCRIPT_PREPARAR], self.datos)

        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertTrue((self.datos / "colegio.db").exists())
        self.assertEqual(contar_respaldos_antes_de_migrar(self.raiz / "respaldos"), 0)

    def test_base_existente_con_migraciones_pendientes_crea_exactamente_un_respaldo_previo(self):
        base = ejecutar_en_proceso(["manage.py", "migrate", "colegio", "0001"], self.datos)
        self.assertEqual(base.returncode, 0, base.stderr)

        resultado = ejecutar_en_proceso(["-c", SCRIPT_PREPARAR], self.datos)

        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual(contar_respaldos_antes_de_migrar(self.raiz / "respaldos"), 1)
