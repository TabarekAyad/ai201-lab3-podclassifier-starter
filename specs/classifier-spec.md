# Classifier Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 2.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `build_few_shot_prompt()` and
`classify_episode()` in `classifier.py`.

---

## build_few_shot_prompt(labeled_examples, description)

### What it does
Constructs a prompt string for the LLM that includes the task instructions,
all labeled training examples, and the new episode description to classify.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `labeled_examples` | `list[dict]` | Each dict has `"title"`, `"description"`, `"label"` (and others). These are the examples you labeled in Milestone 1. |
| `description` | `str` | The episode description to classify. |

### Output

| Return value | Type | Description |
|---|---|---|
| prompt | `str` | A complete prompt string ready to send to the LLM. |

---

### Spec fields — fill these in before writing code

**Task instruction (what should the LLM know about the task?):**

```
You are classifying podcast episodes by their format. Classify the episode
into exactly one of these four labels:

- interview: a conversation between a host and one or more guests
- solo: a single host speaking from memory, experience, or opinion — no guests,
  no assembled external sources
- panel: multiple guests with roughly equal speaking time, often debating or
  discussing a topic together
- narrative: a story assembled from external sources — interviews, archival
  audio, reporting — with a clear narrative arc

Return only the label and your reasoning. Do not explain the taxonomy.
```

---

**How should labeled examples be formatted in the prompt?**

```
Each example should include the episode title, a brief excerpt or the full
description, and the correct label. Separate examples with a blank line or
a delimiter like "---". Include all fields that help the model see why the
label was applied — title and description are both useful; other fields
(like episode ID) are not needed.
```

---

**Example block sketch (write one concrete example):**

```
Title: {title}
Description: {description}
Label: {label}
```

---

**How should the new episode (to be classified) be presented?**

```
Present it in the same format as the labeled examples, but omit the Label
line and replace it with an instruction to classify. For example:

Title: {title}
Description: {description}
Label: ?

Then add a line like: "Classify the episode above. Return your answer in
the format below:" followed by the output format you chose.
```

---

**What output format should you request from the LLM?**

```
Ask the LLM to respond in exactly this two-line format:

  Label: {label}
  Reasoning: {one sentence}

Rationale for this choice over alternatives:
- JSON: reliable when the model cooperates, but LLMs often wrap output in
  markdown code fences or produce trailing commas, causing json.loads() to
  raise and giving no partial recovery.
- Label-only first line: simplest to parse but breaks if the model adds any
  preamble (e.g. "Sure! The label is...").
- "Label: X / Reasoning: Y": easy to parse line-by-line, fails gracefully
  (the label line is still findable even if reasoning is odd), and
  normalizing to lowercase handles all capitalization variants.

Parsing strategy in classify_episode():
  1. Split response on newlines.
  2. Find the line that starts with "label:" (case-insensitive after .lower()).
  3. Extract everything after the colon, .strip().lower() → candidate label.
  4. Find the line that starts with "reasoning:" the same way → reasoning text.
```

---

**Edge cases to handle in the prompt:**

```
- labeled_examples is empty: build_few_shot_prompt() still constructs a
  valid prompt — the examples section is just absent. The LLM will classify
  from the task instructions alone (zero-shot). This is acceptable because
  app.py already guards against calling classify_episode() when
  labeled_examples is empty and shows a warning to the user instead.

- description is very short (e.g. a title with no body): the prompt still
  works structurally — less context just means less signal for the LLM.
  No special handling needed; the model will do its best and may return a
  lower-confidence reasoning.
```

---

## classify_episode(description, labeled_examples)

### What it does
Classifies a single podcast episode description using the few-shot LLM classifier.
Returns a dict with a label and reasoning.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `description` | `str` | The episode description to classify. |
| `labeled_examples` | `list[dict]` | Labeled training examples from `load_labeled_examples()`. |

### Output

| Return value | Type | Description |
|---|---|---|
| result | `dict` | Must have keys `"label"` and `"reasoning"`. `"label"` must be one of `VALID_LABELS` or `"unknown"`. |

---

### Spec fields — fill these in before writing code

