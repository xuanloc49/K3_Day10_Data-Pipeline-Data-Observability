from __future__ import annotations


from datetime import UTC, datetime

from core.config import load_settings
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xay dung baseline pipeline end-to-end.

    Steps:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    """
    settings = load_settings()

    # Ensure parent output directories exist
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.embeddings_json.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.eval_testset.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.baseline_metrics.parent.mkdir(parents=True, exist_ok=True)
    settings.paths.quality_dir.mkdir(parents=True, exist_ok=True)
    settings.paths.baseline_report.parent.mkdir(parents=True, exist_ok=True)

    # 1. Load or fetch raw records
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    # 2. Clean data
    run_date = datetime.now(UTC)
    clean_df = build_clean_dataframe(records, run_date=run_date)

    # 3. Save clean CSV / JSON
    clean_df.to_csv(settings.paths.clean_csv, index=False)
    clean_df.to_json(settings.paths.clean_json, orient="records", indent=2)

    # 4. Build Chroma index
    index = LocalEmbeddingIndex.build(
        df=clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    # 5. Create or load evaluation test set
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)

    # 6. Evaluate baseline
    eval_bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 7. Run quality checks & freshness report
    quality_res = run_data_quality_checks(
        df=clean_df,
        settings=settings,
        report_name="baseline_quality",
    )
    freshness_res = build_freshness_report(
        df=clean_df,
        settings=settings,
        report_path=settings.paths.freshness_report,
    )

    # 8. Create markdown report
    source_summary = {
        "total_raw_records": len(records),
        "clean_records": len(clean_df),
        "source_api": settings.source_api,
        "query": settings.source_query,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=eval_bundle.summary,
        quality=quality_res,
        freshness=freshness_res,
    )

    print("Phase 1 baseline pipeline completed successfully.")
    print(f"Clean CSV saved to: {settings.paths.clean_csv}")
    print(f"Baseline report saved to: {settings.paths.baseline_report}")

