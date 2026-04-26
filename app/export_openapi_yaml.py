from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from app.main import app


def export_openapi_yaml(output_path: str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    schema = app.openapi()
    path.write_text(yaml.safe_dump(schema, sort_keys=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI spec as YAML")
    parser.add_argument(
        "--output",
        default="docs/api/openapi.yaml",
        help="Output path for OpenAPI YAML (default: docs/api/openapi.yaml)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = export_openapi_yaml(args.output)
    print(f"OpenAPI YAML exported to {output}")


if __name__ == "__main__":
    main()
