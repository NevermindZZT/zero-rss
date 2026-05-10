"""脚本执行引擎。

通过 subprocess 在独立进程中安全执行用户 Python 脚本，
传递参数并通过 stdout 捕获返回结果。
"""

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from ..config import settings
from .protocol import validate_item, REQUIRED_VARS, REQUIRED_FUNC


class ScriptError(Exception):
    """脚本执行相关错误。"""
    pass


async def run_script(
    code: str,
    params: dict[str, Any],
    instance_id: str,
    timeout: int | None = None,
) -> list[dict[str, Any]]:
    """执行用户脚本并返回 RSS 条目列表。

    Args:
        code: Python 脚本源代码。
        params: 传递给脚本的参数。
        instance_id: 实例 ID (用于日志)。
        timeout: 超时秒数，默认使用配置值。

    Returns:
        RSS 条目字典列表。

    Raises:
        ScriptError: 脚本执行失败或返回无效数据。
    """
    if timeout is None:
        timeout = settings.script_timeout

    # 构建包装脚本: 导入用户脚本, 调用 run(), 输出 JSON
    wrapper = _build_wrapper(code, params)

    loop = asyncio.get_event_loop()

    def _run():
        try:
            result = subprocess.run(
                [sys.executable, "-c", wrapper],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(settings.scripts_dir_path),
            )

            if result.returncode != 0:
                stderr = result.stderr.strip() or "Unknown error"
                raise ScriptError(f"Script exited with code {result.returncode}: {stderr}")

            if not result.stdout.strip():
                return []

            try:
                items = json.loads(result.stdout.strip())
            except json.JSONDecodeError as e:
                raise ScriptError(f"Script output is not valid JSON: {e}")

            if not isinstance(items, list):
                raise ScriptError("Script must return a list of items")

            # 验证每个条目
            for i, item in enumerate(items):
                errs = validate_item(item)
                if errs:
                    raise ScriptError(f"Item {i} validation failed: {', '.join(errs)}")

            return items

        except subprocess.TimeoutExpired:
            raise ScriptError(f"Script timed out after {timeout}s")

    return await loop.run_in_executor(None, _run)


async def test_script(code: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    """测试运行脚本 (不保存结果，带默认超时)。

    Args:
        code: 脚本源代码。
        params: 测试参数。

    Returns:
        RSS 条目列表。
    """
    return await run_script(code, params, instance_id="test", timeout=30)


def _build_wrapper(code: str, params: dict[str, Any]) -> str:
    """构建包装脚本，将用户脚本代码嵌入可执行上下文。

    包装脚本:
    1. 解析用户脚本的 NAME, DESCRIPTION 等元数据验证
    2. 调用 run(params, context) 获取结果
    3. 将结果以 JSON 格式打印到 stdout
    """
    return f'''
import json, sys, traceback, asyncio
from typing import Any

# 用户脚本代码
_USER_CODE = {json.dumps(code)}

# 编译并执行用户代码以提取 run 函数
_global_vars = {{}}
exec(compile(_USER_CODE, "<user_script>", "exec"), _global_vars)

# 验证必需导出
_REQUIRED_VARS = {json.dumps(REQUIRED_VARS)}
for _var in _REQUIRED_VARS:
    if _var not in _global_vars:
        print(json.dumps({{"error": f"Missing required variable: {{_var}}"}}), file=sys.stderr)
        sys.exit(1)

if "run" not in _global_vars:
    print(json.dumps({{"error": "Missing required function: run"}}), file=sys.stderr)
    sys.exit(1)

# 构建上下文
_context = {{
    "logger": {{"info": lambda m: None, "error": lambda m: None}},
    "data_dir": ".",
}}

# 运行
try:
    _run_func = _global_vars["run"]
    _params = {json.dumps(params)}
    _items = _run_func(_params, _context)

    # 支持同步和异步
    if asyncio.iscoroutine(_items):
        _items = asyncio.run(_items)

    print(json.dumps(_items, default=str, ensure_ascii=False))
except Exception as _e:
    print(json.dumps({{"error": str(_e), "traceback": traceback.format_exc()}}), file=sys.stderr)
    sys.exit(1)
'''
