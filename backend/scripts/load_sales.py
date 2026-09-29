"""Load sales.csv into retail.fact_sales.

Safe to re-run: by default it verifies the loaded data and exits without
writing. Pass --force to truncate and reload.

    python load_sales.py
    python load_sales.py --force
"""

from loader import build_parser, run

TARGETS = [
    ("sales.csv", "fact_sales", "sale_id"),
]


def main() -> int:
    parser = build_parser(__doc__ or "Load the sales fact table")
    args = parser.parse_args()
    return run(TARGETS, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
