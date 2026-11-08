import csv
import io
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine, get_db
from app.database.models import (
    DataSource,
    Pipeline,
    PipelineRun,
    RawRecord,
    PipelineLog,
)

from collections import Counter
from decimal import Decimal, InvalidOperation

from app.database.models import (
    StagingSalesTransaction,
    QualityIssue,
    WarehouseSale,
)

from app.routers.api import router as api_router

app = FastAPI(
    title="RetailFlow API",
    description="Retail Data Pipeline Management Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to RetailFlow API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

#temp
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "RetailFlow API",
        "database": "PostgreSQL"
    }


@app.get("/db-health")
def database_health_check():
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()

        return {
            "status": "connected",
            "database": "retailflow_db",
            "test_query": value
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )


@app.post("/api/ingestion/sales-csv")
def upload_sales_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Check the uploaded file
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file."
        )

    # 2. Read and parse the CSV
    try:
        contents = file.file.read()
        csv_text = contents.decode("utf-8-sig")

        reader = csv.DictReader(io.StringIO(csv_text))

        required_columns = {
            "transaction_id",
            "transaction_date",
            "customer_id",
            "product_id",
            "product_name",
            "category",
            "quantity",
            "unit_price",
            "total_amount",
            "payment_method",
            "store_location",
        }

        if not reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="The CSV file is empty or has no header row."
            )

        missing_columns = required_columns - set(reader.fieldnames)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing CSV columns: {', '.join(sorted(missing_columns))}"
            )

        rows = list(reader)

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="The CSV file contains no transaction records."
            )

        if any(None in row for row in rows):
            raise HTTPException(
                status_code=400,
                detail="The CSV contains rows with more values than headers."
            )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the CSV. Please use UTF-8 encoding."
        )

    # 3. Register the data source
    try:
        source = db.query(DataSource).filter(
            DataSource.name == "Sales Transactions CSV"
        ).first()

        if not source:
            source = DataSource(
                name="Sales Transactions CSV",
                source_type="CSV",
                status="Connected"
            )
            db.add(source)

        #Update the last sync timestamp
        source.last_sync_at = datetime.now(timezone.utc)    

        destination = db.query(DataSource).filter(
            DataSource.name == "RetailFlow PostgreSQL Warehouse"
        ).first()

        if not destination:
            destination = DataSource(
                name="RetailFlow PostgreSQL Warehouse",
                source_type="Database",
                status="Connected"
            )
            db.add(destination)

        db.flush()

        # 4. Find or create the pipeline
        pipeline = db.query(Pipeline).filter(
            Pipeline.name == "Sales Transactions ETL"
        ).first()

        if not pipeline:
            pipeline = Pipeline(
                name="Sales Transactions ETL",
                source_id=source.id,
                destination_id=destination.id,
                status="Running"
            )
            db.add(pipeline)
        else:
            pipeline.source_id = source.id
            pipeline.destination_id = destination.id
            pipeline.status = "Running"

        db.flush()

        # 5. Create a pipeline execution
        pipeline_run = PipelineRun(
            pipeline_id=pipeline.id,
            status="Running",
            trigger_type="Manual"
        )

        db.add(pipeline_run)
        db.flush()

        db.add(PipelineLog(
            pipeline_run_id=pipeline_run.id,
            level="INFO",
            component="extractor",
            message="CSV extraction started."
        ))

        # 6. Preserve the original CSV rows
        raw_records = [
            RawRecord(
                pipeline_run_id=pipeline_run.id,
                row_number=index,
                raw_data=row
            )
            for index, row in enumerate(rows, start=1)
        ]

        db.add_all(raw_records)

        # 7. Update execution details
        pipeline_run.records_processed = len(raw_records)
        pipeline_run.records_failed = 0
        pipeline_run.status = "Success"
        pipeline_run.completed_at = datetime.now(timezone.utc)

        pipeline.status = "Success"

        db.add(PipelineLog(
            pipeline_run_id=pipeline_run.id,
            level="INFO",
            component="extractor",
            message=f"Successfully extracted {len(raw_records)} CSV records."
        ))

        db.commit()

        return {
            "message": "CSV uploaded and extracted successfully.",
            "filename": file.filename,
            "pipeline": pipeline.name,
            "pipeline_run_id": pipeline_run.id,
            "records_extracted": len(raw_records),
            "status": pipeline_run.status
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to save CSV records to the database."
        )

