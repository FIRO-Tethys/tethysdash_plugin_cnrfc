from intake.source import base
from .constants import CNRFCGauges, CNRFCEnsembleBaseUrl


class VolumeExceedance(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_5day_streamflow_volume_exceedance"
    visualization_tags = [
        "cnrfc",
        "5 day",
        "streamflow",
        "volume",
        "exceedance",
    ]
    visualization_description = "Depicts the daily streamflow volume accumulation for the next 5 days and compares values to exceedance probabilities. More information can be found at https://www.cnrfc.noaa.gov/ensembleProduct.php"
    visualization_args = {
        "gauge_location": CNRFCGauges,
    }
    visualization_group = "CNRFC"
    visualization_label = "5 Day Streamflow Volume Exceedance"
    visualization_type = "image"

    def __init__(self, gauge_location, metadata=None):
        # store important kwargs
        self.gauge_location = gauge_location
        super(VolumeExceedance, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""

        return CNRFCEnsembleBaseUrl + self.gauge_location + ".ens_4x5day.png"
