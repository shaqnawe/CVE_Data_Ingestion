import logging
from celery import current_task
from celery_app import celery_app
import etl

logger = logging.getLogger("celery_tasks")


@celery_app.task(bind=True, name="tasks.run_etl_pipeline")
def run_etl_pipeline(self):
    """
    Celery task to run the ETL pipeline.
    This task is scheduled to run periodically.
    """
    try:
        logger.info(f"Starting ETL pipeline task {self.request.id}")

        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "Running ETL pipeline..."})

        # Run the ETL pipeline
        metrics = etl.run_etl_pipeline()

        logger.info(f"ETL pipeline completed successfully. Task ID: {self.request.id}")

        return {"status": "success", "metrics": metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"ETL pipeline failed. Task ID: {self.request.id}, Error: {str(e)}"
        )

        # Update task state with error
        self.update_state(state="FAILURE", meta={"error": str(e)})

        raise e


@celery_app.task(bind=True, name="tasks.fetch_nvd_feed")
def fetch_nvd_feed(self):
    """
    Celery task to fetch NVD feed only.
    """
    try:
        logger.info(f"Starting NVD feed fetch task {self.request.id}")

        metrics = etl.fetch_and_save_feed()

        logger.info(f"NVD feed fetch completed. Task ID: {self.request.id}")

        return {"status": "success", "metrics": metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"NVD feed fetch failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
        raise Exception(
            f"NVD feed fetch failed. Task ID: {self.request.id}, Error: {str(e)}"
        )


@celery_app.task(bind=True, name="tasks.transform_and_load")
def transform_and_load(self):
    """
    Celery task to transform and load data only.
    """
    try:
        logger.info(f"Starting transform and load task {self.request.id}")

        metrics = etl.transform_and_load()

        logger.info(f"Transform and load completed. Task ID: {self.request.id}")

        return {"status": "success", "metrics": metrics, "task_id": self.request.id}

    except Exception as e:
        logger.error(
            f"Transform and load failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
        raise Exception(
            f"Transform and load failed. Task ID: {self.request.id}, Error: {str(e)}"
        )
