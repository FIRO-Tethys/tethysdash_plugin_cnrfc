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
        ]
    },
    package_data={"": ["*.csv", "*.yml", "*.html"]},
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
)
