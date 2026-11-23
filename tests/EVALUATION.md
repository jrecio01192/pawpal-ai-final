# PawPal+ Daily Planner — Reliability Evaluation

## Run command and result

```powershell
python -m pytest -q
```

**Recorded development run:** **42 passed, 0 failed** on November 22, 2026.
- **27 tests:** Original PawPal+ and Task Management functionality.
- **15 tests:** Daily planner retrieval, validation, and safe fallback.
- **AI test method:** Simulated model responses, **not** paid or live OpenAI calls.

## Automated evaluation results

| Test case / input | What was checked | Result |
|---|---|---|
| Empty task list | Returns empty plan without crashing | Pass |
| Past-due, same-day, future, and completed tasks | Includes only relevant incomplete tasks | Pass |
| Overdue task | Marks it High priority | Pass |
| Two incomplete tasks at identical time | Flags both as conflicting | Pass |
| Valid simulated model recommendation | Returns only real task IDs, labels result AI | Pass |
| Model invents a task ID | Rejects output; falls back safely | Pass |
| Model leaves a task out | Rejects output; falls back safely | Pass |
| Model lowers overdue priority | Rejects output; preserves High baseline | Pass |
| Model lowers conflict priority | Rejects output; preserves Medium baseline | Pass |
| Model repeats one task ID | Rejects output; falls back safely | Pass |
| Model request fails | No record change; rules-only fallback | Pass |
| AI selected without a key | Clear error for nonempty task plan | Pass |
| Past and upcoming vet visits | Includes only visits in the upcoming three-day window | Pass |
| Task updated after plan generation | Record signature changes, indicating a stale plan | Pass |
| Invalid date input type | Rejects invalid input | Pass |

## Browser and live-model evaluation status

| Check | Result | Evidence / qualification |
|---|---|---|
| Rules-only plan in Streamlit | **Pass — user-confirmed** | User reported the rules preview generated successfully |
| Scheduled-time picker accepts selected time | **Pass — user-confirmed** | User reported the time-selector fix worked |
| Complete end-to-end browser run with all scenarios | Not fully verified | Only the above actions are confirmed |
| Live OpenAI AI recommendation | Not tested | Paid API access intentionally not used |
| Local Ollama model integration | Not implemented | Suggested future improvement, not part of current submission |

## Interpretation
The automated results demonstrate that retrieval, baseline priorities, data checks, and the model-response fallback logic behave as designed in the tested cases. **They do not establish that a real LLM will answer correctly or that the whole Streamlit interface is bug-free.** In particular, validation checks IDs, basic structure, and priority floors—not the truth of every natural-language claim.

## Improvements identified
1. Add persistent storage so restarting a Streamlit session does not lose records.
2. Support overlapping task durations and realistic scheduling constraints.
3. Gather human ratings of model explanations after connecting a real local or cloud model.
4. Add more browser-level integration tests.
