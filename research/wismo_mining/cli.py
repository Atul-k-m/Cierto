"""Command line: collect | classify | report | compare | sample | validate | run."""
from __future__ import annotations

import argparse
import sys

from .config import load_brands


def _brands(arg: str | None) -> list[str]:
    known = load_brands()
    keys = list(known) if not arg or arg == "all" else [b.strip() for b in arg.split(",") if b.strip()]
    bad = [k for k in keys if k not in known]
    if bad:
        sys.exit(f"unknown brand(s): {', '.join(bad)}; known: {', '.join(known)}")
    return keys


def cmd_collect(a) -> None:
    from .collectors import collect_brand
    brands = load_brands()
    only = a.sources.split(",") if a.sources else None
    for k in _brands(a.brands):
        print(f"[collect] {k}")
        collect_brand(brands[k], only=only)


def cmd_classify(a) -> None:
    from .classify import classify_brand
    for k in _brands(a.brands):
        n, w = classify_brand(k)
        print(f"[classify] {k}: {n} rows, {w} WISMO-related")


def cmd_report(a) -> None:
    from .report import write_brand_report
    for k in _brands(a.brand):
        print(f"[report] {write_brand_report(k)}")


def cmd_compare(a) -> None:
    from .report import write_compare_report
    print(f"[compare] {write_compare_report(_brands(a.brands))}")


def cmd_sample(a) -> None:
    from .validate import draw_sample
    for k in _brands(a.brands):
        print(f"[sample] {draw_sample(k, a.n, a.seed, a.tag, a.positives, a.neg_pool)}")


def cmd_validate(a) -> None:
    from .validate import evaluate
    for k in _brands(a.brands):
        print(evaluate(k, tag=a.tag, save=a.save, taxonomy=a.taxonomy))


def cmd_run(a) -> None:
    a.sources = None
    if not a.skip_collect:
        cmd_collect(a)
    cmd_classify(a)
    a.brand = a.brands
    cmd_report(a)
    cmd_compare(a)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="wismo_mining", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("collect", help="fetch reviews into data/reviews/<brand>/<source>.jsonl")
    s.add_argument("--brands", default="all")
    s.add_argument("--sources", help="comma list, e.g. google_play,app_store")
    s.set_defaults(fn=cmd_collect)

    s = sub.add_parser("classify", help="apply taxonomy.yaml -> data/classified/<brand>.jsonl")
    s.add_argument("--brands", default="all")
    s.set_defaults(fn=cmd_classify)

    s = sub.add_parser("report", help="write docs/research/wismo-<brand>.md")
    s.add_argument("--brand", required=True, help="brand key or comma list")
    s.set_defaults(fn=cmd_report)

    s = sub.add_parser("compare", help="write docs/research/wismo-compare.md")
    s.add_argument("--brands", default="all")
    s.set_defaults(fn=cmd_compare)

    s = sub.add_parser("sample", help="draw a seeded validation sample to hand-label")
    s.add_argument("--brands", default="all")
    s.add_argument("--n", type=int, default=60)
    s.add_argument("--positives", type=float, default=0.75, help="share drawn from classifier-WISMO rows")
    s.add_argument("--seed", type=int, default=20260930)
    s.add_argument("--tag", default="A")
    s.add_argument("--neg-pool", default="all", choices=["all", "low"],
                   help="draw predicted-non-WISMO rows from all ratings or only 1-2 star / complaint posts")
    s.set_defaults(fn=cmd_sample)

    s = sub.add_parser("validate", help="score the classifier against hand labels")
    s.add_argument("--brands", default="all")
    s.add_argument("--tag", default="A", help="label set to score against")
    s.add_argument("--save", help="save a metrics snapshot under this name (e.g. v1)")
    s.add_argument("--taxonomy", help="score a frozen taxonomy snapshot instead of taxonomy.yaml")
    s.set_defaults(fn=cmd_validate)

    s = sub.add_parser("run", help="collect + classify + report + compare")
    s.add_argument("--brands", default="all")
    s.add_argument("--skip-collect", action="store_true", help="reuse data already collected")
    s.set_defaults(fn=cmd_run)

    a = p.parse_args(argv)
    a.fn(a)
    return 0
