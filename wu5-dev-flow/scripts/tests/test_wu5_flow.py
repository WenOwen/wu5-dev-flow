from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "wu5_flow.py"


class FlowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def cli(self, *args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if ok and result.returncode != 0:
            self.fail(f"CLI failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}")
        return result

    def git(self, *args: str, ok: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["git", *args], cwd=self.root, text=True, encoding="utf-8", errors="replace", capture_output=True
        )
        if ok and result.returncode != 0:
            self.fail(f"git failed: {args}\nstdout={result.stdout}\nstderr={result.stderr}")
        return result

    def configure_git(self) -> None:
        self.git("config", "user.name", "Wu5 Test")
        self.git("config", "user.email", "wu5@example.invalid")

    def commit_all(self, message: str = "chore: 初始化") -> None:
        self.git("add", "-A")
        self.git("commit", "-m", message)

    def init_empty(self) -> None:
        self.cli("init")
        self.configure_git()

    def set_fake_quality(self, pass_checks: bool = True) -> None:
        path = self.root / "spec" / "workflow.json"
        workflow = json.loads(path.read_text(encoding="utf-8"))
        code = "raise SystemExit(0)" if pass_checks else "raise SystemExit(1)"
        workflow["quality_commands"] = [
            {"name": "fake", "command": [sys.executable, "-c", code], "required": True, "enabled": True}
        ]
        path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def read_state(self) -> dict:
        return json.loads((self.root / "spec" / "state.json").read_text(encoding="utf-8"))

    def resolve_placeholders(self, *names: str, slug: str = "add-login") -> None:
        change = self.root / "spec" / "changes" / slug
        for name in names:
            path = change / name
            text = path.read_text(encoding="utf-8").replace("待定义", "已定义").replace("待填写", "已填写")
            path.write_text(text, encoding="utf-8")

    def test_empty_init_is_idempotent_and_preserves_agents(self) -> None:
        (self.root / "AGENTS.md").write_text("# Existing\n", encoding="utf-8")
        self.cli("init")
        self.cli("init")
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# Existing", agents)
        self.assertEqual(agents.count("<!-- wu5-dev-flow:start -->"), 1)
        self.assertEqual(self.read_state()["project_kind"], "empty")

    def test_legacy_scan_excludes_secret_files(self) -> None:
        (self.root / "app.py").write_text("print('ok')\n", encoding="utf-8")
        (self.root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
        self.cli("init")
        self.assertEqual(self.read_state()["phase"], "baseline-review")
        baseline = "\n".join(path.read_text(encoding="utf-8") for path in (self.root / "spec" / "baseline").glob("*.md"))
        self.assertIn("app.py", baseline)
        self.assertNotIn(".env", baseline)
        self.assertNotIn("secret", baseline)

    def test_legacy_baseline_requires_completed_scan(self) -> None:
        (self.root / "app.py").write_text("print('ok')\n", encoding="utf-8")
        self.cli("init")
        self.configure_git()
        rejected = self.cli("approve", "baseline", ok=False)
        self.assertIn("占位内容", rejected.stderr)
        for path in (self.root / "spec" / "baseline").glob("*.md"):
            text = path.read_text(encoding="utf-8").replace("<!-- AI 完整扫描后补充。 -->", "扫描结论：已由测试补全。")
            path.write_text(text, encoding="utf-8")
        self.cli("approve", "baseline")
        self.assertEqual(self.read_state()["phase"], "ready")

    def test_dirty_tree_blocks_new_change(self) -> None:
        self.init_empty()
        result = self.cli("new", "add-login", "--type", "feature", "--mode", "full", ok=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("未提交改动", result.stderr)

    def test_approval_hash_change_invalidates_spec_and_plan(self) -> None:
        self.init_empty()
        self.commit_all()
        self.cli("new", "add-login", "--type", "feature", "--mode", "full")
        self.resolve_placeholders("proposal.md", "spec.md", "design.md")
        self.cli("approve", "spec")
        self.commit_all("docs(spec): 批准规格")
        self.resolve_placeholders("plan.md", "test-plan.md")
        self.cli("approve", "plan")
        self.commit_all("docs(plan): 批准计划")
        spec = self.root / "spec" / "changes" / "add-login" / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
        self.cli("status")
        state = self.read_state()
        self.assertFalse(state["approvals"]["spec"]["valid"])
        self.assertFalse(state["approvals"]["plan"]["valid"])

    def test_full_workflow_reaches_archive(self) -> None:
        self.init_empty()
        self.set_fake_quality()
        self.commit_all()
        self.cli("new", "add-login", "--type", "feature", "--mode", "full")
        rejected = self.cli("approve", "spec", ok=False)
        self.assertIn("占位内容", rejected.stderr)
        self.resolve_placeholders("proposal.md", "spec.md", "design.md")
        self.cli("approve", "spec")
        self.commit_all("docs(spec): 批准规格")
        self.resolve_placeholders("plan.md", "test-plan.md")
        self.cli("approve", "plan")
        self.commit_all("docs(plan): 批准计划")
        self.cli("check", "implement")

        (self.root / "app.py").write_text("def login():\n    return True\n", encoding="utf-8")
        feature = self.root / "spec" / "features" / "login.md"
        feature.write_text("# 登录\n\n系统必须支持登录。\n", encoding="utf-8")
        evidence = self.root / "spec" / "changes" / "add-login" / "verification.md"
        text = evidence.read_text(encoding="utf-8").replace("- [ ] 规格符合性审查", "- [x] 规格符合性审查").replace(
            "- [ ] 代码质量审查", "- [x] 代码质量审查"
        ).replace("- [ ] 未引入不当 hardcode", "- [x] 未引入不当 hardcode")
        evidence.write_text(text, encoding="utf-8")
        self.cli("verify", "full")
        self.git("add", "-A")
        self.cli("check", "commit")
        self.commit_all("feat(auth): 增加登录")
        self.cli("check", "archive")
        self.cli("archive", "add-login")
        self.assertEqual(self.read_state()["phase"], "ready-to-push")

    def test_protected_branch_blocks_implementation(self) -> None:
        self.init_empty()
        self.commit_all()
        self.cli("new", "docs-cleanup", "--type", "docs", "--mode", "light")
        self.commit_all("docs: 创建轻量变更")
        default_branch = self.git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        # The previous command reports the feature branch; discover the protected branch from its parent.
        protected = json.loads((self.root / "spec" / "workflow.json").read_text(encoding="utf-8"))["protected_branches"]
        target = next(name for name in protected if self.git("show-ref", "--verify", f"refs/heads/{name}", ok=False).returncode == 0)
        self.git("switch", target)
        state_path = self.root / "spec" / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["active_change"] = {"slug": "docs-cleanup", "mode": "light", "type": "docs", "branch": default_branch}
        state["phase"] = "implementing"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        result = self.cli("check", "implement", ok=False)
        self.assertIn("受保护分支", result.stderr)

    def test_verification_fingerprint_and_light_archive(self) -> None:
        self.init_empty()
        self.set_fake_quality()
        self.commit_all()
        self.cli("new", "docs-cleanup", "--type", "docs", "--mode", "light")
        change = self.root / "spec" / "changes" / "docs-cleanup" / "change.md"
        text = change.read_text(encoding="utf-8").replace(
            "- [ ] 已确认没有行为、接口、依赖或跨模块变化",
            "- [x] 已确认没有行为、接口、依赖或跨模块变化",
        ).replace("- [ ] 未引入不当 hardcode", "- [x] 未引入不当 hardcode").replace(
            "- [ ] 已运行适用的验证", "- [x] 已运行适用的验证"
        )
        change.write_text(text, encoding="utf-8")
        self.cli("verify", "full")
        self.git("add", "-A")
        self.cli("check", "commit")
        self.commit_all("docs: 完成轻量变更")
        # Commit changes the repository metadata but not the content fingerprint.
        self.cli("archive", "docs-cleanup")
        self.assertEqual(self.read_state()["phase"], "ready-to-push")
        self.assertTrue(any((self.root / "spec" / "archive").iterdir()))

    def test_archive_requires_hardcode_review(self) -> None:
        self.init_empty()
        self.set_fake_quality()
        self.commit_all()
        self.cli("new", "docs-cleanup", "--type", "docs", "--mode", "light")
        change = self.root / "spec" / "changes" / "docs-cleanup" / "change.md"
        text = change.read_text(encoding="utf-8").replace(
            "- [ ] 已确认没有行为、接口、依赖或跨模块变化",
            "- [x] 已确认没有行为、接口、依赖或跨模块变化",
        )
        change.write_text(text, encoding="utf-8")
        self.cli("verify", "full")
        result = self.cli("archive", "docs-cleanup", ok=False)
        self.assertIn("hardcode", result.stderr)

    def test_dependency_and_migration_gates(self) -> None:
        self.init_empty()
        self.set_fake_quality()
        self.commit_all()
        self.cli("new", "deps-update", "--type", "chore", "--mode", "light")
        (self.root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
        self.cli("verify", "full")
        self.git("add", "-A")
        result = self.cli("check", "commit", ok=False)
        self.assertIn("依赖批准", result.stderr)
        self.cli("approve", "dependency", "--name", "example")
        self.cli("check", "commit")
        self.git("reset")
        migration = self.root / "migrations" / "001.sql"
        migration.parent.mkdir()
        migration.write_text("ALTER TABLE demo ADD x INT;\n", encoding="utf-8")
        self.git("add", "-A")
        result = self.cli("check", "commit", ok=False)
        self.assertIn("数据迁移", result.stderr)

    def test_failed_verification_returns_nonzero(self) -> None:
        self.init_empty()
        self.set_fake_quality(pass_checks=False)
        self.commit_all()
        self.cli("new", "docs-cleanup", "--type", "docs", "--mode", "light")
        result = self.cli("verify", "full", ok=False)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.read_state()["verification"]["passed"])

    def test_new_process_recovers_active_change_from_files(self) -> None:
        self.init_empty()
        self.commit_all()
        self.cli("new", "resume-work", "--type", "feature", "--mode", "full")
        result = self.cli("status")
        self.assertIn("resume-work", result.stdout)
        self.assertIn("drafting-spec", result.stdout)
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("spec/index.md", agents)
        self.assertIn("wu5_flow.py", agents)

    def test_verification_redacts_secret_like_output(self) -> None:
        self.init_empty()
        workflow_path = self.root / "spec" / "workflow.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        workflow["quality_commands"] = [{
            "name": "safe-output",
            "command": [sys.executable, "-c", "print('TOKEN=super-secret-value')"],
            "required": True,
            "enabled": True,
        }]
        workflow_path.write_text(json.dumps(workflow, ensure_ascii=False, indent=2), encoding="utf-8")
        self.commit_all()
        self.cli("new", "redact-log", "--type", "docs", "--mode", "light")
        self.cli("verify", "full")
        serialized = json.dumps(self.read_state(), ensure_ascii=False)
        self.assertNotIn("super-secret-value", serialized)
        self.assertIn("[REDACTED]", serialized)


if __name__ == "__main__":
    unittest.main()
