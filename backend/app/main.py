from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import engine

app = FastAPI(
    title="RetailFlow API",
    description="Retail Data Pipeline Management Platform",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to RetailFlow API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/db-health")
def database_health_check():
    try:
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