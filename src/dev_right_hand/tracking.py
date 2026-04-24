from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import structlog

from dev_right_hand.contracts import ExecutionEvent


logger = structlog.get_logger(__name__)


class ExecutionTracker:
    """Simple in-memory tracker ready to be swapped by an external backend."""

    def __init__(self) -> None:
        self.run_id = uuid4().hex
        self.started_at = datetime.utcnow()
        self._events: list[ExecutionEvent] = []

    @property
    def events(self) -> list[ExecutionEvent]:
        return list(self._events)

    def record(self, agent_name: str, status: str, **details: object) -> None:
        event = ExecutionEvent(
            run_id=self.run_id,
            agent_name=agent_name,
            status=status,
            details=dict(details),
        )
        self._events.append(event)
        logger.info(
            "agent_event",
            run_id=event.run_id,
            agent_name=agent_name,
            status=status,
            details=event.details,
        )
