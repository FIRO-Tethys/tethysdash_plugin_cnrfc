from intake.source import base
from .constants import (
    CNRFCGauges
)
from .utilities import get_nwps_location_metadata


class ImpactStatements(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_impact_statements"
    visualization_args = {
        "gauge_location": CNRFCGauges,
    }
    visualization_group = "CNRFC"
    visualization_label = "Impact Statements"
    visualization_type = "table"

    def __init__(self, gauge_location, metadata=None):
        # store important kwargs
        self.gauge_location = gauge_location
        super(ImpactStatements, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""

        
        metadata = get_nwps_location_metadata(self.gauge_location)
        impact_statements = metadata["flood"].get("impacts", [{}])
        title = f"{self.gauge_location} Impact Statements"
        
        
        
        return {"title": title, "data": impact_statements}
