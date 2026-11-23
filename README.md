# PawPal+ AI Daily Care Planner

**An improved pet-care tracker with a daily planning workflow, safety checks, and automated reliability tests.** Built with Python and Streamlit.

## Original project (Module 2)
This project extends **PawPal+ (AI110 Module 2)**. My original application stored pets, feeding records, veterinary visits, and care tasks using classes such as `Owner`, `Pet`, `Task`, and `Scheduler`. It included a Streamlit interface for pet records and a Python scheduler; the final-project work added web-based task management and a daily planner.

## What the improved system does
- Add and view pets, feedings, and veterinary visit history.
- Create one-time, daily, or weekly tasks, and mark tasks completed or reopened.
- Identify incomplete overdue tasks and tasks scheduled at the **exact same time**.
- Generate a **rules-only care plan** without a key or paid service.
- Optionally ask an OpenAI language model for recommendations based on the real tasks in the app.
- Check AI output before showing it. If validation fails, the app returns to the labeled rules-only plan.
- Keep a person in control: plans are recommendations and do not automatically update tasks.

**Important distinction:** The rules-only preview uses fixed Python logic, **not a language model**. The optional AI mode requires API access and has not been live-tested for this submission. The integrated reliability/guardrail system and automated tests can be demonstrated without paying for API calls.

## Architecture overview
Mermaid source: [`diagrams/architecture.mmd`](diagrams/architecture.mmd). Existing class diagram: [`diagrams/uml.mmd`](diagrams/uml.mmd).

The flow is: **Streamlit input → stored pet/task records → retrieval → rule-based baseline → optional LLM → strict validation → displayed plan → human review**. If model output is invalid or the request fails, the system shows the baseline plan instead. Tests exercise both the baseline and the validation/fallback paths with a fake model client; no real AI API call is required to run the tests.

## How to run it (Windows / VS Code)
1. Clone this repository and open the project folder in VS Code.
2. Create and activate a Python virtual environment.
3. Install dependencies, run tests, and launch Streamlit.

In **PowerShell**:

```powershell
cd path\to\pawpal-ai-final
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

In **Command Prompt**, activate with `.venv\Scripts\activate.bat` instead. Then run the same `python -m ...` commands. If PowerShell blocks script activation, use CMD rather than changing machine-wide security settings.

You can also run the existing command-line scheduler demonstration with `python main.py`.

**No API key needed:** In the **AI Planner** tab, select **Rules-only preview (no API key)**.

**Optional API mode:** Select **AI recommendations** and supply an OpenAI API key from https://platform.openai.com/api-keys, or set `OPENAI_API_KEY` in your environment. This service may incur charges. Never put the key into source code, screenshots, or a Git commit. A free local LLM is a future option, but **Ollama is not integrated into this version**.

## Sample interactions and outputs
The following are reproducible **rules-only** examples from a fixed test time of **November 22, 2026, at 12:00 PM**. The words in optional AI mode may differ.

| Input / situation | Result |
|---|---|
| Mochi has an unfinished feeding task scheduled for 8:00 AM today | **High** priority. "This scheduled task is overdue; check whether it was already done." |
| Mochi grooming and Biscuit walking are both scheduled for 4:00 PM today | Both have **Medium** priority, with a message that another pending task has the same time |
| No tasks have been created | "No pending tasks for this day or overdue tasks were found." |

### Demo steps
1. In **Pets**, create two pets.
2. In **Tasks**, add an overdue task and two tasks at the same exact time.
3. In **AI Planner**, select today's date and **Rules-only preview**; generate the plan.
4. Confirm overdue tasks are High and the matching-time tasks show a conflict.
5. Mark a task complete in **Tasks**; regenerate the plan to see current results.

## Design choices and trade-offs
I reused `Scheduler.organize_tasks()` from my Module 2 project instead of writing a new scheduling system. This kept the code modular and prevented duplicate logic. The retrieval and baseline rules produce a dependable fallback, while an optional language model can write more flexible explanations. Strict validation prevents fabricated task IDs or unsafe priority downgrades, but it cannot fully verify whether natural-language explanations are true. The planner relies on user-entered data and does not offer medical advice.

## Testing summary
**Development test run:** `python -m pytest -q` → **42 passed, 0 failed** (27 original/Task Management tests + 15 AI planner tests). This includes incorrect fake model responses, exceptions, missing records, and task-state changes. See [`tests/EVALUATION.md`](tests/EVALUATION.md) for test-by-test outcomes and honest manual-test status.

**What worked:** The rule-based baseline and rejection/fallback logic passed the automated cases; the rules-only preview was also manually reported working. **What is not yet verified:** A live external AI request, the quality of actual model wording, and a complete end-to-end browser test. The scheduled-time selector bug was fixed and manually confirmed.

## Limitations and future improvements
- Streamlit session storage is temporary; no persistent database has been added.
- Scheduling conflicts cover exact-time matches, not overlapping task durations.
- Overdue only means **unmarked and past the scheduled time**, not necessarily forgotten.
- Optional model explanations can contain mistakes despite structural checks.
- A user must review recommendations and confirm task completion.
- Future upgrades: persistent records, duration-aware scheduling, more human evaluations, and an optional locally hosted model.

## Reflection
This project taught me to improve existing code rather than replace it. The main lesson was that testing and guardrails are part of the system, not extra scripts added after the fact. My graded **Reflection and Ethics** responses, including one AI suggestion I accepted and one I revised, are in [`model_card.md`](model_card.md).
