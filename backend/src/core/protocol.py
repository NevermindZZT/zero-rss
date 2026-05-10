"""用户脚本协议定义。

定义脚本与系统之间的通信协议、类型常量和验证函数。
"""

from typing import Any

# 脚本必须导出的变量
REQUIRED_VARS = ["NAME", "DESCRIPTION"]
REQUIRED_FUNC = "run"

# 可选变量
OPTIONAL_VARS = ["VERSION", "AUTHOR", "PARAMS", "SCHEDULE"]

# 参数类型
PARAM_TYPES = {"string", "number", "boolean", "select", "multiline", "password"}

# 调度类型
SCHEDULE_TYPES = {"interval", "cron", "on_refresh", "manual"}

# RSS 条目必需字段
REQUIRED_ITEM_FIELDS = ["title", "description", "link"]

# RSS 条目可选字段
OPTIONAL_ITEM_FIELDS = ["guid", "pub_date", "author", "categories", "image", "content"]


def validate_item(item: dict[str, Any]) -> list[str]:
    """验证单个 RSS 条目是否合法。

    Args:
        item: 用户脚本返回的条目字典。

    Returns:
        错误信息列表，为空表示合法。
    """
    errors = []
    if not isinstance(item, dict):
        return ["Item must be a dict"]

    for field in REQUIRED_ITEM_FIELDS:
        if field not in item or not item.get(field):
            errors.append(f"Missing required field: {field}")

    return errors
