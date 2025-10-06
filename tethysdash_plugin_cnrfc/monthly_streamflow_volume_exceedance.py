from intake.source import base
from .constants import CNRFCGauges, CNRFCEnsembleBaseUrl


class StreamflowVolumeExceedance(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_monthly_streamflow_volume_exceedance"
    visualization_tags = [
        "cnrfc",
        "monthly",
        "volume",
        "streamflow",
        "ensemble",
        "accumulation",
    ]
    visualization_description = "Depicts the total streamflow volume accumulation (deterministic and ensembles) for the next month. More information can be found at https://www.cnrfc.noaa.gov/ensembleProduct.php"
    visualization_args = {
        "gauge_location": CNRFCGauges,
    }
    visualization_group = "CNRFC"
    visualization_label = "Monthly Streamflow Volume Exceedance"
    visualization_type = "image"
    visualization_attribution = "CNRFC"

    def __init__(self, gauge_location, metadata=None):
        # store important kwargs
        self.gauge_location = gauge_location
        super(StreamflowVolumeExceedance, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""

        return CNRFCEnsembleBaseUrl + self.gauge_location + ".ens_monthly.png"
