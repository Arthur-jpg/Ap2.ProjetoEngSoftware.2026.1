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
        log.info("=== Fase 1: Descoberta de repos ===")
        from github_discovery import run_fase1
        run_fase1()

    if args.fase is None or args.fase == 2:
        log.info("=== Fase 2: Clone & build ===")
        from clone_build import run_fase2
        run_fase2()

    if args.fase is None or args.fase == 3:
        log.info("=== Fase 3: SourceMeter ===")
        from run_sourcemeter import run_fase3
        run_fase3()

    if args.fase is None or args.fase == 4:
        log.info("=== Fase 4: SpotBugs ===")
        from run_spotbugs import run_fase4
        run_fase4()

    if args.fase is None or args.fase == 5:
        log.info("=== Fase 5: Dataset final ===")
        from build_dataset import run_fase5
        run_fase5()

    log.info("Pipeline concluído.")


if __name__ == "__main__":
    main()
