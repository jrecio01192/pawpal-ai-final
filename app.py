"""PawPal+ Streamlit app: pets, feedings, vet visits, and scheduled tasks."""

from datetime import date, datetime, time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler
from task_management import create_care_task, task_status


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.write("Keep your pets, feeding times, veterinary checkups, and care tasks in one place.")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")

owner: Owner = st.session_state.owner
owner_name = st.sidebar.text_input("Owner name", value=owner.name, key="owner_name_input")
if owner_name.strip():
    owner.rename(owner_name)
else:
    st.sidebar.warning("Owner name cannot be blank; using the previous name.")

pets_tab, feeding_tab, vet_tab, tasks_tab = st.tabs(
    ["Pets", "Feeding", "Vet history", "Tasks"]
)

with pets_tab:
    st.subheader("Your pets")
    st.caption(f"Owner: {owner.name}")

    with st.form("add_pet_form", clear_on_submit=True):
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["Dog", "Cat", "Bird", "Other"])
        add_pet = st.form_submit_button("Add pet")

    if add_pet:
        try:
            pet = owner.add_pet(pet_name, species)
            st.success(f"Added {pet.name}.")
        except ValueError as error:
            st.error(str(error))

    if owner.pets:
        for pet in owner.pets:
            st.markdown(f"**{pet.name}** · {pet.species} · Owner: {pet.owner_name}")
    else:
        st.info("No pets yet. Add your first pet above.")

with feeding_tab:
    st.subheader("Feeding log")
    if not owner.pets:
        st.info("Add a pet before recording a feeding.")
    else:
        with st.form("add_feeding_form", clear_on_submit=True):
            selected_pet: Pet = st.selectbox(
                "Pet", owner.pets, format_func=lambda pet: pet.name
            )
            feeding_date = st.date_input("Date", value=date.today())
            feeding_time = st.time_input(
                "Feeding time", value=datetime.now().time().replace(second=0, microsecond=0)
            )
            food = st.text_input("Food (optional)")
            add_feeding = st.form_submit_button("Record feeding")

        if add_feeding:
            fed_at = datetime.combine(feeding_date, feeding_time)
            selected_pet.add_feeding(fed_at, food)
            st.success(f"Recorded feeding for {selected_pet.name}.")

        feeding_rows = [
            {
                "Date and time": record.fed_at.strftime("%Y-%m-%d %I:%M %p"),
                "Pet": record.pet_name,
                "Owner": record.owner_name,
                "Food": record.food or "—",
            }
            for pet in owner.pets
            for record in pet.feedings
        ]
        if feeding_rows:
            st.dataframe(feeding_rows, hide_index=True, use_container_width=True)
        else:
            st.info("No feedings recorded yet.")

with vet_tab:
    st.subheader("Veterinary checkup history")
    if not owner.pets:
        st.info("Add a pet before recording a vet visit.")
    else:
        with st.form("add_vet_visit_form", clear_on_submit=True):
            selected_pet: Pet = st.selectbox(
                "Pet", owner.pets, format_func=lambda pet: pet.name
            )
            visit_date = st.date_input("Visit date", value=date.today(), key="visit_date")
            veterinarian = st.text_input("Veterinarian or clinic")
            notes = st.text_area("Checkup notes")
            add_visit = st.form_submit_button("Add vet visit")

        if add_visit:
            if not veterinarian.strip():
                st.error("Enter the veterinarian or clinic name.")
            else:
                selected_pet.add_vet_visit(visit_date, veterinarian, notes)
                st.success(f"Added vet visit for {selected_pet.name}.")

        visit_rows = [
            {
                "Date": visit.visit_date.isoformat(),
                "Pet": visit.pet_name,
                "Owner": visit.owner_name,
                "Veterinarian / clinic": visit.veterinarian,
                "Notes": visit.notes or "—",
            }
            for pet in owner.pets
            for visit in pet.vet_visits
        ]
        if visit_rows:
            st.dataframe(visit_rows, hide_index=True, use_container_width=True)
        else:
            st.info("No vet visits recorded yet.")

