from intake.source import base
from .constants import CNRFCGauges, CNRFCEnsembleBaseUrl


class MaximumFlowProbability(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_10day_hourly_maximum_streamflow_probability"
    visualization_tags = [
        "cnrfc",
        "10 day",
        "hourly",
        "streamflow",
        "probability",
        "ensemble",
        "maximum",
    ]
    visualization_description = "Depicts the probabilities for the hourly maximum streamflow for the next 10 days. More information can be found at https://www.cnrfc.noaa.gov/ensembleProduct.php"
    visualization_args = {
        "gauge_location": CNRFCGauges,
    }
    visualization_group = "CNRFC"
    visualization_label = "10-Day Hourly Maximum Streamflow Probability"
    visualization_type = "image"
    visualization_attribution = "CNRFC"

    def __init__(self, gauge_location, metadata=None):
        # store important kwargs
        self.gauge_location = gauge_location
        super(MaximumFlowProbability, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""

        return CNRFCEnsembleBaseUrl + self.gauge_location + ".ens_boxwhisker.png"
