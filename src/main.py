import argparse
import sys

from utils import log


def main():
    parser = argparse.ArgumentParser(description="Pipeline de métricas de código OO")
    parser.add_argument(
        "--fase",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Executar apenas a fase especificada (1-5)",
    )
    args = parser.parse_args()

    if args.fase is None or args.fase == 1:
        from config import REPOS_JSON
        if args.fase is None and REPOS_JSON.exists():
            log.info("=== Fase 1: pulada (repos.json já existe) ===")
        else:
            log.info("=== Fase 1: Descoberta de repos ===")
            from github_discovery import run_fase1
            run_fase1()

    if args.fase is None or args.fase == 2:
        from config import REPOS_JSON, RAW_DIR
        import json
        repos_clonados = (
            REPOS_JSON.exists()
            and all(
                (RAW_DIR / f"{r['owner']}__{r['repo']}").exists()
                for r in json.loads(REPOS_JSON.read_text())
            )
        )
        if args.fase is None and repos_clonados:
            log.info("=== Fase 2: pulada (repos já clonados) ===")
        else:
            log.info("=== Fase 2: Clone & build ===")
            from clone_build import run_fase2
            run_fase2()

    if args.fase is None or args.fase == 3:
        from config import REPOS_JSON
        import json
        sm_feito = (
            REPOS_JSON.exists()
            and any(r.get("sourcemeter_ok") for r in json.loads(REPOS_JSON.read_text()))
        )
        if args.fase is None and sm_feito:
            log.info("=== Fase 3: pulada (SourceMeter já executado) ===")
        else:
            log.info("=== Fase 3: SourceMeter ===")
            from run_sourcemeter import run_fase3
            run_fase3()

    if args.fase is None or args.fase == 4:
        from config import REPOS_JSON
        import json
        spotbugs_feito = (
            REPOS_JSON.exists()
            and any(r.get("spotbugs_ok") for r in json.loads(REPOS_JSON.read_text()))
        )
        if args.fase is None and spotbugs_feito:
            log.info("=== Fase 4: pulada (SpotBugs já executado) ===")
        else:
            log.info("=== Fase 4: SpotBugs ===")
            from run_spotbugs import run_fase4
            run_fase4()

    if args.fase is None or args.fase == 5:
        from config import DATASET_CSV
        if args.fase is None and DATASET_CSV.exists():
            log.info("=== Fase 5: pulada (dataset.csv já existe) ===")
        else:
            log.info("=== Fase 5: Dataset final ===")
            from build_dataset import run_fase5
            run_fase5()

    log.info("Pipeline concluído.")


if __name__ == "__main__":
    main()
