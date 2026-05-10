"""脚本模板管理 API。"""

import ast
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Script, Instance
from ..schemas import ScriptCreate, ScriptUpdate, ScriptResponse, ScriptListItem
from ..auth import verify_token

logger = logging.getLogger("zero-rss.api.scripts")
router = APIRouter(prefix="/api/scripts", tags=["scripts"], dependencies=[Depends(verify_token)])


def _parse_script_metadata(code: str) -> dict[str, Any]:
    """解析 Python 脚本中的元数据 (NAME, DESCRIPTION, PARAMS, SCHEDULE 等)。

    通过 AST 安全解析，不执行代码。

    Args:
        code: Python 脚本源代码。

    Returns:
        包含元数据的字典。
    """
    metadata: dict[str, Any] = {
        "name": "",
        "description": "",
        "version": "1.0.0",
        "author": "",
        "params": [],
        "schedule": None,
    }

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return metadata | {"_error": str(e)}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id

                    # 处理字符串类型的元数据
                    if name in ("NAME", "DESCRIPTION", "VERSION", "AUTHOR"):
                        if isinstance(node.value, (ast.Constant, ast.Str)):
                            val = node.value.value if isinstance(node.value, ast.Constant) else node.value.s
                            if name == "NAME":
                                metadata["name"] = val
                            elif name == "DESCRIPTION":
                                metadata["description"] = val
                            elif name == "VERSION":
                                metadata["version"] = val
                            elif name == "AUTHOR":
                                metadata["author"] = val

                    # 处理列表和字典类型的元数据 (PARAMS, SCHEDULE)
                    elif name in ("PARAMS", "SCHEDULE"):
                        if isinstance(node.value, (ast.List, ast.Dict, ast.Constant)):
                            try:
                                val = ast.literal_eval(node.value)
                                if name == "PARAMS":
                                    metadata["params"] = val if isinstance(val, list) else []
                                elif name == "SCHEDULE":
                                    metadata["schedule"] = val
                            except (ValueError, SyntaxError):
                                pass

    return metadata


@router.get("", response_model=list[ScriptListItem])
async def list_scripts(
    search: str = "",
    db: AsyncSession = Depends(get_db),
):
    """获取所有脚本模板列表。"""
    query = select(Script).order_by(Script.updated_at.desc())

    if search:
        query = query.where(
            Script.name.ilike(f"%{search}%") | Script.filename.ilike(f"%{search}%")
        )

    result = await db.execute(query)
    scripts = result.scalars().all()

    # 同时获取每个脚本的实例数
    instance_counts = {}
    count_result = await db.execute(
        select(Instance.script_id, func.count(Instance.id).label("count"))
        .group_by(Instance.script_id)
    )
    for row in count_result:
        instance_counts[row.script_id] = row.count

    items = []
    for s in scripts:
        params_schema = []
        if s.params_schema:
            try:
                params_schema = json.loads(s.params_schema) if isinstance(s.params_schema, str) else s.params_schema
            except (json.JSONDecodeError, TypeError):
                params_schema = []

        default_schedule = None
        if s.default_schedule:
            try:
                default_schedule = json.loads(s.default_schedule) if isinstance(s.default_schedule, str) else s.default_schedule
            except (json.JSONDecodeError, TypeError):
                default_schedule = None

        items.append(ScriptListItem(
            id=s.id,
            name=s.name,
            description=s.description,
            version=s.version,
            author=s.author,
            filename=s.filename,
            params_schema=params_schema,
            default_schedule=default_schedule,
            created_at=s.created_at,
            updated_at=s.updated_at,
            instance_count=instance_counts.get(s.id, 0),
        ))

    return items


@router.post("", response_model=ScriptResponse, status_code=201)
async def create_script(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传并创建新的脚本模板。

    上传的 Python 文件应包含:
    - NAME, DESCRIPTION 变量
    - run(params, context) 函数
    - 可选: PARAMS, SCHEDULE 变量
    """
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="File must be a .py file")

    code = (await file.read()).decode("utf-8")
    metadata = _parse_script_metadata(code)

    if "_error" in metadata:
        raise HTTPException(status_code=400, detail=f"Invalid Python syntax: {metadata['_error']}")
    if not metadata["name"]:
        raise HTTPException(status_code=400, detail="Script must define NAME variable")

    # 检查文件名唯一
    existing = await db.execute(
        select(Script).where(Script.filename == file.filename)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Script filename '{file.filename}' already exists")

    script = Script(
        name=metadata["name"],
        description=metadata.get("description", ""),
        version=metadata.get("version", "1.0.0"),
        author=metadata.get("author", ""),
        filename=file.filename,
        code=code,
        params_schema=json.dumps(metadata.get("params", []), ensure_ascii=False),
        default_schedule=json.dumps(metadata.get("schedule")) if metadata.get("schedule") else None,
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)

    params_schema = json.loads(script.params_schema) if script.params_schema else []
    default_schedule = json.loads(script.default_schedule) if script.default_schedule else None

    return ScriptResponse(
        id=script.id,
        name=script.name,
        description=script.description,
        version=script.version,
        author=script.author,
        filename=script.filename,
        code=script.code,
        params_schema=params_schema,
        default_schedule=default_schedule,
        created_at=script.created_at,
        updated_at=script.updated_at,
    )


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个脚本模板详情。"""
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    params_schema = json.loads(script.params_schema) if script.params_schema else []
    default_schedule = json.loads(script.default_schedule) if script.default_schedule else None

    return ScriptResponse(
        id=script.id,
        name=script.name,
        description=script.description,
        version=script.version,
        author=script.author,
        filename=script.filename,
        code=script.code,
        params_schema=params_schema,
        default_schedule=default_schedule,
        created_at=script.created_at,
        updated_at=script.updated_at,
    )


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: str,
    data: ScriptUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新脚本模板的代码。"""
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    metadata = _parse_script_metadata(data.code)
    if "_error" in metadata:
        raise HTTPException(status_code=400, detail=f"Invalid Python syntax: {metadata['_error']}")
    if not metadata["name"]:
        raise HTTPException(status_code=400, detail="Script must define NAME variable")

    script.code = data.code
    script.name = metadata["name"]
    script.description = metadata.get("description", "")
    script.version = metadata.get("version", "1.0.0")
    script.author = metadata.get("author", "")
    script.params_schema = json.dumps(metadata.get("params", []), ensure_ascii=False)
    script.default_schedule = json.dumps(metadata.get("schedule")) if metadata.get("schedule") else None
    script.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(script)

    params_schema = json.loads(script.params_schema) if script.params_schema else []
    default_schedule = json.loads(script.default_schedule) if script.default_schedule else None

    return ScriptResponse(
        id=script.id,
        name=script.name,
        description=script.description,
        version=script.version,
        author=script.author,
        filename=script.filename,
        code=script.code,
        params_schema=params_schema,
        default_schedule=default_schedule,
        created_at=script.created_at,
        updated_at=script.updated_at,
    )


@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除脚本模板及其所有实例和条目。"""
    script = await db.get(Script, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    await db.delete(script)
    await db.commit()
