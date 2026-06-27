import json
import os
from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL, VALID_LABELS, DATA_PATH, TRAIN_FILE, LABELS_FILE

_client = Groq(api_key=GROQ_API_KEY)


def load_labeled_examples() -> list[dict]:
    """
    Load the training episodes and merge them with the student's labels.

    Returns a list of dicts, each with:
      - "id"          : episode ID
      - "title"       : episode title
      - "podcast"     : podcast name
      - "description" : episode description
      - "label"       : the label from my_labels.json (may be None if not yet annotated)

    Only returns episodes where the label is a valid, non-null string.
    Episodes with null labels are silently skipped.
    """
    train_path = os.path.join(DATA_PATH, TRAIN_FILE)
    labels_path = os.path.join(DATA_PATH, LABELS_FILE)

    with open(train_path, encoding="utf-8") as f:
        episodes = {ep["id"]: ep for ep in json.load(f)}

    with open(labels_path, encoding="utf-8") as f:
        labels = {entry["id"]: entry["label"] for entry in json.load(f)}

    labeled = []
    for ep_id, ep in episodes.items():
        label = labels.get(ep_id)
        if label in VALID_LABELS:
            labeled.append({**ep, "label": label})

    return labeled


def build_few_shot_prompt(labeled_examples: list[dict], description: str) -> str:
    """
    Build a few-shot classification prompt using the student's labeled training examples.
    """
    task_instruction = (
        "You are classifying podcast episodes by their structural format.\n"
        "Assign exactly one of these four labels:\n\n"
        "- interview: a host speaks with one guest; the guest's knowledge or story drives the episode\n"
        "- solo: a single host speaking alone from memory, opinion, or experience — no guests\n"
        "- panel: three or more speakers with roughly equal standing discussing a topic together\n"
        "- narrative: a story assembled from external sources (reporting, archives, interview clips) with a clear story arc\n\n"
        "Classify by structure, not topic or tone."
    )

    example_blocks = []
    for ex in labeled_examples:
        example_blocks.append(
            f"Title: {ex['title']}\n"
            f"Description: {ex['description']}\n"
            f"Label: {ex['label']}"
        )
    examples_section = "\n\n---\n\n".join(example_blocks)

    new_episode = (
        f"Title: (not provided)\n"
        f"Description: {description}\n"
        f"Label: ?"
    )

    output_instruction = (
        "Classify the episode above. Respond in exactly this format:\n\n"
        "Label: <label>\n"
        "Reasoning: <one sentence>\n\n"
        "Use only one of: interview, solo, panel, narrative."
    )

    parts = [task_instruction]
    if example_blocks:
        parts.append("Here are labeled examples:\n\n" + examples_section)
    parts.append("Now classify this episode:\n\n" + new_episode)
    parts.append(output_instruction)

    return "\n\n".join(parts)


def classify_episode(description: str, labeled_examples: list[dict]) -> dict:
    """
    Classify a single podcast episode description using the few-shot LLM classifier.
    """
    try:
        prompt = build_few_shot_prompt(labeled_examples, description)

        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        response_text = response.choices[0].message.content

        label = "unknown"
        reasoning = response_text.strip()

        for line in response_text.splitlines():
            lower = line.lower()
            if lower.startswith("label:"):
                label = line.split(":", 1)[1].strip().lower()
            elif lower.startswith("reasoning:"):
                reasoning = line.split(":", 1)[1].strip()

        if label not in VALID_LABELS:
            label = "unknown"

        return {"label": label, "reasoning": reasoning}

    except Exception as e:
        return {"label": "unknown", "reasoning": f"Error: {e}"}
