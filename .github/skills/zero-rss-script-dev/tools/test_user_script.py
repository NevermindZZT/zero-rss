import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
from typing import Any


REQUIRED_EXPORTS = ("NAME", "DESCRIPTION", "run")
REQUIRED_ITEM_FIELDS = ("title", "description", "link")


def load_module(script_path: str):
    path = Path(script_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Script file not found: {path}")

    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script module: {script_path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate_exports(mod: Any) -> None:
    for name in REQUIRED_EXPORTS:
        if not hasattr(mod, name):
            raise AssertionError(f"Missing required export: {name}")


def validate_items(items: Any, min_items: int) -> None:
    if not isinstance(items, list):
        raise AssertionError("run() must return list[dict]")

    if len(items) < min_items:
        raise AssertionError(f"Expected at least {min_items} items, got {len(items)}")

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise AssertionError(f"item[{i}] must be dict")
        missing = [f for f in REQUIRED_ITEM_FIELDS if f not in item]
        if missing:
            raise AssertionError(f"item[{i}] missing required fields: {missing}")


async def run_script(
    script: str,
    params: dict[str, Any],
    data_dir: str,
    timeout: float,
    min_items: int,
) -> dict[str, Any]:
    mod = load_module(script)
    validate_exports(mod)

    logs: list[tuple[str, str]] = []
    context = {
        "logger": {
            "info": lambda m: logs.append(("info", str(m))),
            "error": lambda m: logs.append(("error", str(m))),
        },
        "data_dir": data_dir,
    }

    result = mod.run(params, context)
    if asyncio.iscoroutine(result):
        result = await asyncio.wait_for(result, timeout=timeout)

    validate_items(result, min_items=min_items)

    return {
        "ok": True,
        "script": script,
        "count": len(result),
        "sample": result[:3],
        "logs": logs[:20],
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test a zero-rss user script")
    parser.add_argument("script", help="Path to the user script .py file")
    parser.add_argument("--params", default="{}", help="JSON string for params")
    parser.add_argument("--params-file", default="", help="Path to a JSON file with params")
    parser.add_argument("--data-dir", default=".tmp-script-data", help="context['data_dir'] value")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for async run")
    parser.add_argument("--min-items", type=int, default=0, help="Minimum expected number of items")
    args = parser.parse_args()

    if args.params_file:
        params = json.loads(Path(args.params_file).read_text(encoding="utf-8"))
    else:
        params = json.loads(args.params)

    report = await run_script(
        script=args.script,
        params=params,
        data_dir=args.data_dir,
        timeout=args.timeout,
        min_items=args.min_items,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
