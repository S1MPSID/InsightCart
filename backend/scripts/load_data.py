"""Load the dimension tables (customers, products, dates) into retail.dim_*.

Safe to re-run: by default it verifies the loaded data and exits without
writing. Pass --force to truncate and reload.

    python load_data.py
    python load_data.py --force
"""

from loader import build_parser, run

TARGETS = [
    ("customers.csv", "dim_customers", "customer_id"),
    ("products.csv", "dim_products", "product_id"),
    ("dates.csv", "dim_date", "date_id"),
]


def main() -> int:
    parser = build_parser(__doc__ or "Load dimension tables")
    args = parser.parse_args()
    return run(TARGETS, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
