from __future__ import annotations

import pandas as pd


from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate multiple forms of data corruption.

    Steps:
    1. Drop some latest records.
    2. Blank summary on some rows.
    3. Inject noise into summary text.
    4. Truncate titles.
    5. Make publication dates stale.
    6. Add duplicate rows.
    7. Rebuild `text_for_embedding`.
    8. Write corruption log to output_log_path.
    """
    if df.empty:
        write_json(
            output_log_path,
            {"total_input_rows": 0, "total_output_rows": 0, "actions": []},
        )
        return df.copy()

    corrupted_df = df.copy()
    total_input_rows = len(corrupted_df)
    corruption_log: dict = {
        "total_input_rows": total_input_rows,
        "actions": [],
    }

    # 1. Drop some latest records
    drop_count = min(2, len(corrupted_df) - 1) if len(corrupted_df) > 1 else 0
    if drop_count > 0:
        dropped_ids = corrupted_df.iloc[:drop_count]["paper_id"].tolist()
        corrupted_df = corrupted_df.iloc[drop_count:].reset_index(drop=True)
        corruption_log["actions"].append(
            {
                "type": "drop_latest_records",
                "count": drop_count,
                "dropped_paper_ids": dropped_ids,
            }
        )

    # 2. Blank summary on a row
    if len(corrupted_df) > 0:
        target_idx = 0
        paper_id = corrupted_df.loc[target_idx, "paper_id"]
        corrupted_df.loc[target_idx, "summary"] = ""
        corrupted_df.loc[target_idx, "summary_chars"] = 0
        corruption_log["actions"].append(
            {
                "type": "blank_summary",
                "paper_id": paper_id,
                "row_index": target_idx,
            }
        )

    # 3. Inject noise into summary text
    if len(corrupted_df) > 1:
        target_idx = 1
        paper_id = corrupted_df.loc[target_idx, "paper_id"]
        original_summary = str(corrupted_df.loc[target_idx, "summary"])
        noise = " [CORRUPTED_GARBAGE_TEXT ### !!! 9999999]"
        new_summary = original_summary + noise
        corrupted_df.loc[target_idx, "summary"] = new_summary
        corrupted_df.loc[target_idx, "summary_chars"] = len(new_summary)
        corruption_log["actions"].append(
            {
                "type": "inject_noise",
                "paper_id": paper_id,
                "row_index": target_idx,
            }
        )

    # 4. Truncate title
    if len(corrupted_df) > 2:
        target_idx = 2
        paper_id = corrupted_df.loc[target_idx, "paper_id"]
        orig_title = str(corrupted_df.loc[target_idx, "title"])
        truncated_title = orig_title[:15] + "..." if len(orig_title) > 15 else "Truncated"
        corrupted_df.loc[target_idx, "title"] = truncated_title
        corruption_log["actions"].append(
            {
                "type": "truncate_title",
                "paper_id": paper_id,
                "row_index": target_idx,
                "original_title": orig_title,
                "truncated_title": truncated_title,
            }
        )

    # 5. Make publication date stale
    if len(corrupted_df) > 3:
        target_idx = 3
        paper_id = corrupted_df.loc[target_idx, "paper_id"]
        stale_date = "2000-01-01"
        corrupted_df.loc[target_idx, "published"] = stale_date
        if "age_days" in corrupted_df.columns:
            corrupted_df.loc[target_idx, "age_days"] = 9000
        corruption_log["actions"].append(
            {
                "type": "stale_published_date",
                "paper_id": paper_id,
                "row_index": target_idx,
                "new_date": stale_date,
            }
        )

    # 6. Add duplicate rows
    if len(corrupted_df) > 0:
        dup_row = corrupted_df.iloc[[0]].copy()
        corrupted_df = pd.concat([corrupted_df, dup_row], ignore_index=True)
        corruption_log["actions"].append(
            {
                "type": "add_duplicate_row",
                "duplicated_paper_id": dup_row.iloc[0]["paper_id"],
            }
        )

    # 7. Rebuild `text_for_embedding`
    corrupted_df["text_for_embedding"] = corrupted_df.apply(
        lambda row: f"Title: {row.get('title', '')} | Authors: {row.get('authors_joined', '')} | Summary: {row.get('summary', '')}",
        axis=1,
    )

    corruption_log["total_output_rows"] = len(corrupted_df)

    # 8. Write corruption log to output_log_path
    write_json(output_log_path, corruption_log)

    return corrupted_df

