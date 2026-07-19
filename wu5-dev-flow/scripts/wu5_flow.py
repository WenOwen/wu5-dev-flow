#!/usr/bin/env python3
"""Deterministic project gates for the Wu5 SDD/TDD/Git workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


WORKFLOW_VERSION = 2
SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"
SPEC_DOCS = ("proposal.md", "spec.md", "design.md")
PLAN_DOCS = ("plan.md", "test-plan.md")
BASELINE_DOCS = (
    "system-map.md",
    "behavior-map.md",
    "test-map.md",
    "risks.md",
    "debt.md",
    "adoption-plan.md",
)
SOURCE_SUFFIXES = {
    ".py", ".pyi", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
    ".kt", ".cs", ".cpp", ".c", ".h", ".rb", ".php", ".swift",
}
MANIFESTS = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "poetry.lock",
    "uv.lock", "Pipfile", "package.json", "Cargo.toml", "go.mod",
}
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "dist", "build", "target",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    ".nox", ".coverage", "htmlcov", ".idea", ".vscode", "spec",
}
SECRET_NAMES = {
    ".env", ".env.local", ".env.production", "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519",
}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
DEPENDENCY_NAMES = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt",
    "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock",
}
MIGRATION_PARTS = {"migrations", "migration", "alembic", "versions"}
AGENTS_START = "<!-- wu5-dev-flow:start -->"
AGENTS_END = "<!-- wu5-dev-flow:end -->"
PLACEHOLDER_TOKENS = ("待定义", "待填写", "<!-- AI 完整扫描后补充。 -->")


class FlowError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def redact_output(text: str) -> str:
    patterns = (
        r"(?i)\b(api[_-]?key|token|password|passwd|secret)\s*[=:]\s*[^\s,;]+",
        r"(?i)\bauthorization:\s*bearer\s+[^\s]+",
        r"\b(ghp|github_pat|sk)-[A-Za-z0-9_-]{12,}\b",
    )
    redacted = text
    for pattern in patterns:
        redacted = re.sub(pattern, "[REDACTED]", redacted)
    return redacted


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FlowError(f"缺少文件：{path}") from exc
    except json.JSONDecodeError as exc:
        raise FlowError(f"JSON 格式无效：{path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_json(path: Path, value: dict[str, Any]) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def render_template(relative: str, replacements: dict[str, str]) -> str:
    text = (TEMPLATES / relative).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def run(
    command: list[str], root: Path, *, check: bool = False, capture: bool = True
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=root,
            check=check,
            shell=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=capture,
        )
    except FileNotFoundError as exc:
        raise FlowError(f"找不到命令：{command[0]}") from exc


def git(root: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], root, check=check)


def is_git_repo(root: Path) -> bool:
    return git(root, "rev-parse", "--is-inside-work-tree").returncode == 0


def current_branch(root: Path) -> str:
    result = git(root, "branch", "--show-current")
    return result.stdout.strip() or "(detached)"


def head_commit(root: Path) -> str | None:
    result = git(root, "rev-parse", "HEAD")
    return result.stdout.strip() if result.returncode == 0 else None


def status_lines(root: Path) -> list[str]:
    result = git(root, "status", "--porcelain=v1", "--untracked-files=all", check=True)
    return [line for line in result.stdout.splitlines() if line]


def staged_files(root: Path) -> list[str]:
    result = git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", check=True)
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def is_secret_path(relative: str) -> bool:
    path = Path(relative)
    lower_name = path.name.lower()
    return (
        lower_name in {name.lower() for name in SECRET_NAMES}
        or lower_name.startswith(".env.")
        or path.suffix.lower() in SECRET_SUFFIXES
        or any(part.lower() in {"secrets", "credentials"} for part in path.parts)
    )


def safe_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for base, dirs, names in os.walk(root):
        base_path = Path(base)
        dirs[:] = [
            name for name in dirs
            if name not in EXCLUDED_DIRS and not (base_path / name).is_symlink()
        ]
        for name in names:
            path = base_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or is_secret_path(relative):
                continue
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def detect_project_kind(root: Path) -> str:
    for path in safe_project_files(root):
        relative = path.relative_to(root)
        if relative.as_posix() in {"README.md", "README.txt", ".gitignore", "AGENTS.md"}:
            continue
        if path.name in MANIFESTS or path.suffix.lower() in SOURCE_SUFFIXES:
            return "legacy"
        if "tests" in {part.lower() for part in relative.parts} or path.name.startswith("test_"):
            return "legacy"
    return "empty"


def ruff_configured(root: Path) -> bool:
    if (root / "ruff.toml").exists() or (root / ".ruff.toml").exists():
        return True
    pyproject = root / "pyproject.toml"
    if not pyproject.exists() or is_secret_path(pyproject.name):
        return False
    try:
        return "[tool.ruff" in pyproject.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def default_workflow(project_kind: str, root: Path) -> dict[str, Any]:
    return {
        "workflow_version": WORKFLOW_VERSION,
        "project_kind": project_kind,
        "protected_branches": ["main", "master"],
        "quality_commands": [
            {"name": "pytest", "command": ["python", "-m", "pytest"], "required": True, "enabled": True},
            {"name": "pyright", "command": ["pyright"], "required": True, "enabled": True},
            {"name": "ruff", "command": ["ruff", "check", "."], "required": False, "enabled": ruff_configured(root)},
        ],
        "coverage_must_not_decrease_when_configured": True,
        "remote": "github",
        "merge_strategy": "squash",
    }


def initial_state(project_kind: str) -> dict[str, Any]:
    return {
        "workflow_version": WORKFLOW_VERSION,
        "project_kind": project_kind,
        "phase": "baseline-review" if project_kind == "legacy" else "ready",
        "active_change": None,
        "approvals": {
            "baseline": {"valid": False, "digest": None, "approved_at": None},
            "spec": {"valid": False, "digest": None, "approved_at": None},
            "plan": {"valid": False, "digest": None, "approved_at": None},
            "hotfix": {"valid": False, "digest": None, "approved_at": None},
        },
        "dependency_approvals": [],
        "verification": None,
        "task_progress": [],
        "last_completed": None,
    }


def spec_root(root: Path) -> Path:
    return root / "spec"


def state_path(root: Path) -> Path:
    return spec_root(root) / "state.json"


def load_state(root: Path) -> dict[str, Any]:
    return read_json(state_path(root))


def load_workflow(root: Path) -> dict[str, Any]:
    return read_json(spec_root(root) / "workflow.json")


def active_dir(root: Path, state: dict[str, Any]) -> Path:
    active = state.get("active_change")
    if not active:
        raise FlowError("当前没有活动变更。")
    return spec_root(root) / "changes" / active["slug"]


def digest_files(paths: Iterable[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        if not path.exists():
            raise FlowError(f"批准材料缺失：{path.relative_to(root)}")
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def reject_placeholders(paths: Iterable[Path], root: Path) -> None:
    unresolved = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in PLACEHOLDER_TOKENS):
            unresolved.append(path.relative_to(root).as_posix())
    if unresolved:
        raise FlowError("批准材料仍含占位内容：" + ", ".join(unresolved))


def approval_paths(root: Path, state: dict[str, Any], kind: str) -> list[Path]:
    if kind == "baseline":
        return [spec_root(root) / "baseline" / name for name in BASELINE_DOCS]
    change = active_dir(root, state)
    if kind == "spec":
        return [change / name for name in SPEC_DOCS]
    if kind == "plan":
        return [change / name for name in PLAN_DOCS]
    if kind == "hotfix":
        return [change / "hotfix.md"]
    raise FlowError(f"未知批准类型：{kind}")


def refresh_approvals(root: Path, state: dict[str, Any]) -> bool:
    changed = False
    order = ("baseline", "spec", "plan", "hotfix")
    for kind in order:
        record = state["approvals"].get(kind, {})
        if not record.get("valid"):
            continue
        try:
            current = digest_files(approval_paths(root, state, kind), root)
        except FlowError:
            current = None
        if current != record.get("digest"):
            record["valid"] = False
            record["invalidated_at"] = now_iso()
            changed = True
            if kind in {"baseline", "spec"} and state["approvals"]["plan"].get("valid"):
                state["approvals"]["plan"]["valid"] = False
                state["approvals"]["plan"]["invalidated_at"] = now_iso()
    return changed


def project_fingerprint(root: Path) -> str:
    if not is_git_repo(root):
        raise FlowError("项目尚未初始化 Git。")
    tracked = git(root, "ls-files", "-co", "--exclude-standard", "-z", check=True).stdout
    paths = sorted({part for part in tracked.split("\0") if part})
    ignored = {"spec/state.json", "spec/status.md"}
    digest = hashlib.sha256()
    for relative in paths:
        normalized = relative.replace("\\", "/")
        if normalized in ignored or is_secret_path(normalized):
            continue
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def verification_current(root: Path, state: dict[str, Any]) -> bool:
    verification = state.get("verification")
    return bool(
        verification
        and verification.get("passed")
        and verification.get("fingerprint") == project_fingerprint(root)
    )


def status_markdown(root: Path, state: dict[str, Any]) -> str:
    active = state.get("active_change")
    approvals = state.get("approvals", {})
    lines = [
        "# Wu5 Dev Flow 状态",
        "",
        f"- 阶段：`{state.get('phase')}`",
        f"- 项目类型：`{state.get('project_kind')}`",
        f"- 当前分支：`{current_branch(root) if is_git_repo(root) else 'no-git'}`",
        f"- 活动变更：`{active['slug'] if active else 'none'}`",
        f"- 变更模式：`{active['mode'] if active else 'none'}`",
        "",
        "## 批准",
        "",
    ]
    for kind in ("baseline", "spec", "plan", "hotfix"):
        record = approvals.get(kind, {})
        lines.append(f"- {kind}: {'有效' if record.get('valid') else '无效/未批准'}")
    verification = state.get("verification")
    lines.extend(["", "## 验证", ""])
    if verification:
        lines.append(f"- 结果：{'通过' if verification.get('passed') else '失败'}")
        lines.append(f"- 时间：`{verification.get('verified_at')}`")
        lines.append(f"- 范围：`{verification.get('scope')}`")
    else:
        lines.append("- 尚无验证记录")
    lines.extend(["", "本文件由 `wu5_flow.py` 同步；请勿手工修改。", ""])
    return "\n".join(lines)


def save_state(root: Path, state: dict[str, Any]) -> None:
    write_json(state_path(root), state)
    write_text(spec_root(root) / "status.md", status_markdown(root, state))


def agents_block() -> str:
    script = Path(__file__).resolve().as_posix()
    return (
        f"{AGENTS_START}\n"
        "## Wu5 Dev Flow\n\n"
        "在任何开发、修复、重构、测试、依赖或 Git 操作前，先读取 `spec/index.md` 与 `spec/status.md`，并运行：\n\n"
        f"`python \"{script}\" status`\n\n"
        "遵守 `spec/state.json` 的阶段和批准状态。没有新鲜验证证据不得提交或宣称完成；push、PR 和 merge 必须分别获得用户明确授权。\n"
        f"{AGENTS_END}"
    )


def ensure_agents(root: Path) -> None:
    path = root / "AGENTS.md"
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    block = agents_block()
    pattern = re.compile(re.escape(AGENTS_START) + r".*?" + re.escape(AGENTS_END), re.S)
    if pattern.search(existing):
        updated = pattern.sub(block, existing)
    else:
        updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + block + "\n"
    if updated != existing:
        write_text(path, updated)


def write_baseline(root: Path, files: list[Path]) -> None:
    baseline = spec_root(root) / "baseline"
    rels = [path.relative_to(root).as_posix() for path in files]
    sources = [rel for rel in rels if Path(rel).suffix.lower() in SOURCE_SUFFIXES]
    manifests = [rel for rel in rels if Path(rel).name in MANIFESTS]
    tests = [rel for rel in rels if "tests" in {part.lower() for part in Path(rel).parts} or Path(rel).name.startswith("test_")]
    entries = [rel for rel in sources if Path(rel).name in {"__main__.py", "main.py", "app.py", "cli.py", "manage.py"}]
    large = [
        path.relative_to(root).as_posix() for path in files
        if path.stat().st_size > 200_000
    ]
    modules = "\n".join(f"- `{rel}`" for rel in sources) or "- 未检测到源码文件"
    write_text(baseline / "system-map.md", "# 系统结构基线\n\n## 清单\n\n" + modules + "\n\n## 入口\n\n" + ("\n".join(f"- `{rel}`" for rel in entries) or "- 待 AI 深入确认") + "\n\n## 模块关系与数据流\n\n<!-- AI 完整扫描后补充。 -->\n")
    write_text(baseline / "behavior-map.md", "# 当前行为基线\n\n记录公开接口、输入输出、副作用和已知异常。首次接入只描述现状，不修复行为。\n\n<!-- AI 完整扫描后补充。 -->\n")
    write_text(baseline / "test-map.md", "# 测试基线\n\n## 现有测试\n\n" + ("\n".join(f"- `{rel}`" for rel in tests) or "- 未检测到测试") + "\n\n## 测试缺口\n\n<!-- AI 按稳定边界补充，不在首次接入时创建测试。 -->\n")
    write_text(baseline / "risks.md", "# 风险基线\n\n## 大文件或高复杂度候选\n\n" + ("\n".join(f"- `{rel}`" for rel in large) or "- 暂无自动识别项") + "\n\n## 安全、兼容与未知项\n\n<!-- AI 完整扫描后补充。 -->\n")
    write_text(baseline / "debt.md", "# 基线债务\n\n## 已有 pytest/pyright 失败\n\n<!-- 记录稳定失败与 flaky 测试；新变更不得扩大。 -->\n\n## 结构与文档债务\n")
    write_text(baseline / "adoption-plan.md", "# 接管计划\n\n1. 审计系统结构、行为、测试与风险基线。\n2. 用户明确说“批准基线”。\n3. 以后重构具体模块时，先建立该模块稳定边界的特征测试。\n4. 技术债与 Bug 分别建立正式变更，不在接管阶段顺手修改。\n\n## 项目清单\n\n" + ("\n".join(f"- `{rel}`" for rel in manifests) or "- 未检测到项目清单") + "\n")


def command_init(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    already = (spec_root(root) / "workflow.json").exists()
    if not is_git_repo(root):
        run(["git", "init"], root, check=True)
    if already:
        ensure_agents(root)
        state = load_state(root)
        refresh_approvals(root, state)
        save_state(root, state)
        print("Wu5 Dev Flow 已初始化；已刷新入口与状态。")
        return

    project_kind = detect_project_kind(root)
    spec = spec_root(root)
    for name in ("baseline", "features", "testing", "changes", "archive"):
        (spec / name).mkdir(parents=True, exist_ok=True)
    replacements = {"PROJECT_KIND": project_kind, "WORKFLOW_VERSION": str(WORKFLOW_VERSION)}
    write_text(spec / "index.md", render_template("index.md.tpl", replacements))
    write_text(spec / "project.md", render_template("project.md.tpl", replacements))
    write_text(spec / "testing" / "index.md", render_template("testing.md.tpl", replacements))
    write_json(spec / "workflow.json", default_workflow(project_kind, root))
    state = initial_state(project_kind)
    save_state(root, state)
    ensure_agents(root)
    if project_kind == "legacy":
        write_baseline(root, safe_project_files(root))
    save_state(root, state)
    print(f"初始化完成：项目类型={project_kind}，阶段={state['phase']}。")


def validate_slug(slug: str) -> None:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise FlowError("change slug 只能使用小写字母、数字和连字符。")


def command_new(root: Path, slug: str, change_type: str, mode: str) -> None:
    validate_slug(slug)
    state = load_state(root)
    refresh_approvals(root, state)
    if state.get("active_change"):
        raise FlowError("已有活动变更；同一仓库一次只能实施一个变更。")
    workflow = load_workflow(root)
    resumable_after_merge = state.get("phase") == "ready-to-push" and protected_branch(root, workflow)
    if state.get("phase") != "ready" and not resumable_after_merge:
        raise FlowError(f"当前阶段 {state.get('phase')} 不允许创建变更。")
    dirty = status_lines(root)
    if dirty:
        raise FlowError("工作区存在未提交改动；请先由用户决定如何处理。")
    branch = current_branch(root)
    protected = workflow.get("protected_branches", ["main", "master"])
    prefix = "fix" if mode == "hotfix" else change_type
    target_branch = f"{prefix}/{slug}"
    if branch in protected:
        git(root, "switch", "-c", target_branch, check=True)
    elif branch != target_branch:
        raise FlowError(f"当前分支为 {branch}；请先回到受保护分支或目标分支 {target_branch}。")

    change = spec_root(root) / "changes" / slug
    if change.exists():
        raise FlowError(f"变更目录已存在：{change}")
    replacements = {"SLUG": slug, "REQ_PREFIX": slug.replace("-", "_").upper()[:24]}
    if mode == "full":
        for name in (*SPEC_DOCS, *PLAN_DOCS, "verification.md"):
            write_text(change / name, render_template(f"full/{name}.tpl", replacements))
        phase = "drafting-spec"
    elif mode == "light":
        write_text(change / "change.md", render_template("light/change.md.tpl", replacements))
        phase = "implementing"
    else:
        write_text(change / "hotfix.md", render_template("hotfix/hotfix.md.tpl", replacements))
        phase = "drafting-hotfix"
    state.update({
        "phase": phase,
        "active_change": {
            "slug": slug,
            "type": change_type,
            "mode": mode,
            "branch": target_branch,
            "created_at": now_iso(),
        },
        "verification": None,
        "task_progress": [],
        "dependency_approvals": [],
    })
    for key in ("spec", "plan", "hotfix"):
        state["approvals"][key] = {"valid": False, "digest": None, "approved_at": None}
    save_state(root, state)
    print(f"已创建 {mode} 变更 {slug}，分支 {target_branch}。")


def command_status(root: Path) -> None:
    if not state_path(root).exists():
        raise FlowError("项目尚未初始化；先运行 init。")
    state = load_state(root)
    refresh_approvals(root, state)
    save_state(root, state)
    print(status_markdown(root, state))


def command_approve(root: Path, kind: str, name: str | None) -> None:
    state = load_state(root)
    refresh_approvals(root, state)
    if kind == "dependency":
        if not state.get("active_change"):
            raise FlowError("依赖批准必须关联活动变更。")
        state["dependency_approvals"].append({"name": name or "current-request", "approved_at": now_iso()})
        save_state(root, state)
        print(f"已记录依赖批准：{name or 'current-request'}。")
        return
    if kind == "baseline" and state.get("project_kind") != "legacy":
        raise FlowError("空项目不需要基线批准。")
    active = state.get("active_change")
    if kind in {"spec", "plan", "hotfix"} and not active:
        raise FlowError("当前没有活动变更。")
    if kind == "spec" and active["mode"] != "full":
        raise FlowError("只有完整变更需要规格批准。")
    if kind == "plan":
        if active["mode"] != "full" or not state["approvals"]["spec"].get("valid"):
            raise FlowError("计划批准前必须存在有效规格批准。")
    if kind == "hotfix" and active["mode"] != "hotfix":
        raise FlowError("当前变更不是紧急修复。")
    paths = approval_paths(root, state, kind)
    reject_placeholders(paths, root)
    digest = digest_files(paths, root)
    state["approvals"][kind] = {
        "valid": True,
        "digest": digest,
        "approved_at": now_iso(),
        "head_before": head_commit(root),
    }
    if kind == "baseline":
        state["phase"] = "ready"
    elif kind == "spec":
        state["phase"] = "drafting-plan"
    else:
        state["phase"] = "implementing"
    save_state(root, state)
    print(f"已记录 {kind} 批准；内容哈希={digest[:12]}。")


def protected_branch(root: Path, workflow: dict[str, Any]) -> bool:
    return current_branch(root) in workflow.get("protected_branches", ["main", "master"])


def migration_paths(paths: Iterable[str]) -> list[str]:
    found = []
    for relative in paths:
        parts = {part.lower() for part in Path(relative).parts}
        if parts & MIGRATION_PARTS:
            found.append(relative)
    return found


def dependency_paths(paths: Iterable[str]) -> list[str]:
    return [relative for relative in paths if Path(relative).name in DEPENDENCY_NAMES]


def milestone_paths(root: Path, state: dict[str, Any]) -> set[str]:
    candidates: list[Path] = [state_path(root), spec_root(root) / "status.md"]
    if state.get("phase") == "baseline-review" or state["approvals"]["baseline"].get("valid"):
        candidates.extend(approval_paths(root, state, "baseline"))
        candidates.extend([spec_root(root) / "index.md", spec_root(root) / "project.md", spec_root(root) / "workflow.json", root / "AGENTS.md"])
    active = state.get("active_change")
    if active and active["mode"] == "full":
        if state["approvals"]["plan"].get("valid"):
            candidates.extend(approval_paths(root, state, "plan"))
        elif state["approvals"]["spec"].get("valid"):
            candidates.extend(approval_paths(root, state, "spec"))
    if active and active["mode"] == "hotfix" and state["approvals"]["hotfix"].get("valid"):
        candidates.extend(approval_paths(root, state, "hotfix"))
    return {path.relative_to(root).as_posix() for path in candidates if path.exists()}


def command_check(root: Path, gate: str) -> None:
    state = load_state(root)
    refresh_approvals(root, state)
    workflow = load_workflow(root)
    active = state.get("active_change")
    if gate == "implement":
        if not active or state.get("phase") != "implementing":
            raise FlowError(f"当前阶段 {state.get('phase')} 不允许实施。")
        if protected_branch(root, workflow):
            raise FlowError("禁止在受保护分支实施。")
        if active["mode"] == "full" and not state["approvals"]["plan"].get("valid"):
            raise FlowError("完整变更需要有效计划批准。")
        if active["mode"] == "hotfix" and not state["approvals"]["hotfix"].get("valid"):
            raise FlowError("紧急修复需要有效批准。")
        dirty = status_lines(root)
        if dirty and active["mode"] != "light":
            raise FlowError("实施前工作区必须干净；先提交已批准的里程碑文档。")
    elif gate == "commit":
        paths = staged_files(root)
        if not paths:
            raise FlowError("没有已暂存文件；先 git add 再检查提交门禁。")
        secrets = [path for path in paths if is_secret_path(path)]
        if secrets:
            raise FlowError("禁止提交敏感文件：" + ", ".join(secrets))
        migrations = migration_paths(paths)
        if migrations:
            raise FlowError("检测到数据迁移路径，本 Skill 拒绝实施：" + ", ".join(migrations))
        dependencies = dependency_paths(paths)
        if dependencies and not state.get("dependency_approvals"):
            raise FlowError("依赖文件有变化，但没有明确的依赖批准。")
        if protected_branch(root, workflow):
            raise FlowError("禁止在受保护分支创建变更提交。")
        if set(paths).issubset(milestone_paths(root, state)):
            print("提交门禁通过：批准里程碑文档。")
            save_state(root, state)
            return
        if not verification_current(root, state):
            raise FlowError("缺少与当前内容匹配的新鲜验证证据。")
    elif gate == "push":
        if protected_branch(root, workflow):
            raise FlowError("禁止直接 push 受保护分支。")
        if state.get("phase") != "ready-to-push":
            raise FlowError("变更尚未归档，不能准备 push。")
    elif gate == "archive":
        ensure_archive_ready(root, state)
    else:
        raise FlowError(f"未知门禁：{gate}")
    save_state(root, state)
    print(f"{gate} 门禁通过。")


def verification_document(root: Path, state: dict[str, Any]) -> Path:
    change = active_dir(root, state)
    mode = state["active_change"]["mode"]
    return change / ({"full": "verification.md", "light": "change.md", "hotfix": "hotfix.md"}[mode])


def command_verify(root: Path, scope: str) -> None:
    state = load_state(root)
    refresh_approvals(root, state)
    if state.get("phase") not in {"implementing", "verifying", "ready-to-archive"}:
        raise FlowError(f"当前阶段 {state.get('phase')} 不允许验证。")
    workflow = load_workflow(root)
    results = []
    all_required_passed = True
    for item in workflow.get("quality_commands", []):
        if not item.get("enabled", True):
            continue
        command = item.get("command")
        if not isinstance(command, list) or not command or not all(isinstance(part, str) for part in command):
            raise FlowError(f"质量命令格式无效：{item.get('name')}")
        try:
            result = run(command, root)
            exit_code = result.returncode
            output = ((result.stdout or "") + (result.stderr or "")).strip()
        except FlowError as exc:
            exit_code = 127
            output = str(exc)
        passed = exit_code == 0
        if item.get("required", False) and not passed:
            all_required_passed = False
        results.append({
            "name": item.get("name"),
            "command": [redact_output(part) for part in command],
            "exit_code": exit_code,
            "passed": passed,
            "summary": redact_output(output[-1200:]) if output else "(no output)",
        })
    report_lines = ["", f"### 自动验证 {now_iso()}", "", f"- 范围：`{scope}`"]
    for result in results:
        report_lines.append(f"- `{result['name']}`：exit `{result['exit_code']}`，{'通过' if result['passed'] else '失败'}")
    evidence = verification_document(root, state)
    with evidence.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(report_lines) + "\n")
    fingerprint = project_fingerprint(root)
    state["verification"] = {
        "scope": scope,
        "passed": all_required_passed,
        "verified_at": now_iso(),
        "fingerprint": fingerprint,
        "head": head_commit(root),
        "results": results,
    }
    state["phase"] = "ready-to-archive" if all_required_passed else "verifying"
    save_state(root, state)
    print("验证通过。" if all_required_passed else "验证失败；查看 spec/status.md 与验证文档。")
    if not all_required_passed:
        raise SystemExit(1)


def ensure_archive_ready(root: Path, state: dict[str, Any]) -> None:
    active = state.get("active_change")
    if not active or state.get("phase") != "ready-to-archive":
        raise FlowError("当前变更尚未达到归档阶段。")
    if not verification_current(root, state):
        raise FlowError("验证证据与当前内容不匹配。")
    evidence = verification_document(root, state).read_text(encoding="utf-8")
    enforce_hardcode_gate = load_workflow(root).get("workflow_version", 1) >= 2
    if active["mode"] == "full":
        if "- [x] 规格符合性审查" not in evidence or "- [x] 代码质量审查" not in evidence:
            raise FlowError("完整变更必须完成规格符合性与代码质量两轮审查。")
        if enforce_hardcode_gate and "- [x] 未引入不当 hardcode" not in evidence:
            raise FlowError("尚未完成禁止 hardcode 审查。")
        if active["type"] in {"feature", "fix", "refactor"} and not any((spec_root(root) / "features").rglob("*.md")):
            raise FlowError("归档前必须更新 spec/features/ 的当前有效规格。")
    elif active["mode"] == "light":
        if "- [x] 已确认没有行为、接口、依赖或跨模块变化" not in evidence:
            raise FlowError("轻量变更尚未确认无行为变化。")
        if enforce_hardcode_gate and "- [x] 未引入不当 hardcode" not in evidence:
            raise FlowError("尚未完成禁止 hardcode 审查。")
    elif active["mode"] == "hotfix":
        required = ("- [x] 已先观察复现测试失败", "- [x] 已补齐当前规格", "- [x] 已记录复盘")
        if any(item not in evidence for item in required):
            raise FlowError("紧急修复尚未完成失败测试、补档或复盘。")
        if enforce_hardcode_gate and "- [x] 未引入不当 hardcode" not in evidence:
            raise FlowError("尚未完成禁止 hardcode 审查。")
    changed = git(root, "diff", "--name-only", "HEAD").stdout.splitlines()
    migrations = migration_paths(changed)
    if migrations:
        raise FlowError("检测到数据迁移路径，本 Skill 拒绝归档：" + ", ".join(migrations))


def update_archive_index(root: Path, destination: Path) -> None:
    index = spec_root(root) / "index.md"
    text = index.read_text(encoding="utf-8")
    marker = "\n## 最近归档\n"
    entry = f"\n- [{destination.name}](archive/{destination.name}/)\n"
    if marker not in text:
        text = text.rstrip() + marker + entry
    else:
        text = text.rstrip() + entry
    write_text(index, text)


def command_archive(root: Path, slug: str) -> None:
    state = load_state(root)
    refresh_approvals(root, state)
    active = state.get("active_change")
    if not active or active["slug"] != slug:
        raise FlowError("归档 slug 与当前活动变更不匹配。")
    ensure_archive_ready(root, state)
    source = active_dir(root, state)
    destination = spec_root(root) / "archive" / f"{datetime.now().date().isoformat()}-{slug}"
    if destination.exists():
        raise FlowError(f"归档目录已存在：{destination}")
    snapshot = json.loads(json.dumps(state))
    write_json(source / "state.json", snapshot)
    write_text(source / "status.md", status_markdown(root, state))
    shutil.move(str(source), str(destination))
    update_archive_index(root, destination)
    state["last_completed"] = {
        "slug": slug,
        "archived_at": now_iso(),
        "archive": destination.relative_to(root).as_posix(),
        "verification": state.get("verification"),
    }
    state["active_change"] = None
    state["phase"] = "ready-to-push"
    state["verification"] = None
    state["task_progress"] = []
    save_state(root, state)
    print(f"已归档到 {destination.relative_to(root)}。")


def command_doctor(root: Path) -> None:
    problems = []
    if not is_git_repo(root):
        problems.append("不是 Git 仓库")
    if not (spec_root(root) / "workflow.json").exists():
        problems.append("尚未初始化 spec/workflow.json")
    else:
        workflow = load_workflow(root)
        if workflow.get("workflow_version") != WORKFLOW_VERSION:
            problems.append(f"流程版本为 {workflow.get('workflow_version')}，当前 Skill 为 {WORKFLOW_VERSION}；需人工批准迁移")
        for item in workflow.get("quality_commands", []):
            if not item.get("enabled", True):
                continue
            command = item.get("command", [])
            if command and shutil.which(command[0]) is None:
                problems.append(f"缺少命令：{command[0]} ({item.get('name')})")
    agents = root / "AGENTS.md"
    if not agents.exists() or AGENTS_START not in agents.read_text(encoding="utf-8", errors="replace"):
        problems.append("AGENTS.md 缺少 Wu5 持久入口")
    if problems:
        print("Doctor 发现问题：")
        for problem in problems:
            print(f"- {problem}")
        raise SystemExit(1)
    print("Doctor 通过：Git、流程文件、入口和质量命令均就绪。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wu5 SDD/TDD/Git workflow gates")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="项目根目录，默认当前目录")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    new = sub.add_parser("new")
    new.add_argument("slug")
    new.add_argument("--type", choices=("feature", "fix", "refactor", "docs", "chore"), required=True)
    new.add_argument("--mode", choices=("full", "light", "hotfix"), required=True)
    sub.add_parser("status")
    approve = sub.add_parser("approve")
    approve.add_argument("kind", choices=("baseline", "spec", "plan", "dependency", "hotfix"))
    approve.add_argument("--name")
    check = sub.add_parser("check")
    check.add_argument("gate", choices=("implement", "commit", "push", "archive"))
    verify = sub.add_parser("verify")
    verify.add_argument("scope", choices=("targeted", "affected", "full"))
    archive = sub.add_parser("archive")
    archive.add_argument("slug")
    sub.add_parser("doctor")
    return parser


def configure_stdio() -> None:
    """Keep Chinese diagnostics deterministic across Windows code pages."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "init":
            command_init(root)
        elif args.command == "new":
            command_new(root, args.slug, args.type, args.mode)
        elif args.command == "status":
            command_status(root)
        elif args.command == "approve":
            command_approve(root, args.kind, args.name)
        elif args.command == "check":
            command_check(root, args.gate)
        elif args.command == "verify":
            command_verify(root, args.scope)
        elif args.command == "archive":
            command_archive(root, args.slug)
        elif args.command == "doctor":
            command_doctor(root)
    except FlowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