**Step 1 — Build the prompt:**

```
Call build_few_shot_prompt(labeled_examples, description) and store the
returned string in a variable (e.g., prompt). Pass through both arguments
exactly as received — no modification needed before calling.
```

---

**Step 2 — Send to the LLM:**

```
Call _client.chat.completions.create() with:
  - model: the model name from config (LLM_MODEL)
  - messages: a list with one dict — {"role": "user", "content": prompt}
    (system-design.md shows an optional system message too — either shape works)
  - max_tokens: a reasonable limit (e.g., 200–300) to keep responses concise

Extract the response text from:
  response.choices[0].message.content
```

---

**Step 3 — Parse the response:**

```
Split response_text on newlines. Iterate over lines:
  - If a line lowercased starts with "label:", extract the part after the
    first colon → .strip().lower() → candidate label string.
  - If a line lowercased starts with "reasoning:", extract the part after
    the first colon → .strip() → reasoning string.

Use .split(":", 1) so that colons inside the reasoning text don't truncate it.
If neither line is found, label defaults to "unknown" and reasoning to the
full raw response (so there's something useful to display).
```

---

**Step 4 — Validate the label:**

```
After parsing and normalizing (strip + lower), check:
  if candidate_label not in VALID_LABELS:
      label = "unknown"
  else:
      label = candidate_label

Do not attempt fuzzy matching or synonym mapping — "unknown" is the correct
sentinel that tells the caller and the evaluation loop that something went wrong.
```

---

**Step 5 — Handle errors gracefully:**

```
Wrap the entire LLM call + parsing block in try/except Exception as e.
On any exception (network timeout, API error, malformed response, etc.):
  return {"label": "unknown", "reasoning": f"Error: {e}"}

This ensures the evaluation loop (which calls classify_episode() 20 times)
continues through all episodes even if one call fails. The "unknown" label
will count as a mismatch in compute_accuracy(), which is the honest outcome.
```

---

### Return value structure

```python
{
    "label": str,      # one of VALID_LABELS, or "unknown" if invalid/error
    "reasoning": str,  # brief explanation from the LLM
}
```

---

## Notes on label quality

The classifier is only as good as your labels. If your training examples have
inconsistent or ambiguous labels, the LLM will learn the wrong pattern.

Before implementing the classifier, re-read `data/taxonomy.md` and double-check
any labels you're unsure about. Annotation quality is part of the lab.

---

## Implementation Notes

**Test: what does the raw LLM response look like for one episode?**

```
Episode tested: The Aral Sea: A Disaster in Four Acts (expected: narrative)

Raw response text:
Label: narrative
Reasoning: The episode is described as telling a story in four parts, using a
structured narrative approach to convey the history and impact of the Aral Sea's
decline, which is characteristic of the narrative format.
```

**How did you parse the label out of the response?**

```
1. Split response_text on newlines to get individual lines.
2. For each line, call line.lower() to normalize capitalization.
3. If the lowercased line starts with "label:", use line.split(":", 1)[1]
   to extract everything after the first colon (the [1] limit prevents
   splitting on colons that appear inside the reasoning text).
4. Call .strip().lower() on the extracted value → candidate label string.
5. Same logic for "reasoning:" → reasoning string.

Example:
  line  = "Label: narrative"
  lower = "label: narrative"
  lower.startswith("label:")  → True
  line.split(":", 1)[1]       → " narrative"
  .strip().lower()            → "narrative"
```

**Did any episodes return `"unknown"`? If so, why?**

```
No. All four test cases returned a valid label. The model followed the
"Label: X\nReasoning: Y" format exactly in every response — no preamble,
no markdown fences, no capitalization variance — so every candidate label
passed the VALID_LABELS check.
```

**One thing about the output format that surprised you:**

```
The model was more consistent than expected — it never added preamble text
like "Sure!" or "Here is my classification:" before the Label line, and it
never wrapped output in markdown code fences. The two-line format held across
all four label types without a single deviation. The concern about capitalization
variance (e.g. "Interview" vs "interview") also turned out to be a non-issue
in practice, though the .lower() normalization is still the right defensive move.
```
