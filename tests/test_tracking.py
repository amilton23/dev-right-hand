from dev_right_hand.tracking import ExecutionTracker


def test_tracker_records_events() -> None:
    tracker = ExecutionTracker()
    tracker.record("CodeReviewAgent", "started", repository="demo")
    tracker.record("CodeReviewAgent", "finished", findings=2)

    assert len(tracker.events) == 2
    assert tracker.events[0].agent_name == "CodeReviewAgent"
    assert tracker.events[1].details["findings"] == 2
