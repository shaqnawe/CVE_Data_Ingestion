import logging
from backend.celery_app import celery_app
from backend.etl import run_etl_pipeline, fetch_and_save_feed, transform_and_load
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import RequestException

logger = logging.getLogger("celery_tasks")


@celery_app.task(
    bind=True,
    name="tasks.run_etl_pipeline",
    autoretry_for=(RequestException, SQLAlchemyError),
    retry_kwargs={"max_retries": 3, "countdown": 60, "retry_backoff": True},
)
def run_etl_pipeline_task(self):
    """
    Celery task to run the ETL pipeline with detailed progress tracking.
    This task is scheduled to run periodically.
    """
    try:
        logger.info(f"Starting ETL pipeline task {self.request.id}")
        pipeline_metrics = run_etl_pipeline(triggered_by="celery-beat")
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "ETL pipeline completed successfully",
                "progress": 100,
                "stage": "complete",
                "task_id": self.request.id,
                "metrics": pipeline_metrics,
            },
        )
        return {
            "status": "success",
            "metrics": pipeline_metrics,
            "task_id": self.request.id,
        }
    except Exception as e:
        logger.error(
            f"ETL pipeline failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "status": "ETL pipeline failed",
                "task_id": self.request.id,
            },
        )
        raise e


@celery_app.task(
    bind=True,
    name="tasks.fetch_nvd_feed",
    autoretry_for=(RequestException, SQLAlchemyError),
    retry_kwargs={"max_retries": 3, "countdown": 60, "retry_backoff": True},
)
def fetch_nvd_feed_task(self):
    """
    Celery task to fetch NVD feed only.
    """
    try:
        logger.info(f"Starting NVD feed fetch task {self.request.id}")

        self.update_state(
            state="PROGRESS", meta={"status": "Fetching NVD feed...", "progress": 0}
        )

        metrics = fetch_and_save_feed()

        self.update_state(
            state="SUCCESS",
            meta={"status": "NVD feed fetched successfully", "progress": 100},
        )

        logger.info(f"NVD feed fetch completed. Task ID: {self.request.id}")

        return {"status": "success", "metrics": metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"NVD feed fetch failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
        raise Exception(
            f"NVD feed fetch failed. Task ID: {self.request.id}, Error: {str(e)}"
        ) from e


@celery_app.task(
    bind=True,
    name="tasks.transform_and_load",
    autoretry_for=(RequestException, SQLAlchemyError),
    retry_kwargs={"max_retries": 3, "countdown": 60, "retry_backoff": True},
)
def transform_and_load_task(self):
    """
    Celery task to transform and load data only.
    """
    try:
        logger.info(f"Starting transform and load task {self.request.id}")

        self.update_state(
            state="PROGRESS",
            meta={"status": "Transforming and loading data...", "progress": 0},
        )

        metrics = transform_and_load()

        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Data transformed and loaded successfully",
                "progress": 100,
            },
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
