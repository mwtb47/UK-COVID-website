# ======================================================================
# Script to save graphs summarising deaths data as html files. This will
# be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class DeathsData:
    """Class containing methods to prepare data on:
        - daily deaths
        - daily deaths by region
        - deaths by council in the past 7 days
    """
    def __init__(self, population):
        self.population = population

    def prepare_deaths_data(self):
        """Prepare deaths data to be used in graphs."""
        deaths_url = ("https://api.coronavirus.data.gov.uk/v2/"
                      "data?areaType=overview"
                      "&metric=newDeaths28DaysByDeathDate"
                      "&format=csv")

        deaths = pd.read_csv(deaths_url)
        deaths['date'] = pd.to_datetime(deaths['date'], format='%Y-%m-%d')
        deaths = deaths.sort_values('date')

        # Date is only available from the 6th March 2020
        deaths = deaths[deaths['date'] >= '2020-03-06']
        deaths = deaths [['date', 'newDeaths28DaysByDeathDate']]
        deaths.columns = ['date', 'deaths']

        # 7 day rolling averages for daily deaths
        deaths['deaths_7_day'] = deaths['deaths'].rolling(window=7).mean()

        # Thousand comma separated strings to be displayed in labels on
        # graphs for easier reading.
        deaths['deaths_str'] = ["{:,}".format(x).replace(".0", "")
                                for x in deaths['deaths']]
        deaths['deaths_7_day_str'] = ["{:,}".format(round(x, 2))
                                      for x in deaths['deaths_7_day']]

        # 5 most recent days in grey as the data is incomplete
        deaths['color'] = (
            ['rgba(150, 65, 65, 0.5)'] * (len(deaths.index) - 5)
            + ['rgb(200, 200, 200)'] * 5)

        return deaths

    def prepare_regional_deaths_data(self):
        """Download and prepare deaths data for the 9 regions of England.
        """
        regional_url = ("https://api.coronavirus.data.gov.uk/v2/"
                        "data?areaType=region"
                        "&metric=newDeaths28DaysByDeathDate"
                        "&format=csv")

        regional = pd.read_csv(regional_url)
        regional['date'] = pd.to_datetime(regional['date'], format='%Y-%m-%d')
        regional = regional.sort_values('date')
        regional.columns = ['area_code', 'area_name', 'area_type',  'date',
                            'deaths']

        # 7 day rolling average for deaths and daily deaths.
        grouped_regions = regional.groupby(['area_name', 'area_code'],
                                           as_index=False)
        regional['deaths_7_day'] = grouped_regions[['deaths']].apply(
            lambda x: x.rolling(window=7, min_periods=1).mean())

        # Population totals by region
        self.regional_pop = self.population.groupby(
            'Code', as_index=False)['population'].sum()

        regional = regional.merge(
            self.regional_pop,
            left_on='area_code',
            right_on='Code',
            how='left')

        regional['deaths_per_100k'] = (regional['deaths_7_day']
                                       / regional['population'] * 100000)

        # Create thousand commas separated strings to use in the plots
        # as they are easier to read.
        for c in ['deaths_7_day', 'deaths_per_100k']:
            regional[c + '_str'] = ["{:,}".format(round(x, 2))
                                    for x in regional[c]]

        return regional

    def prepare_council_deaths_data(self):
        """Download and prepare deaths data for each of England's
        councils.
        """
        council_url = ("https://api.coronavirus.data.gov.uk/v2/"
                       "data?areaType=ltla"
                       "&metric=newDeaths28DaysByDeathDate"
                       "&format=csv")
        council = pd.read_csv(council_url)
        council['date'] = pd.to_datetime(council['date'], format='%Y-%m-%d')
        council = council.sort_values('date')
        council.columns = ['area_code', 'area_name', 'area_type', 'date',
                           'deaths']

        # Group by area and take the sum of deaths in the past 7 days
        grouped_council = council.groupby(['area_code', 'area_name'],
                                          as_index=False)
        council_week = grouped_council['deaths'].apply(
            lambda x: x.iloc[-7:].sum())

        council_week = council_week.merge(
            self.regional_pop,
            left_on='area_code',
            right_on='Code',
            how='left')

        council_week['deaths_per_100000'] = (
            council_week['deaths'] / council_week['population'] * 100000)

        return council_week

