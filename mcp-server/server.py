#!/usr/bin/env python3
"""
Self-Improve Module Registry MCP Server

提供三个 tool 供 agent 按需检索和安装代码模块：
- search_modules: 搜索模块
- get_module_api: 查看模块 API（不含源码）
- install_module: 安装模块到项目路径
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import uvicorn
from mcp import types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

REPO_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.json"
MODULES_ROOT = REPO_ROOT / "modules"
STATS_PATH = REPO_ROOT / "stats.json"

server = Server("self-improve-modules")


def load_stats() -> dict:
    """加载安装统计数据"""
    if not STATS_PATH.exists():
        return {"installs": []}
    return json.loads(STATS_PATH.read_text(encoding="utf-8"))


def save_stats(stats: dict) -> None:
    """保存安装统计数据"""
    STATS_PATH.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def record_install(module_name: str, target_dir: str) -> None:
    """记录一次模块安装"""
    from datetime import datetime, timezone
    stats = load_stats()
    stats["installs"].append({
        "module": module_name,
        "target_dir": target_dir,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_stats(stats)


def load_registry() -> list[dict[str, Any]]:
    """从 registry.json 加载模块索引"""
    if not REGISTRY_PATH.exists():
        return []
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return data.get("modules", [])


def load_manifest(module_entry: dict[str, Any]) -> dict[str, Any] | None:
    """根据 registry 条目加载对应的 manifest.json"""
    manifest_path = REPO_ROOT / module_entry["path"] / "manifest.json"
    if not manifest_path.exists():
        return None
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def search(query: str) -> list[dict[str, Any]]:
    registry = load_registry()
    query_lower = query.strip().lower()
    keywords = query_lower.split()

    # 空查询返回全部模块
    if not keywords:
        return [
            {
                "name": entry["name"],
                "type": entry["type"],
                "lang": entry["lang"],
                "summary": entry["summary"],
            }
            for entry in registry
        ]

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
    src_dir = REPO_ROOT / entry["path"] / "src"
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

    record_install(module_name, target_dir)

    return [types.TextContent(type="text", text="\n".join(result_parts))]


MCP_PORT = 9475
DASHBOARD_HTML_PATH = Path(__file__).parent / "dashboard.html"

# --- SSE transport ---
sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0], streams[1], server.create_initialization_options()
        )


async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request._send)


# --- Dashboard routes ---
async def dashboard_html(request):
    if not DASHBOARD_HTML_PATH.exists():
        return HTMLResponse("dashboard.html not found", status_code=500)
    return HTMLResponse(DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))


async def dashboard_stats(request):
    registry = load_registry()
    stats = load_stats()
    install_counts: dict[str, int] = {}
    for record in stats.get("installs", []):
        name = record["module"]
        install_counts[name] = install_counts.get(name, 0) + 1

    modules = []
    for entry in registry:
        modules.append({
            "name": entry["name"],
            "type": entry["type"],
            "lang": entry["lang"],
            "summary": entry.get("summary", ""),
            "tags": entry.get("tags", []),
            "installs": install_counts.get(entry["name"], 0),
        })

    return JSONResponse({
        "total_modules": len(registry),
        "total_installs": len(stats.get("installs", [])),
        "modules": modules,
    })


# --- Starlette app ---
app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=handle_messages, methods=["POST"]),
        Route("/", endpoint=dashboard_html),
        Route("/api/stats", endpoint=dashboard_stats),
    ],
)


if __name__ == "__main__":
    print(f"MCP SSE server: http://127.0.0.1:{MCP_PORT}/sse", file=sys.stderr)
    print(f"Dashboard:      http://127.0.0.1:{MCP_PORT}/", file=sys.stderr)
    uvicorn.run(app, host="127.0.0.1", port=MCP_PORT, log_level="warning")
