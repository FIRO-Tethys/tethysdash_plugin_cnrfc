from intake.source import base


class DailyBriefing(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_daily_briefing"
    visualization_args = {}
    visualization_group = "CNRFC"
    visualization_label = "Daily Briefing"
    visualization_type = "image"

    def __init__(self, metadata=None):
        # store important kwargs
        super(DailyBriefing, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""

        return "https://www.cnrfc.noaa.gov/images/dailyBriefing/dailyBriefing.png"
