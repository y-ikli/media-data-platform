"""Abstract base class for marketing data source connectors."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid


class DataSourceConnector(ABC):
    """
    Abstract base class defining the contract for all data source connectors.
    
    Each connector must implement:
    - `extract()`: raw data extraction
    
    Methods `load_raw()` and `run()` are provided and reusable.
    """
    
    def __init__(self, source_name: str):
        """
        Initialize the connector.
        
        Args:
            source_name: Unique source identifier (ex: "google_ads", "meta_ads")
        """
        self.source_name = source_name
    
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
        Execute the complete pipeline: extract → enrich.
        
        This method orchestrates steps and is identical for all sources.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (inclusive)
        
        Returns:
            List of enriched dictionaries ready for raw zone
        """
        rows = self.extract(start_date, end_date)
        enriched_rows = self.load_raw(rows)
        return enriched_rows

