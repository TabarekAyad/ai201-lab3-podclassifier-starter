# Evaluation Spec — Pod Classifier

Complete this spec **before** writing any code for Milestone 3.

Use Plan or Ask mode to think through each blank field. When you're done,
your answers here become the blueprint for `compute_accuracy()` and
`compute_per_class_accuracy()` in `evaluate.py`.

---

## Background: What is evaluation?

After building a classifier, we need to know how well it works. Evaluation answers:
- **Overall:** What fraction of episodes did we classify correctly?
- **Per-class:** Are we better at some labels than others?

Both functions take the same inputs: a list of predicted labels and a list of
ground-truth labels, in the same order.

---

## compute_accuracy(predictions, ground_truth)

### What it does
Returns the fraction of predictions that exactly match the ground truth.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`, one per episode. |
| `ground_truth` | `list[str]` | The correct labels, in the same order as `predictions`. |

### Output

| Return value | Type | Description |
|---|---|---|
| accuracy | `float` | A value between 0.0 and 1.0. |

---

### Spec fields — fill these in before writing code

**Formula:**

```
accuracy = number of positions where predictions[i] == ground_truth[i]
           ÷ total number of episodes

"Correct" means exact string match between the predicted label and the
ground-truth label at the same index. Case matters — "Interview" ≠ "interview"
— but our classifier always returns lowercase, so this isn't a real risk.
```

---

**Step-by-step logic:**

```
1. If ground_truth is empty, return 0.0 (guard against division by zero).
2. Count correct predictions: sum 1 for each i where predictions[i] == ground_truth[i].
3. Divide correct count by len(ground_truth).
4. Return the float.
```

---

**Edge case — what if both lists are empty?**

```
Return 0.0. There are no predictions to evaluate, so accuracy is undefined —
0.0 is the safest sentinel and avoids a ZeroDivisionError.
```

---

**Worked example:**

```
predictions  = ["interview", "solo", "panel", "interview"]
ground_truth = ["interview", "solo", "solo",  "narrative"]

Position 0: "interview" == "interview"  ✓
Position 1: "solo"      == "solo"       ✓
Position 2: "panel"     == "solo"       ✗
Position 3: "interview" == "narrative"  ✗

correct = 2
total   = 4
accuracy = 2 / 4 = 0.5
```

---

## compute_per_class_accuracy(predictions, ground_truth)

### What it does
Returns accuracy broken down by each label. For each label in `VALID_LABELS`,
reports how many episodes with that ground-truth label were classified correctly.

### Inputs

| Parameter | Type | Description |
|---|---|---|
| `predictions` | `list[str]` | Labels predicted by `classify_episode()`. |
| `ground_truth` | `list[str]` | Correct labels, in the same order. |

### Output

A `dict` keyed by label. Each value is a dict with three keys:

```python
{
    "interview": {"correct": int, "total": int, "accuracy": float},
    "solo":      {"correct": int, "total": int, "accuracy": float},
    "panel":     {"correct": int, "total": int, "accuracy": float},
    "narrative": {"correct": int, "total": int, "accuracy": float},
}
```

---

### Spec fields — fill these in before writing code

**What does "correct" mean for a given class?**

```
An episode counts as correctly classified for class X when:
  - ground_truth[i] == X  (the episode actually belongs to class X)
  - AND predictions[i] == X  (we predicted X)

Both conditions must hold. An episode where ground_truth="solo" and
predicted="solo" is correct for solo. An episode where ground_truth="solo"
and predicted="interview" is a miss for solo — it increments solo's total
but not solo's correct count.
```

---

**What does "total" mean for a given class?**

```
Total for class X = number of episodes where ground_truth[i] == X.
It is NOT the total number of all predictions. It counts only the episodes
that actually belong to that class in the test set.
```

---

**Step-by-step logic:**

```
1. Initialize a dict for each label in VALID_LABELS:
     {label: {"correct": 0, "total": 0} for label in VALID_LABELS}

2. Loop over zip(predictions, ground_truth) to get (predicted, truth) pairs.

3. For each pair:
     - Increment counts[truth]["total"] by 1  (this episode belongs to truth's class)
     - If predicted == truth:
         increment counts[truth]["correct"] by 1

4. After the loop, compute accuracy for each label:
     accuracy = correct / total  if total > 0  else 0.0

5. Return the dict with all three fields (correct, total, accuracy) per label.
```

---

**Edge case — what if a class has no examples in ground_truth (total == 0)?**

```
Set accuracy to 0.0. Dividing by zero would raise an exception, and there
are no examples to evaluate — 0.0 is the correct sentinel. This can happen
on small or imbalanced test sets.
```

---

**Worked example:**

```
predictions  = ["interview", "interview", "solo", "panel", "panel"]
ground_truth = ["interview", "solo",      "solo", "panel", "narrative"]

Step through each pair:
  (interview, interview) → total[interview]++, correct[interview]++
  (interview, solo)      → total[solo]++                            (miss)
  (solo,      solo)      → total[solo]++,      correct[solo]++
  (panel,     panel)     → total[panel]++,     correct[panel]++
  (panel,     narrative) → total[narrative]++                       (miss)

label       correct  total  accuracy
----------  -------  -----  --------
interview      1       1      1.0
solo           1       2      0.5
panel          1       1      1.0
narrative      0       1      0.0
```

---

## Reflection questions (discuss at the checkpoint)

1. Your overall accuracy might be decent even if one class has very low accuracy.
   Why is per-class accuracy a more informative metric than overall accuracy alone?

2. If `panel` episodes consistently get misclassified as `interview`, what does
   that tell you about your training labels or your prompt?

3. You labeled 20 training episodes and evaluated on 20 test episodes (5 per class).
   How might the evaluation results change if you had labeled 100 training episodes?
   What if you had 200 test episodes?
