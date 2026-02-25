#!/usr/bin/env python3
"""
注册模块到 registry.json

用法: python commands/register.py modules/utilities/python/http-client
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.json"


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"version": "1.0", "modules": []}
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(data: dict) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def register(module_path: str) -> None:
    """从模块目录读取 manifest.json，注册到 registry"""
    module_dir = REPO_ROOT / module_path
    manifest_path = module_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"错误: {manifest_path} 不存在")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 构建 registry 条目（只保留索引需要的字段）
    entry = {
        "name": manifest["name"],
        "type": manifest["type"],
        "lang": manifest["lang"],
        "summary": manifest["summary"],
        "tags": manifest.get("tags", []),
        "path": module_path,
    }

    registry = load_registry()
    modules = registry["modules"]

    # 去重：同名模块覆盖
    modules = [m for m in modules if m["name"] != entry["name"]]
    modules.append(entry)
    registry["modules"] = modules

    save_registry(registry)
    print(f"✅ 已注册模块: {entry['name']} ({entry['type']}/{entry['lang']})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python commands/register.py <module_path>")
        print("示例: python commands/register.py modules/utilities/python/http-client")
        sys.exit(1)
    register(sys.argv[1])
