from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json

# Cac loai cau hoi khop voi tu khoa kich hoat trong `retrieval/qa.py::_extract_answer`,
# de baseline answer sinh ra dung trung khop voi ground_truth o day.
QUESTION_TYPE_CYCLE = ["authors", "date", "categories", "summary"]
MIN_TEST_SET_SIZE = 5


def _question_for_type(question_type: str, row: pd.Series) -> tuple[str, str] | None:
    title = row["title"]
    if question_type == "authors":
        if not row["authors_joined"]:
            return None
        return f"Who authored the paper titled '{title}'?", row["authors_joined"]
    if question_type == "date":
        if not row["published"]:
            return None
        return f"When was the paper titled '{title}' published?", row["published"]
    if question_type == "categories":
        if not row["categories_joined"]:
            return None
        return f"What categories does the paper titled '{title}' belong to?", row["categories_joined"]
    if question_type == "summary":
        if not row["summary"]:
            return None
        return f"What is the paper titled '{title}' about?", first_sentence(row["summary"])
    raise ValueError(f"Unknown question_type: {question_type}")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Tao bo evaluation set (frozen) tu cleaned dataframe."""
    if df.empty:
        raise ValueError("Cannot build test set from an empty cleaned dataframe.")

    target_size = max(MIN_TEST_SET_SIZE, min(10, len(df)))
    samples: list[dict[str, Any]] = []

    for position, (_, row) in enumerate(df.iterrows()):
        if len(samples) >= target_size:
            break

        preferred_type = QUESTION_TYPE_CYCLE[position % len(QUESTION_TYPE_CYCLE)]
        result = _question_for_type(preferred_type, row)
        question_type = preferred_type
        if result is None:
            for fallback_type in QUESTION_TYPE_CYCLE:
                result = _question_for_type(fallback_type, row)
                if result is not None:
                    question_type = fallback_type
                    break
        if result is None:
            continue

        question, ground_truth = result
        samples.append(
            {
                "id": f"q{len(samples) + 1}",
                "question_type": question_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [row["paper_id"]],
            }
        )

    if len(samples) < MIN_TEST_SET_SIZE:
        raise ValueError(f"Only generated {len(samples)} test samples; need at least {MIN_TEST_SET_SIZE}.")

    write_json(output_path, samples)
    return samples
