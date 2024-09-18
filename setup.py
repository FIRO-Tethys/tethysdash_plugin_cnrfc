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
            "cnrfc_impact_statements = cnrfc_visualizations.impact_statements:ImpactStatements",
            "cnrfc_10day_accumulated_volume = cnrfc_visualizations.10day_accumulated_volume:AccumulatedVolume",
            "cnrfc_10day_maximum_flow_probability = cnrfc_visualizations.10day_maximum_flow_probability:MaximumFlowProbability",
            "cnrfc_daily_maximum_flow_probability = cnrfc_visualizations.daily_maximum_flow_probability:MaximumFlowProbability",
            "cnrfc_monthly_volume_exceedance = cnrfc_visualizations.monthly_volume_exceedance:VolumeExceedance",
            "cnrfc_5day_volume_exceedance_levels = cnrfc_visualizations.5day_volume_exceedance_levels:VolumeExceedance",
            "cnrfc_daily_briefing = cnrfc_visualizations.daily_briefing:DailyBriefing",
        ]
    },
    package_data={"": ["*.csv", "*.yml", "*.html"]},
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
)
