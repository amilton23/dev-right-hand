from pathlib import Path

from dev_right_hand.config import AppConfig
from dev_right_hand.orchestrator import MultiAgentOrchestrator


def test_orchestrator_builds_context_and_reports(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    tests_dir = tmp_path / "tests"
    src_dir.mkdir()
    tests_dir.mkdir()

    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")
    (src_dir / "train_model.py").write_text("print('train')\n", encoding="utf-8")
    (tests_dir / "test_train_model.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    orchestrator = MultiAgentOrchestrator(config=AppConfig(repository_root=tmp_path))
    report = orchestrator.analyze()

    assert report.repository_root == tmp_path
    assert len(report.agent_reports) == 5
    assert report.run_id
    assert any(agent_report.agent_name == "MLValidationAgent" for agent_report in report.agent_reports)