@app.post("/api/pipelines/runs/{run_id}/transform")
def transform_sales(
    run_id: int,
    db: Session = Depends(get_db)
):
    # 1. Find the pipeline execution
    pipeline_run = db.query(PipelineRun).filter(
        PipelineRun.id == run_id
    ).first()

    if not pipeline_run:
        raise HTTPException(
            status_code=404,
            detail="Pipeline run not found."
        )

    if pipeline_run.status not in ["Success", "Warning"]:
        raise HTTPException(
            status_code=400,
            detail="Only successfully extracted runs can be transformed."
        )

    # Prevent accidentally processing the same run twice
    existing_staging = (
        db.query(StagingSalesTransaction)
        .join(
            RawRecord,
            StagingSalesTransaction.raw_record_id == RawRecord.id
        )
        .filter(RawRecord.pipeline_run_id == run_id)
        .first()
    )

    if existing_staging:
        raise HTTPException(
            status_code=409,
            detail="This pipeline run has already been transformed."
        )

    raw_records = (
        db.query(RawRecord)
        .filter(RawRecord.pipeline_run_id == run_id)
        .order_by(RawRecord.row_number)
        .all()
    )

    if not raw_records:
        raise HTTPException(
            status_code=400,
            detail="No raw records found for this pipeline run."
        )

    # 2. Identify duplicate transaction IDs
    transaction_ids = [
        str(record.raw_data.get("transaction_id", "")).strip()
        for record in raw_records
    ]

    id_counts = Counter(
        transaction_id
        for transaction_id in transaction_ids
        if transaction_id
    )

    # 3. Prepare the validation rules
    allowed_payment_methods = {
        "Cash",
        "GCash",
        "Maya",
        "Credit Card",
        "Debit Card",
    }

    valid_records = 0
    failed_records = 0
    total_issues = 0

    try:
        for record in raw_records:
            data = record.raw_data
            issues = []

            # Helper: clean text values
            def clean_text(value):
                if value is None:
                    return None

                cleaned = str(value).strip()
                return cleaned if cleaned else None

            # Helper: record a quality issue
            def add_issue(field, rule, severity, message):
                issues.append({
                    "field": field,
                    "rule": rule,
                    "severity": severity,
                    "message": message,
                })

            # 4. Clean text fields
            transaction_id = clean_text(data.get("transaction_id"))
            customer_id = clean_text(data.get("customer_id"))
            product_id = clean_text(data.get("product_id"))
            product_name = clean_text(data.get("product_name"))
            category = clean_text(data.get("category"))
            payment_method = clean_text(data.get("payment_method"))
            store_location = clean_text(data.get("store_location"))

            # 5. Validate required fields
            required_fields = {
                "transaction_id": transaction_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "product_name": product_name,
                "category": category,
                "payment_method": payment_method,
                "store_location": store_location,
            }

            for field, value in required_fields.items():
                if not value:
                    add_issue(
                        field,
                        "Required field",
                        "High",
                        f"{field} is missing or empty."
                    )

            # 6. Validate duplicate transaction IDs
            if transaction_id and id_counts[transaction_id] > 1:
                add_issue(
                    "transaction_id",
                    "Uniqueness check",
                    "Critical",
                    f"Duplicate transaction ID: {transaction_id}."
                )

            # 7. Parse and validate transaction date
            transaction_date = None

            try:
                date_value = clean_text(data.get("transaction_date"))

                if not date_value:
                    raise ValueError("Date is empty.")

                transaction_date = datetime.fromisoformat(date_value)

            except ValueError:
                add_issue(
                    "transaction_date",
                    "Date validation",
                    "High",
                    "Invalid transaction date."
                )

            # 8. Parse and validate quantity
            quantity = None

            try:
                quantity_value = clean_text(data.get("quantity"))

                if not quantity_value:
                    raise ValueError("Quantity is empty.")

                quantity = int(quantity_value)

                if quantity <= 0:
                    add_issue(
                        "quantity",
                        "Positive value check",
                        "High",
                        "Quantity must be greater than zero."
                    )

            except ValueError:
                quantity = None

                if not any(
                    issue["field"] == "quantity" for issue in issues
                ):
                    add_issue(
                        "quantity",
                        "Integer validation",
                        "High",
                        "Quantity must be a valid integer."
                    )

            # 9. Parse and validate unit price
            unit_price = None

            try:
                unit_price_value = clean_text(data.get("unit_price"))

                if not unit_price_value:
                    raise ValueError("Unit price is empty.")

                unit_price = Decimal(unit_price_value)

                if unit_price <= 0:
                    add_issue(
                        "unit_price",
                        "Positive value check",
                        "High",
                        "Unit price must be greater than zero."
                    )

            except (ValueError, InvalidOperation):
                unit_price = None

                if not any(
                    issue["field"] == "unit_price" for issue in issues
                ):
                    add_issue(
                        "unit_price",
                        "Numeric validation",
                        "High",
                        "Unit price must be a valid number."
                    )

            # 10. Parse and validate total amount
            total_amount = None

            try:
                total_value = clean_text(data.get("total_amount"))

                if not total_value:
                    raise ValueError("Total amount is empty.")

                total_amount = Decimal(total_value)

            except (ValueError, InvalidOperation):
                total_amount = None

                add_issue(
                    "total_amount",
                    "Numeric validation",
                    "High",
                    "Total amount must be a valid number."
                )

            if (
                quantity is not None
                and unit_price is not None
                and total_amount is not None
                and total_amount != quantity * unit_price
            ):
                add_issue(
                    "total_amount",
                    "Calculation validation",
                    "High",
                    "Total amount does not match quantity multiplied by unit price."
                )

            # 11. Validate payment method
            if (
                payment_method
                and payment_method not in allowed_payment_methods
            ):
                add_issue(
                    "payment_method",
                    "Allowed values check",
                    "Medium",
                    f"Unsupported payment method: {payment_method}."
                )

            # 12. Save the parsed record into staging
            staging_record = StagingSalesTransaction(
                raw_record_id=record.id,
                transaction_id=transaction_id,
                transaction_date=transaction_date,
                customer_id=customer_id,
                product_id=product_id,
                product_name=product_name,
                category=category,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount,
                payment_method=payment_method,
                store_location=store_location,
                validation_status="Failed" if issues else "Passed",
            )

            db.add(staging_record)

            # 13. Save every quality issue
            for issue in issues:
                db.add(QualityIssue(
                    pipeline_run_id=run_id,
                    raw_record_id=record.id,
                    field=issue["field"],
                    rule=issue["rule"],
                    severity=issue["severity"],
                    message=issue["message"],
                    status="Open",
                ))

            total_issues += len(issues)

            # 14. Only valid records enter the warehouse
            if issues:
                failed_records += 1
            else:
                db.add(WarehouseSale(
                    pipeline_run_id=run_id,
                    raw_record_id=record.id,
                    transaction_id=transaction_id,
                    transaction_date=transaction_date,
                    customer_id=customer_id,
                    product_id=product_id,
                    product_name=product_name,
                    category=category,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_amount=total_amount,
                    payment_method=payment_method,
                    store_location=store_location,
                ))

                valid_records += 1

        # 15. Update execution results
        pipeline_run.records_processed = valid_records
        pipeline_run.records_failed = failed_records
        pipeline_run.status = (
            "Warning" if failed_records > 0 else "Success"
        )
        pipeline_run.completed_at = datetime.now(timezone.utc)

        pipeline_run.pipeline.status = pipeline_run.status

        db.add(PipelineLog(
            pipeline_run_id=run_id,
            level="WARNING" if failed_records else "INFO",
            component="transformer",
            message=(
                f"Transformation completed. "
                f"{valid_records} valid records, "
                f"{failed_records} failed records, "
                f"{total_issues} quality issues."
            )
        ))

        db.commit()

        return {
            "message": "Transformation completed.",
            "pipeline_run_id": run_id,
            "total_records": len(raw_records),
            "valid_records": valid_records,
            "failed_records": failed_records,
            "quality_issues": total_issues,
            "status": pipeline_run.status,
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database error occurred during transformation."
        )