from __future__ import annotations


from datetime import UTC, datetime

import pandas as pd

from core.config import load_settings
from core.utils import read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xay dung corruption -> evaluate -> repair -> compare flow.

    Steps:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    settings = load_settings()

    if not settings.paths.clean_json.exists() and not settings.paths.clean_csv.exists():
        raise RuntimeError("Clean dataset not found. Please run Phase 1 baseline pipeline first.")

    if not settings.paths.baseline_metrics.exists():
        raise RuntimeError("Baseline metrics not found. Please run Phase 1 baseline pipeline first.")

    # 1. Load clean baseline dataset & baseline metrics
    if settings.paths.clean_json.exists():
        clean_df = pd.read_json(settings.paths.clean_json)
    else:
        clean_df = pd.read_csv(settings.paths.clean_csv)

    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # Ensure output directories exist
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.corrupted_embeddings_json.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.corrupted_metrics.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.repaired_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.repaired_embeddings_json.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.repaired_metrics.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.comparison_report.parent.mkdir(parents=True, exist_ok=True)

    # 2. Create corrupted dataframe
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)

    # 3. Save corrupted artifacts
    corrupted_df.to_csv(settings.paths.corrupted_clean_csv, index=False)
    corrupted_df.to_json(settings.paths.corrupted_clean_json, orient="records", indent=2)

    # 4. Rebuild index & evaluate on corrupted data
    corrupted_index = LocalEmbeddingIndex.build(
        df=corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    # 5. Run quality checks & freshness on corrupted data
    corrupted_quality = run_data_quality_checks(
        df=corrupted_df,
        settings=settings,
        report_name="corrupted_quality",
    )
    corrupted_freshness = build_freshness_report(
        df=corrupted_df,
        settings=settings,
        report_path=settings.paths.quality_dir / "corrupted_freshness_report.json",
    )

    # 6. Repair data from raw records
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, run_date=datetime.now(UTC))

    # Save repaired artifacts
    repaired_df.to_csv(settings.paths.repaired_clean_csv, index=False)
    repaired_df.to_json(settings.paths.repaired_clean_json, orient="records", indent=2)

    # 7. Rebuild index & evaluate repaired dataset
    repaired_index = LocalEmbeddingIndex.build(
        df=repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(
        df=repaired_df,
        settings=settings,
        report_name="repaired_quality",
    )
    repaired_freshness = build_freshness_report(
        df=repaired_df,
        settings=settings,
        report_path=settings.paths.quality_dir / "repaired_freshness_report.json",
    )

    # 8. Create comparison report
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    print("Corruption and repair flow completed successfully.")
    print(f"Comparison report saved to: {settings.paths.comparison_report}")

