"""Tests for the new Task Management feature (independent of Streamlit)."""

from datetime import date, datetime

import pytest

from pawpal_system import Owner, Scheduler
from task_management import create_care_task, task_status


@pytest.fixture
def owner():
    person = Owner("Jordan")
    person.add_pet("Mochi", "Cat")
    return person


def test_add_task_through_helper_assigns_pet_and_owner(owner):
    task = create_care_task(owner, "Mochi", "Breakfast", datetime(2026, 11, 22, 8), "DAILY")
    assert task in owner.get_pet("Mochi").tasks
    assert task.frequency == "daily"
    assert (task.pet_name, task.owner_name) == ("Mochi", "Jordan")


def test_blank_task_description_is_rejected(owner):
    with pytest.raises(ValueError, match="description cannot be blank"):
        create_care_task(owner, "Mochi", "   ", datetime(2026, 11, 22, 8))


def test_invalid_frequency_is_rejected(owner):
    with pytest.raises(ValueError, match="Frequency must"):
        create_care_task(owner, "Mochi", "Walk", datetime(2026, 11, 22, 8), "hourly")


def test_duplicate_unfinished_task_is_rejected_case_insensitively(owner):
    create_care_task(owner, "Mochi", "Breakfast", datetime(2026, 11, 22, 8), "daily")
    with pytest.raises(ValueError, match="matching task"):
        create_care_task(owner, "Mochi", "  breakfast ", datetime(2026, 11, 22, 8), "DAILY")


def test_same_time_different_description_is_allowed_and_conflict_detected(owner):
    first = create_care_task(owner, "Mochi", "Breakfast", datetime(2026, 11, 22, 8))
    second = create_care_task(owner, "Mochi", "Medication", datetime(2026, 11, 22, 8))
    assert Scheduler(owner).find_conflicts() == [(first, second)]


def test_completed_task_can_be_created_again(owner):
    first = create_care_task(owner, "Mochi", "Breakfast", datetime(2026, 11, 22, 8))
    Scheduler(owner).complete_task(first.id)
    second = create_care_task(owner, "Mochi", "Breakfast", datetime(2026, 11, 22, 8))
    assert second.id != first.id


def test_unknown_pet_raises_clear_error(owner):
    with pytest.raises(KeyError, match="No pet named"):
        create_care_task(owner, "Unknown", "Walk", datetime(2026, 11, 22, 8))


def test_invalid_time_type_is_rejected(owner):
    with pytest.raises(TypeError, match="datetime"):
        create_care_task(owner, "Mochi", "Breakfast", date(2026, 11, 22))  # type: ignore[arg-type]


def test_task_status_handles_upcoming_overdue_and_completed(owner):
    now = datetime(2026, 11, 22, 12)
    earlier = create_care_task(owner, "Mochi", "Breakfast", datetime(2026, 11, 22, 8))
    later = create_care_task(owner, "Mochi", "Dinner", datetime(2026, 11, 22, 18))
    assert task_status(earlier, now) == "Overdue"
    assert task_status(later, now) == "Upcoming"
    Scheduler(owner).complete_task(earlier.id)
    assert task_status(earlier, now) == "Completed"


def test_recurring_task_completion_creates_new_occurrence(owner):
    task = create_care_task(owner, "Mochi", "Medication", datetime(2026, 11, 22, 8), "daily")
    Scheduler(owner).complete_task(task.id)
    future = [item for item in owner.get_tasks() if not item.completed]
    assert len(future) == 1
    assert future[0].time == datetime(2026, 11, 23, 8)


def test_reopening_and_recompleting_recurring_task_does_not_duplicate(owner):
    task = create_care_task(owner, "Mochi", "Medication", datetime(2026, 11, 22, 8), "daily")
    scheduler = Scheduler(owner)
    scheduler.complete_task(task.id)
    assert len(owner.get_tasks()) == 2
    scheduler.reopen_task(task.id)
    scheduler.complete_task(task.id)
    assert len(owner.get_tasks()) == 2
