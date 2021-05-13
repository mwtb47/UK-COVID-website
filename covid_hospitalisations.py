# ======================================================================
# Script to save graphs summarising hospitalisations data as html files.
# This will be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go

class Hospitalisations:
    """Class containing methods to save two graphs as html files:
        - daily hospital admissions with covid-19
        - number of patients in hospital with covid-19
    """
    def __init__(self, template, plot_config):
        self.template = template
        self.plot_config = plot_config

    def prepare_hospital_data(self):
        """Prepare hospital data to be used in graphs."""
        hospital_url = ("https://api.coronavirus.data.gov.uk/v2/"
                        "data?areaType=overview"
                        "&metric=newAdmissions"
                        "&metric=hospitalCases"
                        "&format=csv")

        hospital = pd.read_csv(hospital_url)
        hospital['date'] = pd.to_datetime(hospital['date'], format='%Y-%m-%d')
        hospital = hospital.sort_values('date')

        # UK admissions data only available from 23rd March 2020
        hospital = hospital[hospital['date'] >= '2020-03-23']
        hospital = hospital[['date', 'newAdmissions', 'hospitalCases']]
        hospital.columns = ['date', 'admissions', 'in_hospital']

        # 7 day rolling average of admissions
        hospital['admissions_7_day'] = hospital['admissions'].rolling(
            window=7).mean()

        # Thousand comma separated strings to be displayed in labels on
        # graphs for easier reading.
        hospital['admissions_str'] = [
            "{:,}".format(x).replace(".0", "") for x in hospital['admissions']]
        hospital['admissions_7_day_str'] = [
            "{:,}".format(round(x, 2)) for x in hospital['admissions_7_day']]
        hospital['in_hospital_str'] = [
            "{:,}".format(x).replace(".0", "") for x in hospital['in_hospital']]

        self.hospital = hospital

    def graph_daily_admissions_uk(self):
        """Plot graph showing daily hospital admissions and save as an
        html file.

        File name: daily_admissions_uk.html
        """
        df = self.hospital

        fig = go.Figure()

        # UK admissions - 7 day rolling average
        fig.add_trace(
            go.Scatter(
                x=list(df['date']),
                y=list(df['admissions_7_day']),
                name="7 Day Average",
                marker=dict(color='rgb(150, 65, 65)'),
                customdata=np.stack((
                    df['admissions_7_day_str'],
                    df['admissions_str']
                ), axis=-1),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='gray',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x}</b><br>'+
                '<b>7 day avg</b>: %{customdata[0]}<br>'+
                '<b>Daily</b>: %{customdata[1]}'
            )
        )

        # UK admissions - bar plot
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['admissions']),
                name="Daily Admissions",
                marker=dict(color='rgba(150, 65, 65, 0.5)'),
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Number of People Admitted to Hospital Each day</b>"
                   "<br><sub>Source: gov.uk"),
            yaxis_separatethousands=True,
            height=600,
            margin=dict(t=70),
            legend=dict(
                orientation='h',
                x=0.5,
                xanchor='center'
            )
        )

        fig.write_html('graphs/admissions/daily_admissions_uk.html',
                       config=self.plot_config)

    def graph_in_hospital_uk(self):
        """Plot graph showing patients in hospital and save as an html
        file.

        File name: in_hospital_uk.html
        """
        df = self.hospital

        fig = go.Figure()

        # UK COVID-19 patients - bar plot
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['in_hospital']),
                marker=dict(color='rgba(150, 65, 65, 0.8)'),
                text=df['in_hospital_str'],
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='gray',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x}</b><br>'+
                '<b>Patients</b>: %{text}<br>'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Total Number of Confirmed COVID-19 Patients in Hospital"
                   "</b><br><sub>Note - the definition of a COVID-19 patient "
                   "differs between England, Wales, Scotland and Northern "
                   "Ireland.<br>Source: gov.uk"),
            height=600,
            margin=dict(t=100),
            legend=dict(
                orientation='h',
                x=0.5,
                xanchor='center'
            )
        )

        fig.write_html('graphs/admissions/in_hospital_uk.html',
                       config=self.plot_config)


def main(template, plot_config):
    """Initiate Hospitalisations class and run methods to plot graphs.
    """
    hospital = Hospitalisations(template, plot_config)
    hospital.prepare_hospital_data()
    hospital.graph_daily_admissions_uk()
    hospital.graph_in_hospital_uk()
