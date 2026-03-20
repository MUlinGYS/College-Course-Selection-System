# 代码库编码检查和乱码检测工具
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
INCLUDE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".vue",
    ".css",
    ".html",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
}
SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
}
SUSPICIOUS_FRAGMENTS = (
    "鐧",
    "鍒",
    "寮€",
    "瀛",
    "璇",
    "绠",
    "缁",
    "闂",
    "鍛",
    "鏁",
    "锛",
    "銆",
    "褰",
    "閫",
    "宸",
    "鐝",
)


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if should_skip(path):
            continue
        if path.suffix.lower() not in INCLUDE_SUFFIXES:
            continue
        files.append(path)
    return files


def main() -> int:
    utf8_errors: list[str] = []
    suspicious_files: list[str] = []

    for path in iter_source_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            utf8_errors.append(f"{path.relative_to(ROOT)}: {exc}")
            continue

        if path == Path(__file__).resolve():
            continue

        if "\ufffd" in text or any(fragment in text for fragment in SUSPICIOUS_FRAGMENTS):
            suspicious_files.append(str(path.relative_to(ROOT)))

    if utf8_errors:
        print("以下文件不是有效 UTF-8：")
        for item in utf8_errors:
            print(f"  - {item}")

    if suspicious_files:
        print("以下文件包含可疑乱码片段，请人工复核：")
        for item in suspicious_files:
            print(f"  - {item}")

    if utf8_errors or suspicious_files:
        return 1

    print("编码检查通过：所有扫描文件均为 UTF-8，且未发现明显乱码片段。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
