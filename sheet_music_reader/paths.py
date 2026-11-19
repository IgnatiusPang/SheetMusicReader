"""Single source of truth for where code, input data and generated output live."""
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent

DATA_DIR = REPO_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
PSALM_PDF_DIR = INPUT_DIR / "psalms"
CANTABILE_DIR = INPUT_DIR / "Cantabile"
SAMPLES_DIR = INPUT_DIR / "samples"
BENCHMARK_INPUT_DIR = INPUT_DIR / "benchmark_corpus"

OUTPUT_DIR = DATA_DIR / "output"
SCORES_DIR = OUTPUT_DIR / "digitized_scores"
PACKS_DIR = OUTPUT_DIR / "sing_along_packs"
BENCHMARK_DIR = OUTPUT_DIR / "benchmark"
PRACTICE_DIR = OUTPUT_DIR / "practice"

WEB_DIR = PACKAGE_DIR / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"

LEAN_DIR = REPO_ROOT / "formalization" / "lean"
WASM_ENGRAVER_JS = REPO_ROOT / "scripts" / "wasm_engraver.js"
