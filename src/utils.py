import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    log.info("$ %s", " ".join(str(c) for c in cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def normalize_class_name(name: str) -> str:
    """Normaliza nome de classe para o join entre SourceMeter e SpotBugs."""
    # Remove sufixos de classes internas anônimas ($1, $2, ...)
    return name.split("$")[0]


def repo_dir_name(owner: str, repo: str) -> str:
    return f"{owner}__{repo}"
