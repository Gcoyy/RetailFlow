from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database.connection import get_db
from app.database.models import (
    DataSource,
    Pipeline,
    PipelineRun,
    RawRecord,
    StagingSalesTransaction,
    QualityIssue,
    WarehouseSale,
    PipelineLog,
)

router = APIRouter(prefix="/api", tags=["RetailFlow Data"])


# Helper functions

def format_datetime(value):
    if not value:
        return None

    return value.strftime("%b %d, %Y %I:%M %p")


def format_duration(started_at, completed_at):
    if not started_at or not completed_at:
        return "—"

    seconds = int((completed_at - started_at).total_seconds())
    seconds = max(seconds, 0)

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes}m {seconds}s"

    if minutes:
        return f"{minutes}m {seconds}s"

    return f"{seconds}s"


def time_ago(value):
    if not value:
        return "Never"

    now = datetime.now(timezone.utc)

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    seconds = max(int((now - value).total_seconds()), 0)

    if seconds < 60:
        return "Just now"

    if seconds < 3600:
        return f"{seconds // 60} min ago"

    if seconds < 86400:
        return f"{seconds // 3600} hour(s) ago"

    return f"{seconds // 86400} day(s) ago"


def execution_code(run_id):
    return f"EX-{run_id:04d}"


# 1. DASHBOARD SUMMARY

@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):

    total_sources = db.query(func.count(DataSource.id)).scalar() or 0

    total_pipelines = db.query(func.count(Pipeline.id)).scalar() or 0

    total_records = db.query(func.count(RawRecord.id)).scalar() or 0

    valid_records = db.query(
        func.count(WarehouseSale.id)
    ).scalar() or 0

    failed_records = db.query(
        func.count(func.distinct(QualityIssue.raw_record_id))
    ).scalar() or 0

    total_issues = db.query(
        func.count(QualityIssue.id)
    ).scalar() or 0

    latest_run = (
        db.query(PipelineRun)
        .order_by(desc(PipelineRun.started_at))
        .first()
    )

    success_rate = (
        round((valid_records / total_records) * 100, 2)
        if total_records else 0
    )

    return {
        "total_sources": total_sources,
        "total_pipelines": total_pipelines,
        "total_records": total_records,
        "valid_records": valid_records,
        "failed_records": failed_records,
        "total_quality_issues": total_issues,
        "success_rate": success_rate,
        "latest_run_status": latest_run.status if latest_run else "None",
    }


# 2. DATA SOURCES

@router.get("/sources")
def get_sources(db: Session = Depends(get_db)):

    sources = db.query(DataSource).order_by(DataSource.id).all()

    results = []

    for source in sources:

        # Count original records extracted from this source
        source_records = (
            db.query(func.count(RawRecord.id))
            .join(PipelineRun, RawRecord.pipeline_run_id == PipelineRun.id)
            .join(Pipeline, PipelineRun.pipeline_id == Pipeline.id)
            .filter(Pipeline.source_id == source.id)
            .scalar()
        ) or 0

        destination_records = (
            db.query(func.count(WarehouseSale.id))
            .join(PipelineRun, WarehouseSale.pipeline_run_id == PipelineRun.id)
            .join(Pipeline, PipelineRun.pipeline_id == Pipeline.id)
            .filter(Pipeline.destination_id == source.id)
            .scalar()
        ) or 0

        record_count = source_records + destination_records

        results.append({
            "id": source.id,
            "name": source.name,
            "type": source.source_type,
            "status": source.status,
            "sync": time_ago(source.last_sync_at),
            "records": f"{record_count:,}",
            "created": format_datetime(source.created_at),
        })

    return results


# 3. PIPELINES

@router.get("/pipelines")
def get_pipelines(db: Session = Depends(get_db)):

    pipelines = db.query(Pipeline).order_by(Pipeline.id).all()

    results = []

    for pipeline in pipelines:

        latest_run = (
            db.query(PipelineRun)
            .filter(PipelineRun.pipeline_id == pipeline.id)
            .order_by(desc(PipelineRun.started_at))
            .first()
        )

        source = db.get(DataSource, pipeline.source_id)
        destination = db.get(DataSource, pipeline.destination_id)

        processed = latest_run.records_processed if latest_run else 0
        failed = latest_run.records_failed if latest_run else 0

        total = processed + failed

        rate = (
            f"{(processed / total) * 100:.1f}%"
            if total else "—"
        )

        results.append({
            "id": pipeline.id,
            "name": pipeline.name,
            "source": source.name if source else "Unknown",
            "destination": destination.name if destination else "Unknown",
            "status": pipeline.status,
            "duration": (
                format_duration(
                    latest_run.started_at,
                    latest_run.completed_at
                )
                if latest_run else "—"
            ),
            "records": f"{processed:,}",
            "rate": rate,
        })

    return results


# 4. DATA QUALITY ISSUES

@router.get("/quality/issues")
def get_quality_issues(db: Session = Depends(get_db)):

    issues = (
        db.query(QualityIssue)
        .order_by(desc(QualityIssue.created_at))
        .all()
    )

    results = []

    for issue in issues:

        results.append({
            "id": f"VAL-{issue.id:04d}",
            "dataset": "sales_transactions.csv",
            "field": issue.field,
            "rule": issue.rule,
            "error": issue.message,
            "severity": issue.severity,
            "date": format_datetime(issue.created_at),
            "status": issue.status,
        })

    return results


# 5. EXECUTION HISTORY

@router.get("/executions")
def get_executions(db: Session = Depends(get_db)):

    runs = (
        db.query(PipelineRun)
        .order_by(desc(PipelineRun.started_at))
        .all()
    )

    results = []

    for run in runs:

        pipeline = db.get(Pipeline, run.pipeline_id)

        results.append({
            "id": execution_code(run.id),
            "pipeline": pipeline.name if pipeline else "Unknown",
            "status": run.status,
            "records": f"{run.records_processed:,}",
            "duration": format_duration(
                run.started_at,
                run.completed_at
            ),
            "start": format_datetime(run.started_at),
            "trigger": run.trigger_type,
        })

    return results


# 6. PIPELINE LOGS

@router.get("/logs")
def get_logs(db: Session = Depends(get_db)):

    logs = (
        db.query(PipelineLog)
        .order_by(desc(PipelineLog.created_at))
        .limit(100)
        .all()
    )

    results = []

    for log in logs:

        run = db.get(PipelineRun, log.pipeline_run_id)

        pipeline = (
            db.get(Pipeline, run.pipeline_id)
            if run else None
        )

        results.append({
            "id": log.id,
            "time": format_datetime(log.created_at),
            "level": log.level,
            "pipeline": pipeline.name if pipeline else "Unknown",
            "execution": execution_code(run.id) if run else "Unknown",
            "message": log.message,
            "component": log.component,
        })

    return results


# 7. RECENT ACTIVITY

@router.get("/activity")
def get_activity(db: Session = Depends(get_db)):

    logs = (
        db.query(PipelineLog)
        .order_by(desc(PipelineLog.created_at))
        .limit(5)
        .all()
    )

    return [
        log.message
        for log in logs
    ]