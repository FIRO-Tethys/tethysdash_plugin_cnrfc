from setuptools import setup, find_packages

INSTALL_REQUIRES = ["intake >=0.6.6", "requests"]

setup(
    name="aquainsight_plugin_cnrfc",
    version="0.0.1",
    description="CNRFC visualizations plugin for aquainsight",
    url="https://github.com/FIRO-Tethys/aquainsight_plugin_cnrfc",
    maintainer="Corey Krewson",
    maintainer_email="ckrewson@aquaveo.com",
    license="BSD",
    py_modules=["aquainsight_plugin_cnrfc"],
    packages=find_packages(),
    entry_points={
        "intake.drivers": [
            "cnrfc_impact_statements = cnrfc_visualizations.impact_statements:ImpactStatements",  # noqa:E501
            "cnrfc_10day_streamflow_volume_accumulation = cnrfc_visualizations.10day_streamflow_volume_accumulation:StreamflowVolumeAccumulation",  # noqa:E501
            "cnrfc_10day_hourly_maximum_streamflow_probability = cnrfc_visualizations.10day_hourly_maximum_streamflow_probability:MaximumFlowProbability",  # noqa:E501
            "cnrfc_10day_daily_maximum_streamflow_probability = cnrfc_visualizations.10day_daily_maximum_streamflow_probability:MaximumFlowProbability",  # noqa:E501
            "cnrfc_monthly_streamflow_volume_exceedance = cnrfc_visualizations.monthly_streamflow_volume_exceedance:StreamflowVolumeExceedance",  # noqa:E501
            "cnrfc_5day_streamflow_volume_exceedance = cnrfc_visualizations.5day_streamflow_volume_exceedance:VolumeExceedance",  # noqa:E501
            "cnrfc_daily_briefing = cnrfc_visualizations.daily_briefing:DailyBriefing",
            "cnrfc_hefs = cnrfc_visualizations.hefs:HEFS",
        ]
    },
    package_data={"": ["*.csv", "*.yml", "*.html"]},
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
)
