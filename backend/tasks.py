import logging
from celery_app import celery_app
import etl
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import RequestException

logger = logging.getLogger("celery_tasks")


@celery_app.task(
    bind=True,
    name="tasks.run_etl_pipeline",
    autoretry_for=(RequestException, SQLAlchemyError),
    retry_kwargs={"max_retries": 3, "countdown": 60, "retry_backoff": True},
)
def run_etl_pipeline(self):
    """
    Celery task to run the ETL pipeline with detailed progress tracking.
    This task is scheduled to run periodically.
    """
    try:
        logger.info(f"Starting ETL pipeline task {self.request.id}")

        # Stage 1: Fetch NVD Feed (0-30%)
        self.update_state(
            state="PROGRESS", 
            meta={
                "status": "Fetching NVD feed...",
                "progress": 0,
                "stage": "fetch",
                "task_id": self.request.id
            }
        )
        logger.info(f"Task {self.request.id}: Starting fetch stage")
        fetch_metrics = etl.fetch_and_save_feed()
        
        self.update_state(
            state="PROGRESS", 
            meta={
                "status": "NVD feed fetched successfully",
                "progress": 30,
                "stage": "fetch_complete",
                "task_id": self.request.id,
                "fetch_metrics": fetch_metrics
            }
        )

        # Stage 2: Transform and Load (30-100%)
        self.update_state(
            state="PROGRESS", 
            meta={
                "status": "Transforming and loading CVE data...",
                "progress": 30,
                "stage": "transform",
                "task_id": self.request.id
            }
        )
        logger.info(f"Task {self.request.id}: Starting transform stage")
        load_metrics = etl.transform_and_load()
        
        self.update_state(
            state="PROGRESS", 
            meta={
                "status": "CVE data loaded successfully",
                "progress": 80,
                "stage": "transform_complete",
                "task_id": self.request.id,
                "load_metrics": load_metrics
            }
        )

        # Stage 3: Finalize (80-100%)
        self.update_state(
            state="PROGRESS", 
            meta={
                "status": "Finalizing ETL pipeline...",
                "progress": 90,
                "stage": "finalize",
                "task_id": self.request.id
            }
        )
        
        # Combine metrics
        pipeline_metrics = {
            "pipeline_start": fetch_metrics.get("start_time"),
            "status": "success",
            "stages": {
                "fetch": fetch_metrics,
                "load": load_metrics
            },
            "total_duration_seconds": (
                fetch_metrics.get("duration_seconds", 0) + 
                load_metrics.get("duration_seconds", 0)
            )
        }

        logger.info(f"ETL pipeline completed successfully. Task ID: {self.request.id}")

        # Final success state
        self.update_state(
            state="SUCCESS", 
            meta={
                "status": "ETL pipeline completed successfully",
                "progress": 100,
                "stage": "complete",
                "task_id": self.request.id,
                "metrics": pipeline_metrics
            }
        )

        return {"status": "success", "metrics": pipeline_metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"ETL pipeline failed. Task ID: {self.request.id}, Error: {str(e)}"
        )

        # Update task state with error
        self.update_state(
            state="FAILURE", 
            meta={
                "error": str(e),
                "status": "ETL pipeline failed",
                "task_id": self.request.id
            }
        )

        raise e


@celery_app.task(
    bind=True,
    name="tasks.fetch_nvd_feed",
    autoretry_for=(RequestException, SQLAlchemyError),
    retry_kwargs={"max_retries": 3, "countdown": 60, "retry_backoff": True},
)
def fetch_nvd_feed(self):
    """
    Celery task to fetch NVD feed only.
    """
    try:
        logger.info(f"Starting NVD feed fetch task {self.request.id}")

        self.update_state(
            state="PROGRESS", 
            meta={"status": "Fetching NVD feed...", "progress": 0}
        )

        metrics = etl.fetch_and_save_feed()

        self.update_state(
            state="SUCCESS", 
            meta={"status": "NVD feed fetched successfully", "progress": 100}
        )

        logger.info(f"NVD feed fetch completed. Task ID: {self.request.id}")

        return {"status": "success", "metrics": metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"NVD feed fetch failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
        raise Exception(
            f"NVD feed fetch failed. Task ID: {self.request.id}, Error: {str(e)}"
        )


@celery_app.task(
    bind=True,
    name="tasks.transform_and_load",
    autoretry_for=(RequestException, SQLAlchemyError),
    retry_kwargs={"max_retries": 3, "countdown": 60, "retry_backoff": True},
)
def transform_and_load(self):
    """
    Celery task to transform and load data only.
    """
    try:
        logger.info(f"Starting transform and load task {self.request.id}")

        self.update_state(
            state="PROGRESS", 
            meta={"status": "Transforming and loading data...", "progress": 0}
        )

        metrics = etl.transform_and_load()

        self.update_state(
            state="SUCCESS", 
            meta={"status": "Data transformed and loaded successfully", "progress": 100}
        )

        logger.info(f"Transform and load completed. Task ID: {self.request.id}")

        return {"status": "success", "metrics": metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"Transform and load failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
        raise Exception(
            f"Transform and load failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