with tasks_tab:
    st.subheader("Task management")
    st.caption("Schedule care tasks, track what is due, and check for conflicts.")

    if not owner.pets:
        st.info("Add a pet in the Pets tab before creating tasks.")
    else:
        scheduler = Scheduler(owner)

        with st.form("add_task_form", clear_on_submit=False):
            task_pet: Pet = st.selectbox(
                "Pet for this task", owner.pets, format_func=lambda pet: pet.name
            )
            task_description = st.text_input("Task description", placeholder="Morning feeding")
            task_date = st.date_input("Scheduled date", value=date.today())
            task_time = st.time_input(
                "Scheduled time",
                value=time(8, 0),
                key="task_scheduled_time",
                help="Choose a time for the task. Your selection is saved when you click Add task.",
            )
            task_frequency = st.selectbox("Repeat", ["once", "daily", "weekly"])
            add_task = st.form_submit_button("Add task")

        if add_task:
            try:
                new_task = create_care_task(
                    owner=owner,
                    pet_name=task_pet.name,
                    description=task_description,
                    scheduled_time=datetime.combine(task_date, task_time),
                    frequency=task_frequency,
                )
            except (ValueError, KeyError, TypeError) as error:
                st.error(str(error))
            else:
                st.success(
                    f"Scheduled '{new_task.description}' for {new_task.pet_name} "
                    f"on {new_task.time.strftime('%b %d, %Y at %I:%M %p')}."
                )

        st.divider()
        st.subheader("Scheduled tasks")

        now = datetime.now()
        all_tasks = scheduler.get_tasks()
        upcoming_count = sum(not task.completed and task.time >= now for task in all_tasks)
        overdue_count = sum(not task.completed and task.time < now for task in all_tasks)
        completed_count = sum(task.completed for task in all_tasks)
        count_cols = st.columns(3)
        count_cols[0].metric("Upcoming", upcoming_count)
        count_cols[1].metric("Overdue", overdue_count)
        count_cols[2].metric("Completed", completed_count)

        pet_filter = st.selectbox(
            "Filter by pet", ["All pets"] + [pet.name for pet in owner.pets]
        )
        status_filter = st.selectbox("Filter by status", ["Pending", "Completed", "All"])
        completed_value = {"Pending": False, "Completed": True, "All": None}[status_filter]
        filtered_tasks = scheduler.filter_tasks(
            pet_name=None if pet_filter == "All pets" else pet_filter,
            completed=completed_value,
        )
        filtered_tasks.sort(key=lambda task: (task.time, task.pet_name.casefold(), task.id))

        if not filtered_tasks:
            st.info("No tasks match these filters.")
        else:
            for task in filtered_tasks:
                with st.container(border=True):
                    description_col, action_col = st.columns([3, 1])
                    with description_col:
                        st.write(task.description)
                        st.caption(
                            f"{task.pet_name} · {task.time.strftime('%b %d, %Y at %I:%M %p')}"
                            f" · {task.frequency.capitalize()} · {task_status(task, now)}"
                        )
                    with action_col:
                        if task.completed:
                            if st.button("Reopen", key=f"reopen_{task.id}"):
                                scheduler.reopen_task(task.id)
                                st.rerun()
                        else:
                            if st.button("Complete", key=f"complete_{task.id}"):
                                scheduler.complete_task(task.id)
                                st.rerun()

        conflicts = scheduler.find_conflicts()
        if conflicts:
            st.warning(f"Found {len(conflicts)} scheduling conflict(s) at the same date and time.")
            for first, second in conflicts:
                st.caption(
                    f"{first.time.strftime('%b %d, %Y at %I:%M %p')}: "
                    f"{first.pet_name} — {first.description} / "
                    f"{second.pet_name} — {second.description}"
                )

    st.caption("Tasks are stored in this Streamlit session and are not saved after the session resets.")
