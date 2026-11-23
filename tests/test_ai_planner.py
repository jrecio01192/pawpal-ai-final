"""AI planner retrieval, policy, fallback, and fake-model integration tests."""
import json
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from ai_planner import generate_daily_plan, owner_record_signature
from pawpal_system import Owner, Scheduler
from task_management import create_care_task

NOW = datetime(2026, 11, 22, 12)
DAY = NOW.date()


@pytest.fixture
def owner():
    owner = Owner("Jordan")
    owner.add_pet("Mochi", "Cat")
    owner.add_pet("Biscuit", "Dog")
    return owner


class FakeClient:
    def __init__(self, get_payload=None, fail=False):
        self.get_payload = get_payload
        self.fail = fail
        self.called = False
        self.responses = self
        self.request_kwargs = None

    def create(self, **kwargs):
        self.called = True
        self.request_kwargs = kwargs
        if self.fail:
            raise ConnectionError("model unavailable")
        payload = self.get_payload(kwargs)
        return SimpleNamespace(output_text=json.dumps(payload))


def make_payload(kwargs):
    records = json.loads(kwargs["input"])
    return {
        "summary": "Check the overdue task and review scheduling overlaps.",
        "recommendations": [
            {
                "task_id": t["task_id"],
                "priority": "high" if t["overdue"] else "medium" if t["same_time_conflict"] else "low",
                "reason": "Review the scheduled care task using the existing records.",
            } for t in records["pending_tasks"]
        ],
    }


def test_no_tasks_safe_empty_plan(owner):
    plan = generate_daily_plan(owner, DAY, now=NOW)
    assert plan.mode == "Rules-only preview"
    assert plan.items == ()


def test_only_pending_target_day_and_overdue_are_retrieved(owner):
    past = create_care_task(owner, "Mochi", "Breakfast", NOW - timedelta(hours=3))
    today = create_care_task(owner, "Mochi", "Dinner", NOW + timedelta(hours=3))
    next_day = create_care_task(owner, "Mochi", "Tomorrow", NOW + timedelta(days=1))
    done = create_care_task(owner, "Biscuit", "Completed", NOW - timedelta(hours=1))
    Scheduler(owner).complete_task(done.id)
    plan = generate_daily_plan(owner, DAY, now=NOW)
    assert {i.task_id for i in plan.items} == {past.id, today.id}
    assert next_day.id not in {i.task_id for i in plan.items}


def test_overdue_priority_cannot_be_low(owner):
    create_care_task(owner, "Mochi", "Feeding", NOW - timedelta(hours=1))
    plan = generate_daily_plan(owner, DAY, now=NOW)
    assert plan.items[0].priority == "High"
    assert "check whether" in plan.items[0].reason.lower()


def test_conflicts_are_flagged(owner):
    create_care_task(owner, "Mochi", "Grooming", NOW + timedelta(hours=1))
    create_care_task(owner, "Biscuit", "Walk", NOW + timedelta(hours=1))
    plan = generate_daily_plan(owner, DAY, now=NOW)
    assert all(item.conflict and item.priority == "Medium" for item in plan.items)


def test_ai_requests_use_actual_tasks_with_schema(owner):
    task = create_care_task(owner, "Mochi", "Breakfast", NOW - timedelta(hours=1))
    client = FakeClient(make_payload)
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=client)
    assert plan.mode == "AI"
    assert plan.items[0].task_id == task.id
    assert client.called
    assert client.request_kwargs["store"] is False
    assert client.request_kwargs["text"]["format"]["type"] == "json_schema"
    assert json.loads(client.request_kwargs["input"])["pending_tasks"][0]["description"] == "Breakfast"


def test_model_cannot_hallucinate_task_ids(owner):
    create_care_task(owner, "Mochi", "Breakfast", NOW)
    client = FakeClient(lambda kw: {"summary": "x", "recommendations": [
        {"task_id": "fabricated", "priority": "high", "reason": "Fake task"}
    ]})
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=client)
    assert plan.mode == "Rules-only preview"
    assert plan.warning


def test_model_cannot_omit_tasks(owner):
    create_care_task(owner, "Mochi", "Breakfast", NOW)
    client = FakeClient(lambda kw: {"summary": "x", "recommendations": []})
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=client)
    assert plan.mode == "Rules-only preview"


def test_model_cannot_downgrade_overdue_task(owner):
    task = create_care_task(owner, "Mochi", "Breakfast", NOW - timedelta(hours=1))
    client = FakeClient(lambda kw: {"summary": "x", "recommendations": [
        {"task_id": task.id, "priority": "low", "reason": "Not urgent"}
    ]})
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=client)
    assert plan.mode == "Rules-only preview"
    assert plan.items[0].priority == "High"


def test_model_cannot_downgrade_conflicting_task(owner):
    a = create_care_task(owner, "Mochi", "Grooming", NOW + timedelta(hours=1))
    b = create_care_task(owner, "Biscuit", "Walk", NOW + timedelta(hours=1))
    client = FakeClient(lambda kw: {"summary": "x", "recommendations": [
        {"task_id": a.id, "priority": "low", "reason": "No urgency"},
        {"task_id": b.id, "priority": "low", "reason": "No urgency"},
    ]})
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=client)
    assert plan.mode == "Rules-only preview"
    assert all(item.priority == "Medium" for item in plan.items)


def test_duplicate_model_id_rejected(owner):
    task = create_care_task(owner, "Mochi", "Breakfast", NOW)
    create_care_task(owner, "Biscuit", "Walk", NOW + timedelta(hours=1))
    client = FakeClient(lambda kw: {"summary": "x", "recommendations": [
        {"task_id": task.id, "priority": "low", "reason": "Routine"},
        {"task_id": task.id, "priority": "low", "reason": "Routine"},
    ]})
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=client)
    assert plan.mode == "Rules-only preview"


def test_model_failure_falls_back_without_changing_tasks(owner):
    task = create_care_task(owner, "Mochi", "Breakfast", NOW)
    plan = generate_daily_plan(owner, DAY, now=NOW, use_ai=True, client=FakeClient(fail=True))
    assert plan.warning
    assert not task.completed
    assert task.time == NOW


def test_missing_api_key_is_error_in_ai_mode(owner):
    create_care_task(owner, "Mochi", "Breakfast", NOW)
    with pytest.raises(ValueError, match="API key"):
        generate_daily_plan(owner, DAY, now=NOW, use_ai=True)


def test_past_and_upcoming_vet_visits(owner):
    pet = owner.get_pet("Mochi")
    pet.add_vet_visit(DAY - timedelta(days=1), "Old Clinic", "")
    pet.add_vet_visit(DAY + timedelta(days=2), "New Clinic", "")
    plan = generate_daily_plan(owner, DAY, now=NOW)
    assert len(plan.upcoming_visits) == 1
    assert "New Clinic" in plan.upcoming_visits[0]


def test_snapshot_signature_changes_when_task_updated(owner):
    a = owner_record_signature(owner)
    task = create_care_task(owner, "Mochi", "Breakfast", NOW)
    b = owner_record_signature(owner)
    assert a != b
    Scheduler(owner).complete_task(task.id)
    assert b != owner_record_signature(owner)


def test_invalid_day_type_rejected(owner):
    with pytest.raises(TypeError, match="date"):
        generate_daily_plan(owner, "2026-11-22", now=NOW)
