import argparse
import asyncio
import html
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
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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

    report = {
        "ok": True,
        "script": script,
        "count": len(result),
        "sample": result[:3],
        "logs": logs[:20],
    }
    return report, result


def _render_raw_block(value: Any) -> str:
    text = "" if value is None else str(value)
    return f"<pre>{html.escape(text)}</pre>"


def _render_preview_block(value: Any) -> str:
    text = "" if value is None else str(value)
    return text


def build_html_report(
    report: dict[str, Any],
    items: list[dict[str, Any]],
    script: str,
    params: dict[str, Any],
) -> str:
    item_cards: list[str] = []
    for i, item in enumerate(items, start=1):
        title = html.escape(str(item.get("title", "")))
        link = str(item.get("link", ""))
        link_escaped = html.escape(link)
        pub_date = html.escape(str(item.get("pub_date", "")))

        description = item.get("description", "")
        content = item.get("content", "")

        item_cards.append(
            "\n".join(
                [
                    '<article class="item">',
                    f"<h2>{i}. {title}</h2>",
                    (
                        '<p class="meta">'
                        f'<a href="{link_escaped}" target="_blank" rel="noopener noreferrer">{link_escaped}</a>'
                        + (f" | pub_date: {pub_date}" if pub_date else "")
                        + "</p>"
                    ),
                    '<section class="block">',
                    '<h3>description 预览</h3>',
                    f'<div class="preview">{_render_preview_block(description)}</div>',
                    '<details><summary>description 原始文本</summary>',
                    _render_raw_block(description),
                    '</details>',
                    '</section>',
                    '<section class="block">',
                    '<h3>content 预览</h3>',
                    f'<div class="preview">{_render_preview_block(content)}</div>',
                    '<details><summary>content 原始文本</summary>',
                    _render_raw_block(content),
                    '</details>',
                    '</section>',
                    '</article>',
                ]
            )
        )

    logs_html = _render_raw_block(json.dumps(report.get("logs", []), ensure_ascii=False, indent=2))
    params_html = _render_raw_block(json.dumps(params, ensure_ascii=False, indent=2))
    report_html = _render_raw_block(json.dumps(report, ensure_ascii=False, indent=2))

    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data: http: https:;" />
  <title>zero-rss script test report</title>
  <style>
    body { font-family: Segoe UI, Arial, sans-serif; margin: 20px; color: #111827; background: #f9fafb; }
    h1, h2, h3 { margin: 0 0 10px; }
    .panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px; margin-bottom: 16px; }
    .meta { color: #4b5563; font-size: 13px; margin: 0 0 12px; word-break: break-all; }
    .item { background: #fff; border: 1px solid #d1d5db; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    .block { border: 1px dashed #d1d5db; border-radius: 8px; padding: 12px; margin-top: 10px; background: #fcfcfd; }
    .preview { line-height: 1.7; }
    pre { white-space: pre-wrap; word-break: break-word; background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow: auto; }
    details { margin-top: 8px; }
    summary { cursor: pointer; color: #1d4ed8; }
    a { color: #2563eb; }
    img { max-width: 100%; height: auto; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #d1d5db; padding: 6px 8px; }
  </style>
</head>
<body>
  <h1>zero-rss 用户脚本测试 HTML 报告</h1>
  <div class="panel">
    <p><strong>script:</strong> __SCRIPT__</p>
    <p><strong>items:</strong> __COUNT__</p>
    <h3>params</h3>
    __PARAMS__
    <h3>report(JSON)</h3>
    __REPORT__
    <h3>logs</h3>
    __LOGS__
  </div>
  __ITEMS__
</body>
</html>
""".replace("__SCRIPT__", html.escape(script)).replace("__COUNT__", str(report.get("count", 0))).replace("__PARAMS__", params_html).replace("__REPORT__", report_html).replace("__LOGS__", logs_html).replace("__ITEMS__", "\n".join(item_cards))


def write_html_report(html_output: str, html_text: str) -> Path:
    out_path = Path(html_output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_text, encoding="utf-8")
    return out_path


async def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test a zero-rss user script")
    parser.add_argument("script", help="Path to the user script .py file")
    parser.add_argument("--params", default="{}", help="JSON string for params")
    parser.add_argument("--params-file", default="", help="Path to a JSON file with params")
    parser.add_argument("--data-dir", default=".tmp-script-data", help="context['data_dir'] value")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for async run")
    parser.add_argument("--min-items", type=int, default=0, help="Minimum expected number of items")
    parser.add_argument(
        "--html-output",
        default="",
        help="Optional path to write standalone HTML report for local RSS content preview",
    )
    args = parser.parse_args()

    if args.params_file:
        params = json.loads(Path(args.params_file).read_text(encoding="utf-8"))
    else:
        params = json.loads(args.params)

    report, items = await run_script(
        script=args.script,
        params=params,
        data_dir=args.data_dir,
        timeout=args.timeout,
        min_items=args.min_items,
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.html_output:
        html_text = build_html_report(
            report=report,
            items=items,
            script=args.script,
            params=params,
        )
        out_path = write_html_report(args.html_output, html_text)
        print(f"HTML report written to: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
