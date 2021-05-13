# ======================================================================
# Script to save graphs summarising cases data as html files. This will
# be imported as a module into main.py.
# ======================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Cases:
    """Class containing methods to save three graphs and one table as
    html files:
        - daily cases
        - daily cases by region (publish date)
        - daily cases by region (specimen data)
        - table of cases by council
    """
    def __init__(self, template, plot_config, population):
        self.template = template
        self.plot_config = plot_config
        self.population = population

    def prepare_cases_data(self):
        """Prepare cases data to be used in graphs."""
        cases_url = ("https://api.coronavirus.data.gov.uk/v2/"
                     "data?areaType=overview"
                     "&metric=newCasesByPublishDate"
                     "&metric=newCasesBySpecimenDate"
                     "&format=csv")

        cases = pd.read_csv(cases_url)
        cases['date'] = pd.to_datetime(cases['date'], format='%Y-%m-%d')
        cases = cases.sort_values('date')

        # Cases data is only available from 28th January 2020
        cases = cases[cases['date'] >= '2020-01-28']
        cases = cases [['date', 'newCasesBySpecimenDate',
                        'newCasesByPublishDate']]
        cases.columns = ['date', 'specimen', 'publish']

        # 7 day rolling averages for daily cases by specimen date and
        # publish date.
        cases['specimen_7_day'] = cases['specimen'].rolling(window=7).mean()
        cases['publish_7_day'] = cases['publish'].rolling(window=7).mean()

        # Thousand comma separated strings to be displayed in labels on
        # graphs for easier reading.
        cols = ['specimen', 'publish', 'specimen_7_day', 'publish_7_day']
        for c in cols:
            cases[c + '_str'] = ["{:,}".format(
                round(x, 2)).replace(".0", "") for x in cases[c]]

        # 5 most recent days in grey as the data is incomplete
        cases['color'] = (
            ['rgba(150, 65, 65, 0.5)'] * (len(cases.index) - 5)
            + ['rgb(200, 200, 200)'] * 5)

        self.cases = cases

    def prepare_regional_cases_data(self):
        """Download and prepare cases data for the 9 regions of England.
        """
        regional_url = ("https://api.coronavirus.data.gov.uk/v2/"
                        "data?areaType=region"
                        "&metric=newCasesBySpecimenDate"
                        "&metric=newCasesByPublishDate"
                        "&format=csv")

        regional = pd.read_csv(regional_url)
        regional['date'] = pd.to_datetime(regional['date'], format='%Y-%m-%d')
        regional = regional.sort_values('date')
        regional.columns = ['area_code', 'area_name', 'area_type',  'date',
                            'specimen', 'publish']

        # Due to a change in reporting method, there is a large spike in
        # cases on 1st July 2020. To estimate the actual daily cases, the
        # average of the 3 days either side of 1st July is taken.
        def july_1(df):
            df = df.reset_index()
            row_july_1 = df[df['date']=='2020-07-01'].index[0]
            rows = (list(range(row_july_1 - 3, row_july_1))
                    + list(range(row_july_1 + 1, row_july_1 + 4)))
            mean = df.iloc[rows, :]['publish'].mean()
            df.loc[df['date']=='2020-07-01', 'publish'] = mean
            return df

        grouped = regional.groupby('area_name', as_index=False)
        regional = grouped.apply(july_1).reset_index(drop=True)

        # 7 day rolling average for cases by specimen date and publish date, and daily
        # deaths.
        grouped_regions = regional.groupby(['area_name', 'area_code'],
                                           as_index=False)
        grouped_regions = grouped_regions[['specimen', 'publish']]
        grouped_regions = grouped_regions.apply(
            lambda x: x.rolling(window=7, min_periods=1).mean())
        regional[['specimen_7_day', 'publish_7_day']] = grouped_regions

        # Population totals by region
        self.regional_pop = self.population.groupby(
            'Code', as_index=False)['population'].sum()

        regional = regional.merge(
            self.regional_pop,
            left_on='area_code',
            right_on='Code',
            how='left')

        regional['specimen_per_100k'] = (regional['specimen_7_day']
                                         / regional['population'] * 100000)
        regional['publish_per_100k'] = (regional['publish_7_day']
                                        / regional['population'] * 100000)

        # Create thousand commas separated strings to use in the plots
        # as they are easier to read.
        for c in ['specimen_7_day', 'publish_7_day', 'specimen_per_100k',
                  'publish_per_100k']:
            regional[c + '_str'] = ["{:,}".format(round(x, 2))
                                    for x in regional[c]]

        self.regional_cases = regional

    def prepare_council_cases_data(self):
        """Download and prepare cases data for each of England's
        councils.
        """
        council_url = ("https://api.coronavirus.data.gov.uk/v2/"
                       "data?areaType=ltla"
                       "&metric=newCasesByPublishDate"
                       "&format=csv")
        council = pd.read_csv(council_url)
        council['date'] = pd.to_datetime(council['date'], format='%Y-%m-%d')
        council = council.sort_values('date')
        council.columns = ['area_code', 'area_name', 'area_type', 'date',
                           'publish']

        # Group by area and take the sum of cases in the past 7 days
        grouped_council = council.groupby(['area_code', 'area_name'],
                                          as_index=False)
        council_week = grouped_council['publish'].apply(
            lambda x: x.iloc[-7:].sum())

        council_week = council_week.merge(
            self.regional_pop,
            left_on='area_code',
            right_on='Code',
            how='left')

        council_week['cases_per_100000'] = (
            council_week['publish'] / council_week['population'] * 100000)

        self.council_week = council_week


    def graph_daily_cases_uk(self):
        """Plot graph showing daily cases for all of the UK and save as
        an html file.

        File name: daily_cases_uk.html
        """
        df = self.cases

        fig = go.Figure()

        # Daily cases (publish date) - 7 day rolling average. Most recent
        # 5 days are not included as the data is incomplete.
        fig.add_trace(
            go.Scatter(
                x=list(df['date'][:-5]),
                y=list(df['publish_7_day'][:-5]),
                name="7 Day Average",
                marker=dict(color='rgb(150, 65, 65)'),
                customdata=np.stack((
                    df['publish_7_day_str'][:-5],
                    df['publish_str'][:-5]
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

        # Daily cases (publish date) - bar plot
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['publish']),
                name="Daily Cases",
                marker=dict(color=list(df['color'])),
                hoverinfo='skip'
            )
        )

        # Daily cases (specimen date) - 7 day rolling average. Most
        # recent 5 days are not included as the data is incomplete.
        fig.add_trace(
            go.Scatter(
                x=list(df['date'][:-5]),
                y=list(df['specimen_7_day'][:-5]),
                name="7 Day Average",
                marker=dict(color='rgb(150, 65, 65)'),
                visible=False,
                customdata=np.stack((
                    df['specimen_7_day_str'][:-5],
                    df['specimen_str'][:-5]
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

        # Daily cases (specimen date) - bar plot
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['specimen']),
                name="Daily Cases",
                marker=dict(color=df['color']),
                visible=False,
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Daily Cases by Published Date</b><br><sub>7 day average"
                   " and daily numbers of cases by date published.<br>The data"
                   " for the most recent 5 days is incomplete, with the<br>"
                   "daily cases shown in grey.<br>Source: gov.uk"),
            height=600,
            margin=dict(t=140),
            legend=dict(
                orientation='h',
                x=0.5,
                xanchor='center'
            ),
            updatemenus=[
                dict(
                    direction='down',
                    x=1,
                    xanchor='right',
                    y=1.01,
                    yanchor='bottom',
                    buttons=list([
                        dict(label="By Publish Date",
                             method='update',
                             args=[{'visible': [True, True, False, False]},
                                   {'title': ("<b>Daily Cases by Published "
                                              "Date</b><br><sub>7 day average "
                                              "and daily numbers of cases by "
                                              "date published.<br>The data for"
                                              " the most recent 5 days is "
                                              "incomplete, with the<br>daily "
                                              "cases shown in grey.<br>Source:"
                                              " gov.uk")}]),
                        dict(label="By Specimen Date",
                             method='update',
                             args=[{'visible': [False, False, True, True]},
                                   {'title': ("<b>Daily Cases by Specimen Date"
                                              "</b><br><sub>7 day average and "
                                              "daily numbers of cases by "
                                              "specimen date.<br>The data for "
                                              "the most recent 5 days is "
                                              "incomplete, with the<br>daily "
                                              "cases shown in grey.<br>Source:"
                                              " gov.uk")}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/cases/daily_cases_uk.html',
                       config=self.plot_config)

    def graph_regional_cases_publish(self):
        """Plot graph showing daily cases by publish date for each
        region and save as an html file.

        File name: regional_cases_publish.html
        """
        df = self.regional_cases

        self.regions = [
            'North West', 'Yorkshire and The Humber', 'North East',
            'West Midlands', 'East Midlands', 'East of England',
            'South West', 'London', 'South East',
        ]
        regions = self.regions

        fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

        # Daily cases by region (publish date)
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['date'][df['area_name'] == region]),
                    y=list(df['publish_7_day'][df['area_name'] == region]),
                    showlegend=False,
                    text=df['publish_7_day_str'][df['area_name'] == region],
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

        # Daily cases by region per 100,000 (publish date)
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['date'][df['area_name'] == region]),
                    y=list(df['publish_per_100k'][df['area_name'] == region]),
                    showlegend=False,
                    visible=False,
                    text=df['publish_per_100k_str'][df['area_name'] == region],
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
                value//3, value%3+1
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
                text=("<b>Daily Cases by Region (Cases Reported by Publish "
                      "Date)</b><br><sub>7 day rolling average of daily cases "
                      "by publish date.<br>Source: gov.uk"),
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
                        dict(label="Cases",
                             method='update',
                             args=[{'visible': [True] * 9 + [False] * 9},
                                     {'title': ("<b>Daily Cases by Region "
                                                "(Cases Reported by Publish "
                                                "Date)</b><br><sub>7 day "
                                                "rolling average of daily "
                                                "cases by publish date.<br>"
                                                "Source: gov.uk")}]),
                        dict(label="Cases per 100,000",
                             method='update',
                             args=[{'visible': [False] * 9 + [True] * 9},
                                     {'title': ("<b>Daily Cases per 100,000 by"
                                                " Region (Cases Reported by "
                                                "Publish Date)</b><br><sub>7 "
                                                "day rolling average of daily "
                                                "cases per 100,000 by publish "
                                                "date.<br>Source: gov.uk")}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/cases/region_cases_publish.html',
                       config=self.plot_config)

    def graph_regional_cases_specimen(self):
        """Plot graph showing daily cases by specimen date for each
        region and save as an html file.

        File name: regional_cases_specimen.html
        """
        df = self.regional_cases
        regions = self.regions

        fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

        # Daily cases by region (specimen date)
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['date'][df['area_name'] == region]),
                    y=list(df['specimen_7_day'][df['area_name'] == region]),
                    showlegend=False,
                    text=df['specimen_7_day_str'][df['area_name'] == region],
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

        # Daily cases by region per 100,000 (specimen date)
        for value, region in enumerate(regions, start=3):
            fig.add_trace(
                go.Scatter(
                    x=list(df['date'][df['area_name'] == region]),
                    y=list(df['specimen_per_100k'][df['area_name'] == region]),
                    showlegend=False,
                    visible=False,
                    text=df['specimen_per_100k_str'][df['area_name'] == region],
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
                text=("<b>Daily Cases by Region (Cases Reported by Specimen "
                      "Date)</b><br><sub>7 day rolling average of daily cases "
                      "by specimen date.<br>Source: gov.uk"),
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
                        dict(label="Cases",
                             method='update',
                             args=[{'visible': [True] * 9 + [False] * 9},
                                     {'title': ("<b>Daily Cases by Region "
                                                "(Cases Reported by Specimen "
                                                "Date)</b><br><sub>7 day "
                                                "rolling average of daily "
                                                "cases by specimen date.<br>"
                                                "Source: gov.uk")}]),
                        dict(label="Cases per 100,000",
                             method='update',
                             args=[{'visible': [False] * 9 + [True] * 9},
                                     {'title': ("<b>Daily Cases per 100,000 by"
                                                " Region (Cases Reported by "
                                                "Specimen Date)</b><br><sub>7 "
                                                "day rolling average of daily "
                                                "cases per 100,000 by specimen "
                                                "date.<br>Source: gov.uk")}]),
                    ])
                )
            ]
        )

        fig.write_html('graphs/cases/region_cases_specimen.html',
                       config=self.plot_config)


    def table_cases_local_area(self):
        """Plot table showing cases in the past 7 days for each council
        and save as an html file.

        File name: cases_local_area.html
        """
        table_config = {'displayModeBar': False}
        colors = ['rgb(240,240,240)', 'rgb(240,230,230)']*150

        # Sort by cases and create a rank column for display in the table
        df_cases = self.council_week.sort_values(
            'cases_per_100000', ascending=False).reset_index()
        df_cases['rank'] = df_cases.index + 1

        # Sort councils alphabetically and create a rank column for
        # display in the table.
        df_alpha = self.council_week.sort_values('area_name').reset_index()
        df_alpha['rank'] = df_alpha.index + 1

        table = go.Figure()

        # Table with values sorted cases
        table.add_trace(
            go.Table(
                header=dict(
                    values=['', '<b>Area</b>',
                            '<b>Cases in Past 7 Days <br>/ 100,000</b>'],
                    font=dict(
                        color='white'
                    ),
                    align='left',
                    height=30,
                    fill_color='rgba(150, 65, 65, 0.9)'
                ),
                cells=dict(
                    values=[list(df_cases['rank']),
                            list(df_cases['area_name']),
                            list(df_cases['cases_per_100000'].round(2))],
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
                            '<b>Cases in Past 7 Days <br>/ 100,000</b>'],
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
                            list(df_alpha['cases_per_100000'].round(2))],
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
                text=("<b>Cases in the Past 7 Days per 100,000</b>"
                      "<br><sub>Cases are by date published."
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
                        dict(label="Sort by: Cases",
                             method='update',
                             args=[{'visible': [True, False]}]),
                        dict(label="Sort by: Area Name",
                             method='update',
                             args=[{'visible': [False, True]}]),
                    ])
                )
            ]
        )

        table.write_html('graphs/cases/cases_local_area.html',
                         config=table_config)


def main(template, plot_config, population):
    """Initiate Cases class and run methods to plot graphs."""
    cases = Cases(template, plot_config, population)
    cases.prepare_cases_data()
    cases.prepare_regional_cases_data()
    cases.prepare_council_cases_data()
    cases.graph_daily_cases_uk()
    cases.graph_regional_cases_publish()
    cases.graph_regional_cases_specimen()
    cases.table_cases_local_area()
