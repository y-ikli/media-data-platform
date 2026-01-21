"""Abstract base class for marketing data source connectors."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid
import logging
import os
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

logger = logging.getLogger(__name__)


class DataSourceConnector(ABC):
    """
    Abstract base class defining the contract for all data source connectors.
    
    Each connector must implement:
    - `extract()`: raw data extraction
    
    Methods `load_raw()`, `write_to_bigquery()` and `run()` are provided and reusable.
    """
    
    def __init__(self, source_name: str, project_id: str = None):
        """
        Initialize the connector.
        
        Args:
            source_name: Unique source identifier (ex: "google_ads", "meta_ads")
            project_id: GCP project ID for BigQuery (optional, reads from settings.yaml or env)
        """
        self.source_name = source_name
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID", "data-pipeline-platform-484814")
        self.dataset_id = "mdp_raw"
        self.bq_client = None
    
    @abstractmethod
    def extract(self, start_date: str, end_date: str) -> list[dict]:
        """
        Extract raw data from the source.
        
        This method MUST be implemented by each subclass.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of dictionaries containing raw data filtered by date
        """
        pass
    
    def load_raw(self, rows: list[dict]) -> list[dict]:
        """
        Enrich raw data with ingestion metadata.
        
        Adds:
        - ingested_at: UTC timestamp of ingestion
        - extract_run_id: Unique UUID to trace extraction run
        - source: source identifier
        
        This method is reusable across all sources.
        
        Args:
            rows: List of dictionaries containing raw data
        
        Returns:
            List enriched with ingestion metadata
        """
        run_id = str(uuid.uuid4())
        ingested_at = datetime.now(tz=timezone.utc).isoformat()
        
        enriched = []
        for row in rows:
            enriched.append(
                {
                    **row,
                    "ingested_at": ingested_at,
                    "extract_run_id": run_id,
                    "source": self.source_name,
                }
            )
        return enriched
    
    def run(self, start_date: str, end_date: str) -> list[dict]:
        """
        Execute the complete pipeline: extract → enrich → load to BigQuery.
        
        This method orchestrates steps and is identical for all sources.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of enriched dictionaries ready for raw zone
        """
        # Extract raw data
        rows = self.extract(start_date, end_date)
        logger.info("Extracted %d rows from %s", len(rows), self.source_name)
        
        # Enrich with metadata
        enriched_rows = self.load_raw(rows)
        logger.info("Enriched %d rows with metadata", len(enriched_rows))
        
        # Load to BigQuery
        if enriched_rows:
            self.write_to_bigquery(enriched_rows)
            logger.info("Successfully loaded %d rows to BigQuery", len(enriched_rows))
        
        return enriched_rows
    
    def get_bigquery_client(self) -> bigquery.Client:
        """
        Get or create BigQuery client.
        
        Returns:
            Initialized BigQuery client
        """
        if self.bq_client is None:
            self.bq_client = bigquery.Client(project=self.project_id)
        return self.bq_client
    
    def write_to_bigquery(self, rows: list[dict]) -> None:
        """
        Write enriched data to BigQuery raw dataset.
        
        Automatically creates table if it doesn't exist.
        
        Args:
            rows: List of enriched dictionaries
        
        Raises:
            Exception: If BigQuery write fails
        """
        if not rows:
            logger.warning("No rows to write to BigQuery")
            return
        
        client = self.get_bigquery_client()
        
        # Determine table name based on source
        table_name = f"{self.source_name}_campaign_daily"
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        logger.info("Writing %d rows to %s", len(rows), table_id)
        
        # Configure write job (append mode, create table if needed)
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
            autodetect=True,  # Auto-detect schema from data
        )
        
        try:
            # Load data to BigQuery
            load_job = client.load_table_from_json(
                rows,
                table_id,
                job_config=job_config,
            )
            load_job.result()  # Wait for job to complete
            logger.info("✓ Successfully loaded %d rows to %s", load_job.output_rows, table_id)
        except Exception as e:
            logger.error("✗ Failed to load data to BigQuery: %s", str(e))
            raise