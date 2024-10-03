import requests
import hjson
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
from intake.source import base
from .utilities import (
    interpolate_stage_from_rating_curve,
    interpolate_flow_from_rating_curve,
    get_proper_name,
    get_nwps_location_metadata,
)
from .constants import CNRFCGauges


class HEFS(base.DataSource):
    container = "python"
    version = "0.0.1"
    name = "cnrfc_hefs"
    visualization_args = {"gauge_location": CNRFCGauges, "include_rain_melt_plot": "checkbox"}
    visualization_group = "CNRFC"
    visualization_label = "HEFS"
    visualization_type = "plotly"

    def __init__(self, gauge_location, include_rain_melt_plot, metadata=None):
        # store important kwargs
        self.gauge_location = gauge_location
        self.include_rain_melt_plot = include_rain_melt_plot
        self.data_groups = {}
        self.ymarkers = {}
        self.title = ""
        self.time_series_data = None
        self.range_xmin = None
        self.range_xmax = None
        self.range_ymin = None
        self.range_ymax = None
        self.forcing_ymin = None
        self.forcing_ymax = None
        self.plot_series = []
        self.plot_shapes = []
        self.plot_annotations = []
        self.layout = None
        self.config = None
        super(HEFS, self).__init__(metadata=metadata)

    def read(self):
        """Return a version of the xarray with all the data in memory"""
        self.get_cnrfc_hefs_data()
        self.get_config()
        self.get_layout()
        return {"data": self.plot_series, "layout": self.layout, "config": self.config}

    def get_config(self):
        self.config = dict(
            responsive=True,
            modeBarButtons=[
                ["toImage"],
                ["zoom2d", "pan2d", "zoomIn2d", "zoomOut2d"],
                ["autoScale2d", "resetScale2d"],
                ["hoverClosestCartesian", "hoverCompareCartesian"],
            ],
        )

    def get_layout(self):
        self.layout = dict(
            title={
                "text": self.title,
                "x": 0.5,
                "xanchor": "center",
                "font": {
                    "size": 15,
                },
            },
            autosize=True,
            xaxis={
                "range": [self.range_xmin, self.range_xmax],
                "type": "date",
                "tickformat": "%a<br>%b %d<br>%-I%p",
                "linecolor": "lightgray",
                "showgrid": True,
                "showline": True,
                "mirror": True,
                "nticks": 10,
                "title": {
                    "text": "<b>Observation / Forecast Time (UTC)</b>",
                },
            },
            yaxis={
                "range": [self.range_ymin * 0.99, self.range_ymax * 1.01],
                "type": "linear",
                "title": {
                    "text": "<b>Stage (Feet)</b>",
                },
                "nticks": 10,
                "linecolor": "lightgray",
                "showgrid": True,
                "showline": True,
                "mirror": True,
            },
            hovermode="x",
            hoversubplots="axis",
            images=[
                {
                    "source": "https://www.cnrfc.noaa.gov/images/NOAA_chart_bg.jpg",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.35,
                    "sizex": 1,
                    "sizey": 0.7,
                    "xanchor": "center",
                    "yanchor": "middle",
                    "layer": "below",
                },
            ],
            shapes=self.plot_shapes,
            annotations=self.plot_annotations,
            legend={
                "borderwidth": 1,
                "yanchor": "middle",
                "y": 0.5,
            },
        )

        if self.include_rain_melt_plot:
            self.layout["yaxis"]["domain"] = [0, 0.75]

            if not self.forcing_ymax:
                self.forcing_ymax = 0.5

            self.layout["yaxis3"] = dict(
                range=[self.forcing_ymin, self.forcing_ymax],
                domain=[0.8, 1],
                title={
                    "text": "<b>Rain +<br>Melt (in.)</b>",
                },
                linecolor="lightgray",
                showgrid=True,
                showline=True,
                mirror=True,
            )

        return

    def get_cnrfc_hefs_data(self):
        rating_curve_flows, rating_curve_stages = self.get_location_rating_curve()
        self.get_hefs_data(rating_curve_flows, rating_curve_stages)

        hefs_metadata = self.get_hefs_metadata()

        print(f"Getting river forecast plot data for {self.gauge_location}")
        river_forecast_plot_web = f"https://www.cnrfc.noaa.gov/graphicalRVF_printer.php?id={self.gauge_location}&scale=1"  # noqa:E501
        response = requests.get(river_forecast_plot_web)

        self.get_hydro_data(response.text)

        self.get_hydro_thresholds(
            rating_curve_flows, rating_curve_stages, response.text
        )

        if self.include_rain_melt_plot:
            self.get_forcing_data(response.text)

        location_proper_name = get_proper_name(self.gauge_location)
        self.title = f"Hourly River Level Probabilities<br>{location_proper_name}<br><b>Issuance Time</b>: {hefs_metadata['issuance_time']}"  # noqa: E501

        return

    def get_hefs_data(self, rating_curve_flows, rating_curve_stages):
        print(f"Getting HEFS plot data for {self.gauge_location}")
        try:
            unit = "feet"
            hefs_csv_url = f"https://www.cnrfc.noaa.gov/csv/{self.gauge_location}_hefs_csv_hourly_sstg.csv"  # noqa:E501
            df = pd.read_csv(hefs_csv_url)
        except Exception:
            unit = "cfs"
            hefs_csv_url = f"https://www.cnrfc.noaa.gov/csv/{self.gauge_location}_hefs_csv_hourly.csv"  # noqa:E501
            df = pd.read_csv(hefs_csv_url)
        df = df.drop(0)
        df = df.set_index("GMT")
        df = df.astype(float)
        if unit == "cfs":
            df = df * 1000
        ens_columns = [f"Ensemble {i}" for i in range(len(df.columns))]
        df.columns = ens_columns
        df_stats = df.T.quantile([0, 0.05, 0.25, 0.4, 0.6, 0.75, 0.95, 1]).T
        df_stats["mean"] = df.T.mean()
        df = df.merge(df_stats, how="left", left_index=True, right_index=True)
        dates = df.index.tolist()
        if unit == "cfs":
            df_flow = df
            df_stage = df.map(
                lambda x: interpolate_stage_from_rating_curve(
                    rating_curve_stages, rating_curve_flows, x
                )
            )
            df_flow = df_flow.reset_index()
            df_stage = df_stage.reset_index()
        else:
            df_stage = df
            df_flow = df.map(
                lambda x: interpolate_flow_from_rating_curve(
                    rating_curve_stages, rating_curve_flows, x
                )
            )
            df_flow = df_flow.reset_index()
            df_stage = df_stage.reset_index()
        del df

        for ens in ens_columns:
            self.plot_series.append(
                dict(
                    type="scatter",
                    mode="lines",
                    name="Ensembles",
                    x=dates,
                    y=df_stage[ens].tolist(),
                    line={
                        "color": "gray",
                    },
                    legendgroup="ensembles",
                    showlegend=True if ens == "Ensemble 1" else False,
                    hoverinfo=None,
                    visible="legendonly",
                )
            )

        hourly_probabilities = [
            {
                "title": "0-5% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[0.05], df_stage[0][::-1]]).tolist(),
                "color": "lightgray",
                "showlegend": True,
            },
            {
                "title": "0-5% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[1], df_stage[0.95][::-1]]).tolist(),
                "color": "lightgray",
                "showlegend": False,
            },
            {
                "title": "5-25% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[0.95], df_stage[0.75][::-1]]).tolist(),
                "color": "#B6BEFC",
                "showlegend": True,
            },
            {
                "title": "5-25% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[0.25], df_stage[0.05][::-1]]).tolist(),
                "color": "#B6BEFC",
                "showlegend": False,
            },
            {
                "title": "25-40% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[0.75], df_stage[0.6][::-1]]).tolist(),
                "color": "#FBFBCF",
                "showlegend": True,
            },
            {
                "title": "25-40% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[0.4], df_stage[0.25][::-1]]).tolist(),
                "color": "#FBFBCF",
                "showlegend": False,
            },
            {
                "title": "40-60% chance",
                "x": dates + dates[::-1],
                "y": pd.concat([df_stage[0.6], df_stage[0.4][::-1]]).tolist(),
                "color": "#F7EBA7",
                "showlegend": True,
            },
        ]

        for prob in hourly_probabilities:
            self.plot_series.append(
                dict(
                    type="scatter",
                    mode="lines",
                    fill="toself",
                    fillcolor=prob["color"],
                    name=prob["title"],
                    x=prob["x"],
                    y=prob["y"],
                    line={
                        "width": 0,
                    },
                    legendgroup="hourly_probabilities",
                    hoverinfo="none",
                    showlegend=prob["showlegend"],
                    legendgrouptitle={
                        "text": "<b>Hourly Probabilities</b>",
                    },
                    legendrank=1001,
                )
            )

        other_series = [
            {
                "title": "Minimum",
                "x": dates,
                "y": df_stage[0].tolist(),
                "text": [
                    f"<i>Minimum</i>: {round(df_stage.loc[i, 0], 2)} feet ({round(df_flow.loc[i, 0], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "Maximum",
                "x": dates,
                "y": df_stage[1].tolist(),
                "text": [
                    f"<i>Maximum</i>: {round(df_stage.loc[i, 1], 2)} feet ({round(df_flow.loc[i, 1], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "5% Percentile",
                "x": dates,
                "y": df_stage[0.05].tolist(),
                "text": [
                    f"<i>5%</i>: {round(df_stage.loc[i, .05], 2)} feet ({round(df_flow.loc[i, .05], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "25% Percentile",
                "x": dates,
                "y": df_stage[0.25].tolist(),
                "text": [
                    f"<i>25%</i>: {round(df_stage.loc[i, .25], 2)} feet ({round(df_flow.loc[i, .25], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "40% Percentile",
                "x": dates,
                "y": df_stage[0.4].tolist(),
                "text": [
                    f"<i>40%</i>: {round(df_stage.loc[i, .4], 2)} feet ({round(df_flow.loc[i, .4], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "60% Percentile",
                "x": dates,
                "y": df_stage[0.6].tolist(),
                "text": [
                    f"<i>60%</i>: {round(df_stage.loc[i, .6], 2)} feet ({round(df_flow.loc[i, .6], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "75% Percentile",
                "x": dates,
                "y": df_stage[0.75].tolist(),
                "text": [
                    f"<i>75%</i>: {round(df_stage.loc[i, .75], 2)} feet ({round(df_flow.loc[i, .75], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "95% Percentile",
                "x": dates,
                "y": df_stage[0.95].tolist(),
                "text": [
                    f"<i>95%</i>: {round(df_stage.loc[i, .95], 2)} feet ({round(df_flow.loc[i, .95], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
            {
                "title": "Ensemble Mean",
                "x": dates,
                "y": df_stage["mean"].tolist(),
                "text": [
                    f"<i>Mean</i>: {round(df_stage.loc[i, 'mean'], 2)} feet ({round(df_flow.loc[i, 'mean'], 2)} cfs)"  # noqa: E501
                    for i in range(len(dates))
                ],
            },
        ]

        for series in other_series:
            self.plot_series.append(
                dict(
                    type="scatter",
                    mode="lines",
                    name=series["title"],
                    x=series["x"],
                    y=series["y"],
                    line={
                        "color": (
                            "green" if series["title"] == "Ensemble Mean" else None
                        ),
                        "width": 2 if series["title"] == "Ensemble Mean" else 0,
                    },
                    showlegend=True if series["title"] == "Ensemble Mean" else False,
                    text=series["text"],
                    hovertemplate="%{text} <extra></extra>",
                )
            )

        self.range_ymin = (
            min(df_stage[0]) if len(df_stage[0]) <= 240 else min(df_stage[0][:239])
        )
        self.range_ymax = (
            max(df_stage[1]) if len(df_stage[1]) <= 240 else max(df_stage[1][:239])
        )
        self.range_xmax = dates[-1] if len(dates) <= 240 else dates[239]

        return

    def get_hefs_metadata(self):
        print(f"Getting HEFS metadata for {self.gauge_location}")
        hefs_plot_web = (
            f"https://www.cnrfc.noaa.gov/ensembleProduct.php?id={self.gauge_location}"
        )
        response = requests.get(hefs_plot_web)
        issuance_time_tag = re.findall(r"(Issuance Time: .*?<\/tr>)", response.text)[0]
        issuance_time_tag = issuance_time_tag.split("</td>", 1)[1]
        soup = BeautifulSoup(issuance_time_tag, "html.parser")
        issuance_time = soup.td.contents[0]

        return {"issuance_time": issuance_time}

    def get_hydro_data(self, charting_data):
        chart_series = re.findall(r"chart.addSeries\((.*),false\);", charting_data)
        all_dates = []
        hydro_ymin = None
        hydro_ymax = None
        observed_forecast_split_dt = None
        for chart_data in chart_series:
            chart_data_json = hjson.loads(chart_data)
            series_name = chart_data_json["name"]
            if not series_name:
                continue
            print(f"--> Parsing {series_name} data")
            valid_dates = []
            valid_values = []
            valid_texts = []
            for data in chart_data_json["data"]:
                valid_date = datetime.fromtimestamp(data["x"] / 1000)
                valid_dates.append(valid_date.strftime("%Y-%m-%dT%H:%M"))
                valid_values.append(data["y"])

                if data.get("flow"):
                    valid_texts.append(
                        f"<i>{series_name}</i>: {data['y']} feet ({data['flow']} cfs)"
                    )
                else:
                    valid_texts.append(f"<i>{series_name}</i>: {data['y']} feet")

                if valid_date not in all_dates:
                    all_dates.append(valid_date)

            if valid_values:
                if "Raw" in series_name:
                    plot_color = "rgb(52, 225, 235)"
                elif "Simulated" in series_name:
                    plot_color = "rgb(0, 0, 255)"
                elif "Forecast" in series_name:
                    plot_color = "rgb(25, 255, 0)"
                else:
                    plot_color = "rgb(255, 102, 255)"

                self.plot_series.append(
                    dict(
                        type="scatter",
                        mode="lines",
                        name=(
                            series_name
                            if "Observed" in series_name
                            else f"Deterministic {series_name}"
                        ),
                        x=valid_dates,
                        y=valid_values,
                        line={
                            "color": plot_color,
                        },
                        text=valid_texts,
                        hovertemplate="%{text} <extra></extra>",
                        legendrank=999,
                    )
                )

                if not hydro_ymin:
                    hydro_ymin = min(valid_values)
                else:
                    hydro_ymin = min(hydro_ymin, min(valid_values))

                if not hydro_ymax:
                    hydro_ymax = max(valid_values)
                else:
                    hydro_ymax = max(hydro_ymax, max(valid_values))

                if "Observed" in series_name:
                    observed_forecast_split_dt = valid_dates[-1]

        self.plot_shapes.append(
            dict(
                type="line",
                x0=observed_forecast_split_dt,
                x1=observed_forecast_split_dt,
                yref="paper",
                y0=0,
                y1=1,
                line={
                    "color": "black",
                },
            )
        )

        all_dates.sort()

        self.range_ymin = min(hydro_ymin, self.range_ymin)
        self.range_ymax = max(hydro_ymax, self.range_ymax)
        self.range_xmin = all_dates[0].strftime("%Y-%m-%d %H:%M:%S")

        return

    def get_hydro_thresholds(
        self, rating_curve_flows, rating_curve_stages, charting_data
    ):
        for threshold in re.findall(
            r"chart.yAxis\[0\].addPlotLine\((.*)\);", charting_data
        ):
            threshold_json = hjson.loads(threshold)
            interpolated_flow = interpolate_flow_from_rating_curve(
                rating_curve_stages, rating_curve_flows, threshold_json["value"]
            )

            self.plot_shapes.append(
                dict(
                    type="line",
                    y0=threshold_json["value"],
                    y1=threshold_json["value"],
                    xref="paper",
                    x0=0,
                    x1=1,
                    line={
                        "color": threshold_json["color"],
                        "dash": "dot",
                    },
                )
            )

            self.plot_annotations.append(
                dict(
                    showarrow=False,
                    text=f"{threshold_json['label']['text']} ({round(interpolated_flow, 2)} cfs)",  # noqa:E501
                    xref="paper",
                    x=0,
                    xanchor="left",
                    y=threshold_json["value"],
                    yanchor="bottom",
                )
            )

        return

    def get_forcing_data(self, charting_data):
        chart_series = re.findall(r"chart2.addSeries\((.*),false\);", charting_data)
        forcing_series = []
        forcing_ymin = None
        forcing_ymax = None
        for chart_data in chart_series:
            chart_data_json = hjson.loads(chart_data)
            series_name = chart_data_json["name"]
            if not series_name:
                continue
            print(f"--> Parsing {series_name} data")
            valid_dates = []
            valid_values = []
            for data in chart_data_json["data"]:
                valid_date = datetime.fromtimestamp(data[0] / 1000)
                valid_dates.append(valid_date.strftime("%Y-%m-%dT%H"))
                valid_values.append(float(data[1]))

            self.plot_series.append(
                dict(
                    type="bar",
                    name=series_name,
                    x=valid_dates,
                    y=valid_values,
                    yaxis="y3",
                    marker_color=(
                        "rgb(25, 25, 255)"
                        if "Observed" in series_name
                        else "rgb(25, 255, 0)"
                    ),
                    showlegend=False,
                    hovertemplate="<i>"
                    + series_name
                    + "</i>: %{y:.2f} inches <extra></extra>",
                )
            )

            forcing_series.append(
                {"title": series_name, "x": valid_dates, "y": valid_values}
            )
            if forcing_ymin is None:
                forcing_ymin = min(valid_values)
            else:
                forcing_ymin = min(forcing_ymin, min(valid_values))

            if forcing_ymax is None:
                forcing_ymax = max(valid_values)
            else:
                forcing_ymax = max(forcing_ymax, max(valid_values))

        self.forcing_ymin = forcing_ymin
        self.forcing_ymax = forcing_ymax

        return

    def get_location_rating_curve(self):
        print(f"Getting river rating curve data for {self.gauge_location}")
        location_rating_curve_url = (
            f"https://www.cnrfc.noaa.gov/data/ratings/{self.gauge_location}_rating.js"
        )
        response = requests.get(location_rating_curve_url)
        flows = [
            float(flow)
            for flow in re.findall(r"ratingFlow.push\((.*)\);", response.text)
        ]
        stages = [
            float(stage)
            for stage in re.findall(r"ratingStage.push\((.*)\);", response.text)
        ]

        return [flows, stages]

    def get_title(self, charting_data):
        chart_title = re.findall(r"chart2.setTitle\((.*), false\);", charting_data)[0]
        chart_titles = hjson.loads(f"[{chart_title}]")

        main_title = chart_titles[0]
        soup = BeautifulSoup(main_title["text"], "html.parser")
        main_title_text = soup.div.contents[0]

        sub_title = chart_titles[1]
        sub_title_text = sub_title["text"]
        sub_title_text = re.findall(
            r"(<b>Forecast Posted:</b> .*) <b>", sub_title_text
        )[0]

        return main_title_text + "<br>River Forecast Plot<br>" + sub_title_text
