"""Application health monitoring service."""
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ApplicationState:
    """Global application state for health monitoring."""
    
    # Application lifecycle
    app_start_time: float = field(default_factory=time.time)
    
    # Collection metrics
    last_collection_time: Optional[datetime] = None
    collections_succeeded: int = 0
    collections_failed: int = 0
    
    # Database health
    database_connected: bool = False
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return time.time() - self.app_start_time
    
    def get_data_freshness_minutes(self) -> Optional[float]:
        """Get minutes since last successful data collection."""
        if self.last_collection_time is None:
            return None
        
        delta = datetime.utcnow() - self.last_collection_time
        return delta.total_seconds() / 60.0


# Global application state singleton
app_state = ApplicationState()
