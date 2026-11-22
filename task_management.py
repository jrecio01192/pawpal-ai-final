"""Task-management helpers used by the PawPal+ Streamlit interface.

The AI planner can later reuse these helpers to examine real scheduled tasks.
"""

from datetime import datetime

from pawpal_system import Owner, Task


ALLOWED_FREQUENCIES = ("once", "daily", "weekly")


def create_care_task(
    owner: Owner,
    pet_name: str,
    description: str,
    scheduled_time: datetime,
    frequency: str = "once",
) -> Task:
    """Create a task, rejecting unsupported frequencies and exact duplicates.

    A duplicate is an unfinished task for the same pet with the same description,
    date/time, and recurrence frequency. Other tasks may share the same time;
    the Scheduler handles those as scheduling conflicts rather than errors.
    """
    normalized_frequency = frequency.strip().casefold()
    if normalized_frequency not in ALLOWED_FREQUENCIES:
        raise ValueError("Frequency must be once, daily, or weekly.")

    pet = owner.get_pet(pet_name)
    candidate = Task(description=description, time=scheduled_time, frequency=normalized_frequency)

    for existing in pet.tasks:
        if (
            not existing.completed
            and existing.description.casefold() == candidate.description.casefold()
            and existing.time == candidate.time
            and existing.frequency.casefold() == candidate.frequency
        ):
            raise ValueError("This pet already has an unfinished matching task at that time.")

    return pet.add_task(candidate)


def task_status(task: Task, now: datetime) -> str:
    """Return a consistent status label for the current task occurrence."""
    if task.completed:
        return "Completed"
    if task.time < now:
        return "Overdue"
    return "Upcoming"