class PlotDeaths:
    """Class containing methods to use the prepared data to save two
    graphs and one table as html files:
        - daily deaths
        - daily deaths by region
        - table of deaths by council
    """
    def __init__(self, data, template, plot_config):
        self.deaths = data['deaths']
        self.regional_deaths = data['regional']
        self.council_week = data['council']
        self.template = template
        self.plot_config = plot_config

    def graph_daily_deaths_uk(self):
        """Plot graph showing daily deaths for all of the UK and save as
        an html file.

        File name: daily_deaths_uk.html
        """
        df = self.deaths

        fig = go.Figure()

        # Daily deaths - 7 day rolling average
        fig.add_trace(
            go.Scatter(
                x=list(df['date'][:-5]),
                y=list(df['deaths_7_day'][:-5]),
                name="7 Day Average",
                marker=dict(color='rgb(150, 65, 65)'),
                customdata=np.stack((
                    df['deaths_7_day_str'][:-5],
                    df['deaths_str'][:-5]
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

        # Daily deaths - bar plot
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['deaths']),
                name="Daily Deaths",
                marker=dict(color=df['color']),
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Daily Deaths Within 28 Days of a Positive COVID-19 Test"
                   "</b><br><sub>7 day average and daily numbers of deaths by "
                   "date of death.<br>The data for the most recent 5 days is "
                   "incomplete, with the<br>daily deaths shown in grey.<br>"
                   "Source: gov.uk"),
            height=600,
            margin=dict(t=140),
            legend=dict(
                orientation='h',
                x=0.5,
                xanchor='center'
            )
        )

        fig.write_html('graphs/deaths/daily_deaths_uk.html',
                       config=self.plot_config)

    def graph_region_daily_deaths(self):
        """Plot graph showing daily deaths for each region and save as
        an html file.

        File name: region_daily_deaths.html
        """
        df = self.regional_deaths[self.regional_deaths['date'] >= '2020-03-01']

        regions = [
            'North West', 'Yorkshire and The Humber', 'North East',
            'West Midlands', 'East Midlands', 'East of England',
            'South West', 'London', 'South East',
        ]

        fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

        # Daily deaths by region
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['date'][df['area_name'] == region]),
                    y=list(df['deaths_7_day'][df['area_name'] == region]),
                    showlegend=False,
                    text=df['deaths_7_day_str'][df['area_name'] == region],
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
                    '%{text}'
                ),
                value // 3, value % 3 + 1
            )

        # Daily deaths by region per 100,000
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['date'][df['area_name'] == region]),
                    y=list(df['deaths_per_100k'][df['area_name'] == region]),
                    showlegend=False,
                    visible=False,
                    text=df['deaths_per_100k_str'][df['area_name'] == region],
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
                    '%{text}'
                ),
                value // 3, value % 3 + 1
            )

        fig.update_xaxes(
            linewidth=1,
            linecolor='black',
            gridwidth=1,
            gridcolor='rgb(240, 240, 240)'
        )

        fig.update_yaxes(
            matches='y',
            linewidth=1,
            linecolor='black',
            gridwidth=1,
            gridcolor='rgb(240, 240, 240)'
        )

        fig.update_layout(
            title=dict(
                text=("<b>Daily Deaths by Region</b>"
                      "<br><sub>7 day rolling average of daily deaths."
                      "<br>Source: gov.uk"),
                x=0,
                xref='paper',
                y=0.96,
                yref='container',
                yanchor='top'

            ),
            plot_bgcolor='white',
            height=800,
            margin=dict(t=120),
            updatemenus=[
                dict(
                    direction='down',
                    x=1,
                    xanchor='right',
                    y=1.07,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="Deaths",
                             method='update',
                             args=[{'visible': [True] * 9 + [False] * 9},
                                     {'title': ("<b>Daily Deaths by Region</b>"
                                                "<br><sub>7 day rolling "
                                                "average of daily deaths.<br>"
                                                "Source: gov.uk")}]),
                        dict(label="Deaths per 100,000",
                             method='update',
                             args=[{'visible': [False] * 9 + [True] * 9},
                                     {'title': ("<b>Daily Deaths per 100,000 "
                                                "by Region</b><br><sub>7 day "
                                                "rolling average of daily "
                                                "deaths per 100,000.<br>"
                                                "Source: gov.uk")}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/deaths/region_daily_deaths.html',
                       config=self.plot_config)

    def table_deaths_local_area(self):
        """Plot table showing deaths in the past 7 days for each council
        and save as an html file.

        File name: deaths_local_area.html
        """
        table_config = {'displayModeBar': False}
        colors = ['rgb(240,240,240)', 'rgb(240,230,230)']*150

        # Sort by deaths and create a rank column for display in the
        # table.
        df_deaths = self.council_week.sort_values(
            'deaths_per_100000', ascending=False).reset_index()
        df_deaths['rank'] = df_deaths.index + 1

        # Sort councils alphabetically and create a rank column for
        # display in the table.
        df_alpha = self.council_week.sort_values('area_name').reset_index()
        df_alpha['rank'] = df_alpha.index + 1

        table = go.Figure()

        # Table with values sorted deaths
        table.add_trace(
            go.Table(
                header=dict(
                    values=['', '<b>Area</b>',
                            '<b>Deaths in Past 7 Days <br>/ 100,000</b>'],
                    font=dict(
                        color='white'
                    ),
                    align='left',
                    height=30,
                    fill_color='rgba(150, 65, 65, 0.9)'
                ),
                cells=dict(
                    values=[list(df_deaths['rank']),
                            list(df_deaths['area_name']),
                            list(df_deaths['deaths_per_100000'].round(2))],
                    align='left',
                    height=30,
                    fill_color=[colors*3]
                ),
                columnwidth=[0.1, 0.55, 0.35]
            )
        )

        # Table with councils sorted alphabetically
        table.add_trace(
            go.Table(
                header=dict(
                    values=['', '<b>Area</b>',
                            '<b>Deaths in Past 7 Days <br>/ 100,000</b>'],
                    font=dict(
                        color='white'
                    ),
                    align='left',
                    height=30,
                    fill_color='rgba(150, 65, 65, 0.9)'
                ),
                cells=dict(
                    values=[list(df_alpha['rank']),
                            list(df_alpha['area_name']),
                            list(df_alpha['deaths_per_100000'].round(2))],
                    align='left',
                    height=30,
                    fill_color=[colors*3]
                ),
                columnwidth=[0.1, 0.55, 0.35],
                visible=False
            )
        )

        table.update_layout(
            title=dict(
                text=("<b>Deaths in the Past 7 Days per 100,000</b>"
                      "<br>Source: gov.uk"),
                x=0.05,
                xref='paper',
                y=0.96,
                yref='container',
                yanchor='top'
            ),
            width=600,
            height=600,
            margin=dict(
                b=0, t=90, l=0, r=0
            ),
            updatemenus=[
                dict(
                    direction='down',
                    x=0.98,
                    xanchor='right',
                    y=1.05,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="Sort by: Deaths",
                             method='update',
                             args=[{'visible': [True, False]}]),
                        dict(label="Sort by: Area Name",
                             method='update',
                             args=[{'visible': [False, True]}]),
                    ])
                )
            ]
        )

        table.write_html('graphs/deaths/deaths_local_area.html',
                         config=table_config)


def main(population, template, plot_config):
    """Initiate DeathsData class and run methods to prepare deaths data.
    Then initiate PlotDeaths class and run methods to plot graphs.
    """
    deaths = DeathsData(population)
    deaths_df = deaths.prepare_deaths_data()
    regional_df = deaths.prepare_regional_deaths_data()
    council_df = deaths.prepare_council_deaths_data()

    data = {
        'deaths': deaths_df,
        'regional': regional_df,
        'council': council_df,
    }

    deaths = PlotDeaths(data, template, plot_config)
    deaths.graph_daily_deaths_uk()
    deaths.graph_region_daily_deaths()
    deaths.table_deaths_local_area()
