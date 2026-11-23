# PawPal+ AI Daily Care Planner — Model Card

## Project and system summary
**Original project:** PawPal+ (AI110 Module 2).

PawPal+ began as a Python and Streamlit application for managing pets, recording feedings and veterinary visits, and organizing care tasks. The final-project extension adds a Task Management interface and a Daily Care Planner with record retrieval, rule-based priorities, optional language-model explanations, and automated validation.

## Model / system used
- **Free, working mode:** Rules-only preview. This is a deterministic Python planning system, **not** an AI-generated answer.
- **Optional AI mode:** OpenAI Responses API, configured in code to use `gpt-4.1-mini` unless changed. It needs a separately billed API key. I have **not** verified a live API call for the final project.
- **Reliability feature:** The app validates model recommendations against stored task IDs and priority rules. Automated tests use a fake model client so they run without paid API access.

## Goal and intended use
Help pet owners review incomplete care tasks, see overdue tasks, identify tasks scheduled for the same time, and decide what to check first. The system does not automatically complete or reschedule tasks. It is not a veterinarian and is not meant for diagnosis, feeding quantities, medication doses, or emergencies.

## Inputs and outputs
**Inputs:** Existing pet names, task descriptions and IDs, scheduled dates/times, completion states, and upcoming recorded vet visit dates. In AI mode, these records (including pet names, task descriptions, and clinic names) are sent to the model provider.

**Outputs:** A labeled daily plan listing known task IDs, priorities (High/Medium/Low), short explanations, and upcoming recorded vet visits. The free preview generates explanations from fixed rules. The optional model mode may vary its wording, but must pass validation before display.

## Workflow and guardrails
1. Retrieve incomplete tasks scheduled for the selected day plus any past-due incomplete tasks.
2. Create a rules-only baseline: overdue tasks are High priority; same-time conflicts are at least Medium priority.
3. If the user chooses AI mode and provides a key, request structured recommendations about those **existing** tasks.
4. Validate the response: every known task appears once, no fabricated IDs are accepted, priority floors hold, and fields have valid formats and lengths.
5. If the request fails or the response fails validation, display a clearly labeled rules-only fallback. Recommendations never update task records automatically.

The system also logs request mode, task counts, and error types without logging the API key or task text. A change to stored records invalidates a previously displayed plan.

## Reliability and testing results
**Automated tests:** `python -m pytest -q` → **42 passed, 0 failed** in the development environment (27 existing/Task Management tests and 15 planner tests). The planner tests simulate valid and invalid model responses. They test invented IDs, omitted tasks, duplicate IDs, lowered priorities, request failures, empty data, and record changes.

**Manual checks reported:** The user confirmed that the rules-only preview works and that a scheduled-time input problem was fixed. A live language-model request has **not** been tested; passing mock tests does not prove it works or that explanations are always accurate. Detailed cases and outcomes are in [`tests/EVALUATION.md`](tests/EVALUATION.md).

## Reflection and Ethics

### 1. What are the limitations or biases in your system?
The planner depends on the records a person enters. If someone forgets to mark a task complete, it may appear overdue even if it was already done. It treats every overdue task as High priority, even though some tasks are more important than others. It only detects conflicts when two tasks have the exact same scheduled time; it does not account for task duration or travel. Data is stored only in the current Streamlit session, so it is not a long-term record system.

The optional language model could also give misleading explanations or reflect patterns from its training data. My automated tests check task references and priorities, but they do not prove that every sentence an AI model generates is correct.

### 2. Could your AI be misused, and how would you prevent that?
Yes. A user might mistake a scheduling recommendation for veterinary advice or trust an AI statement without checking the records. Someone could also enter misleading instructions inside a task description and try to influence the model's answer.

To reduce these risks, the app explains that it is **not veterinary advice**, requires people to confirm whether tasks were actually completed, and does not change records automatically. The AI prompt tells the model to treat task descriptions as untrusted data. The validator rejects made-up task IDs, missing tasks, duplicate tasks, and unsafe priority changes. If validation fails, it shows the rules-only preview instead. API keys should never be shared or committed to GitHub, and private pet information should not be entered into external AI mode without understanding that it is sent to a provider.

### 3. What surprised you while testing your AI's reliability?
I learned that a model response can look properly formatted and still be wrong. In simulated tests, recommendations that used a made-up task ID, skipped a real task, or lowered an overdue task's priority were rejected. This showed why I needed checks in Python instead of trusting an AI response just because it was valid JSON.

I also ran into a separate scheduling-time input bug during the project. Fixing that reminded me that the interface and ordinary app logic need testing too, not just the AI portion. The **42 passing automated tests** are encouraging, but they cannot replace a live model test or checking results in the browser.

### 4. How did you collaborate with AI? What suggestion did you accept and what did you change or reject?
I used an AI coding assistant to plan the extension, review how my existing classes fit together, write the new planner and tests, and debug problems. I **accepted** the suggestion to separate task retrieval, a baseline plan, and model-output validation. This made failures easier to test and helped prevent the AI from inventing tasks.

I **changed** the suggestion to rely on a paid OpenAI API for the main demonstration. I did not want API charges, so I kept a free rules-only preview that can run and be tested without a key, while leaving external AI mode optional. I made sure the free mode is clearly labeled as rule-based rather than pretending that it uses an AI model. This trade-off keeps the project accessible, although actual live AI reasoning remains unverified unless a model is connected and tested.

## Responsible use and future improvements
This tool should support a pet owner's judgment, not replace a veterinarian or make medical decisions. In the future I would add permanent storage, detect overlapping task durations rather than only identical times, test explanation quality with human reviewers, and optionally connect a free local model such as Ollama after testing its reliability.
