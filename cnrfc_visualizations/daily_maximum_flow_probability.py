from intake.source import base
from .constants import CNRFCGauges, CNRFCEnsembleBaseUrl


class MaximumFlowProbability(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_daily_maximum_flow_probability"
    visualization_args = {
        "gauge_location": CNRFCGauges,
    }
    visualization_group = "CNRFC"
    visualization_label = "Daily Maximum Flow Probability"
    visualization_type = "image"

    def __init__(self, gauge_location, metadata=None):
        # store important kwargs
        self.gauge_location = gauge_location
        super(MaximumFlowProbability, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""

        return CNRFCEnsembleBaseUrl + self.gauge_location + ".ens_10day.png"