from __future__ import annotations

import json
from pathlib import Path

import typer

from dev_right_hand.config import AppConfig
from dev_right_hand.orchestrator import MultiAgentOrchestrator


app = typer.Typer(help="Multi-agent repository analyzer for data and AI teams.")


@app.command()
def scan(path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True)) -> None:
    """Analyze a repository or local folder and print a JSON report."""
    config = AppConfig(repository_root=path.resolve())
    orchestrator = MultiAgentOrchestrator(config=config)
    report = orchestrator.analyze()
    typer.echo(json.dumps(report.model_dump(mode="json"), indent=2, default=str))


if __name__ == "__main__":
    app()
