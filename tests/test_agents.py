from pathlib import Path

from dev_right_hand.agents.code_review import CodeReviewAgent
from dev_right_hand.contracts import FindingCategory, RepositoryContext


def test_code_review_agent_flags_missing_tests(tmp_path: Path) -> None:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    module_path = app_dir / "service.py"
    module_path.write_text("def run():\n    return 'ok'\n", encoding="utf-8")

    context = RepositoryContext(
        repository_root=tmp_path,
        python_files=[module_path],
        test_files=[],
        config_files=[],
        model_files=[],
    )
    report = CodeReviewAgent().run(context)

    assert any(finding.category == FindingCategory.CODE_QUALITY for finding in report.findings)
    assert any(finding.title == "Tests are missing" for finding in report.findings)
