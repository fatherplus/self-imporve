#!/usr/bin/env python3
"""
Self-Improve Module Registry MCP Server

提供三个 tool 供 agent 按需检索和安装代码模块：
- search_modules: 搜索模块
- get_module_api: 查看模块 API（不含源码）
- install_module: 安装模块到项目路径
"""

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import mcp.server.stdio
from mcp import types
from mcp.server import Server

REGISTRY_PATH = Path(__file__).parent.parent / "registry.json"
MODULES_ROOT = Path(__file__).parent.parent / "modules"

server = Server("self-improve-modules")


def load_registry() -> list[dict[str, Any]]:
    """从 registry.json 加载模块索引"""
    if not REGISTRY_PATH.exists():
        return []
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("modules", [])


def load_manifest(module_entry: dict[str, Any]) -> dict[str, Any] | None:
    """根据 registry 条目加载对应的 manifest.json"""
    manifest_path = MODULES_ROOT / module_entry["path"] / "manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def search(query: str) -> list[dict[str, Any]]:
    registry = load_registry()
    query_lower = query.lower()
    keywords = query_lower.split()
    scored: list[tuple[int, dict]] = []

    for entry in registry:
        score = 0
        tags = [t.lower() for t in entry.get("tags", [])]
        name = entry["name"].lower()
        summary = entry.get("summary", "").lower()

        for kw in keywords:
            if kw in tags:
                score += 10
            if kw in name:
                score += 5
            if kw in summary:
                score += 1

        if score > 0:
            scored.append((score, {
                "name": entry["name"],
                "type": entry["type"],
                "lang": entry["lang"],
                "summary": entry["summary"],
            }))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


def find_entry(name: str) -> dict[str, Any] | None:
    """按 name 查找 registry 条目"""
    for entry in load_registry():
        if entry["name"] == name:
            return entry
    return None


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="search_modules",
            description="搜索可复用代码模块，返回匹配的模块名和摘要列表",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词（匹配模块名、摘要、标签）",
                    }
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_module_api",
            description="查看模块的 API 文档（不含源码），了解如何使用该模块",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "模块名（从 search_modules 结果中获取）",
                    }
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="install_module",
            description="安装模块到项目指定路径，复制源码文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "模块名",
                    },
                    "target_dir": {
                        "type": "string",
                        "description": "安装目标路径（如 ./lib）",
                    },
                },
                "required": ["name", "target_dir"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "search_modules":
        return _handle_search(arguments["query"])
    elif name == "get_module_api":
        return _handle_get_api(arguments["name"])
    elif name == "install_module":
        return _handle_install(arguments["name"], arguments["target_dir"])
    return [types.TextContent(type="text", text=f"未知工具: {name}")]


def _handle_search(query: str) -> list[types.TextContent]:
    results = search(query)
    if not results:
        return [types.TextContent(type="text", text="未找到匹配的模块")]
    text = json.dumps(results, ensure_ascii=False, indent=2)
    return [types.TextContent(type="text", text=text)]


def _handle_get_api(module_name: str) -> list[types.TextContent]:
    entry = find_entry(module_name)
    if not entry:
        return [types.TextContent(type="text", text=f"模块 '{module_name}' 不存在")]

    manifest = load_manifest(entry)
    if not manifest:
        return [types.TextContent(type="text", text=f"模块 '{module_name}' 的 manifest.json 缺失")]

    # 构建 API 文档（不含源码）
    doc_parts = [
        f"# {manifest['name']}",
        f"\n**类型:** {manifest['type']} | **语言:** {manifest['lang']}",
        f"\n**简介:** {manifest['summary']}",
    ]

    # 安装信息
    if install := manifest.get("install"):
        doc_parts.append(f"\n## 安装")
        if deps := install.get("dependencies"):
            doc_parts.append(f"依赖: {', '.join(deps)}")
        if entry_point := install.get("entry"):
            doc_parts.append(f"导入: `{entry_point}`")

    # API 定义
    if api := manifest.get("api"):
        doc_parts.append(f"\n## API")
        doc_parts.append(json.dumps(api, ensure_ascii=False, indent=2))

    # 适配点（component 专属）
    if adapt := manifest.get("adapt_points"):
        doc_parts.append(f"\n## 适配点")
        for point in adapt:
            doc_parts.append(f"- {point}")

    # 设计决策（blueprint 专属）
    if decisions := manifest.get("design_decisions"):
        doc_parts.append(f"\n## 设计决策")
        for d in decisions:
            doc_parts.append(f"- {d}")

    return [types.TextContent(type="text", text="\n".join(doc_parts))]


def _handle_install(module_name: str, target_dir: str) -> list[types.TextContent]:
    entry = find_entry(module_name)
    if not entry:
        return [types.TextContent(type="text", text=f"模块 '{module_name}' 不存在")]

    if entry["type"] == "blueprint":
        return [types.TextContent(
            type="text",
            text=f"blueprint 类型模块不支持安装，请用 get_module_api 查看架构指导",
        )]

    manifest = load_manifest(entry)
    if not manifest:
        return [types.TextContent(type="text", text=f"manifest.json 缺失")]

    # 源码目录
    src_dir = MODULES_ROOT / entry["path"] / "src"
    if not src_dir.exists():
        return [types.TextContent(type="text", text=f"源码目录不存在: {src_dir}")]

    # 目标目录: target_dir/module_name/
    module_slug = module_name.replace("-", "_")
    dest = Path(target_dir).resolve() / module_slug
    dest.mkdir(parents=True, exist_ok=True)

    # 复制文件
    copied = []
    for src_file in src_dir.rglob("*"):
        if src_file.is_file():
            rel = src_file.relative_to(src_dir)
            dst_file = dest / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            copied.append(str(rel))

    # 构建安装结果
    install_info = manifest.get("install", {})
    result_parts = [
        f"✅ 模块 '{module_name}' 已安装到 {dest}",
        f"复制文件: {', '.join(copied)}",
    ]
    if deps := install_info.get("dependencies"):
        result_parts.append(f"需安装依赖: {', '.join(deps)}")
    if entry_point := install_info.get("entry"):
        result_parts.append(f"导入方式: {entry_point}")

    return [types.TextContent(type="text", text="\n".join(result_parts))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
