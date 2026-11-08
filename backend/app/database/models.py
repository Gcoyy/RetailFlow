from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Numeric,
    ForeignKey,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


# 1. DATA SOURCES
class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Connected")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    source_pipelines: Mapped[list["Pipeline"]] = relationship(
        back_populates="source",
        foreign_keys="Pipeline.source_id",
    )
    destination_pipelines: Mapped[list["Pipeline"]] = relationship(
        back_populates="destination",
        foreign_keys="Pipeline.destination_id",
    )


# 2. PIPELINES
class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Paused")

    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id"), nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["DataSource"] = relationship(
        back_populates="source_pipelines",
        foreign_keys=[source_id],
    )
    destination: Mapped["DataSource"] = relationship(
        back_populates="destination_pipelines",
        foreign_keys=[destination_id],
    )
    runs: Mapped[list["PipelineRun"]] = relationship(
        back_populates="pipeline"
    )


# 3. PIPELINE RUNS
class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("pipelines.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(30), default="Running")
    trigger_type: Mapped[str] = mapped_column(String(30), default="Manual")

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)

    pipeline: Mapped["Pipeline"] = relationship(back_populates="runs")
    raw_records: Mapped[list["RawRecord"]] = relationship(
        back_populates="pipeline_run"
    )
    quality_issues: Mapped[list["QualityIssue"]] = relationship(
        back_populates="pipeline_run"
    )
    logs: Mapped[list["PipelineLog"]] = relationship(
        back_populates="pipeline_run"
    )
    warehouse_sales: Mapped[list["WarehouseSale"]] = relationship(
        back_populates="pipeline_run"
    )


# 4. RAW RECORDS
class RawRecord(Base):
    __tablename__ = "raw_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=False
    )

    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pipeline_run: Mapped["PipelineRun"] = relationship(
        back_populates="raw_records"
    )
    staging_record: Mapped["StagingSalesTransaction | None"] = relationship(
        back_populates="raw_record",
        uselist=False,
    )
    quality_issues: Mapped[list["QualityIssue"]] = relationship(
        back_populates="raw_record"
    )


# 5. STAGING SALES TRANSACTIONS
class StagingSalesTransaction(Base):
    __tablename__ = "staging_sales_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    raw_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_records.id"), nullable=False, unique=True
    )

    transaction_id: Mapped[str | None] = mapped_column(String(50))
    transaction_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    customer_id: Mapped[str | None] = mapped_column(String(50))
    product_id: Mapped[str | None] = mapped_column(String(50))
    product_name: Mapped[str | None] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int | None] = mapped_column(Integer)
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    payment_method: Mapped[str | None] = mapped_column(String(50))
    store_location: Mapped[str | None] = mapped_column(String(100))

    validation_status: Mapped[str] = mapped_column(
        String(30), default="Pending"
    )

    raw_record: Mapped["RawRecord"] = relationship(
        back_populates="staging_record"
    )


# 6. QUALITY ISSUES
class QualityIssue(Base):
    __tablename__ = "quality_issues"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=False
    )
    raw_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_records.id"), nullable=False
    )

    field: Mapped[str] = mapped_column(String(100), nullable=False)
    rule: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="Medium")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Open")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pipeline_run: Mapped["PipelineRun"] = relationship(
        back_populates="quality_issues"
    )
    raw_record: Mapped["RawRecord"] = relationship(
        back_populates="quality_issues"
    )


# 7. WAREHOUSE SALES
class WarehouseSale(Base):
    __tablename__ = "warehouse_sales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=False
    )
    raw_record_id: Mapped[int] = mapped_column(
        ForeignKey("raw_records.id"), nullable=False, unique=True
    )

    transaction_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    customer_id: Mapped[str] = mapped_column(String(50), nullable=False)
    product_id: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    store_location: Mapped[str] = mapped_column(String(100), nullable=False)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pipeline_run: Mapped["PipelineRun"] = relationship(
        back_populates="warehouse_sales"
    )


# 8. PIPELINE LOGS
class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    pipeline_run_id: Mapped[int] = mapped_column(
        ForeignKey("pipeline_runs.id"), nullable=False
    )

    level: Mapped[str] = mapped_column(String(20), nullable=False)
    component: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    pipeline_run: Mapped["PipelineRun"] = relationship(
        back_populates="logs"
    )