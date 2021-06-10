# ======================================================================
# Script to save graphs summarising vaccination data as html files. This
# will imported as a module into main.py.
# ======================================================================

from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go

class VaccinationsData:
    """Class containing methods to prepare data on:
        - daily vaccination totals
        - percentage vaccinated by age group
    """
    def __init__(self, population):
        self.population = population

    def prepare_vaccination_data(self):
        """Prepare vaccination data for the UK population."""
        vaccine_url = ("https://api.coronavirus.data.gov.uk/v2/"
                       "data?areaType=overview"
                       "&metric=cumPeopleVaccinatedFirstDoseByPublishDate"
                       "&metric=cumPeopleVaccinatedSecondDoseByPublishDate"
                       "&format=csv")

        vaccine = pd.read_csv(vaccine_url)
        vaccine['date'] = pd.to_datetime(vaccine['date'], format='%Y-%m-%d')
        vaccine = vaccine[vaccine['date'] >= '2021-01-10'].sort_values('date')
        vaccine.columns = ['area_code', 'area_name', 'area_type', 'date',
                           'total_first', 'total_second']

        # Create thousand-comma-separated strings to use in the plots as
        # they are easier to read.
        cols = ['total_first', 'total_second']
        for c in cols:
            vaccine[c + '_str'] = ["{:,}".format(int(x)) for x in vaccine[c]]

        # Daily vaccinations
        vaccine['daily_1'] = vaccine['total_first'].diff()
        vaccine['daily_2'] = vaccine['total_second'].diff()

        # Daily vaccinations 7 day average
        vaccine['daily_1_7_day_avg'] = vaccine['daily_1'].rolling(
            window=7).mean()
        vaccine['daily_2_7_day_avg'] = vaccine['daily_2'].rolling(
            window=7).mean()

        # Create thousand-comma-separated strings to use in the plots as
        # they are easier to read.
        for c in ['daily_1', 'daily_2']:
            vaccine[c + '_str'] = [
                "{:,}".format(x).replace(".0", "") for x in vaccine[c]]
        for c in ['daily_1_7_day_avg', 'daily_2_7_day_avg']:
            vaccine[c + '_str'] = [
                "{:,}".format(round(x, 2)) for x in vaccine[c]]

        return vaccine

    def prepare_age_group_vaccine_data(self):
        """Merge vaccination data by age group with the populations of
        those age groups to give the percentage of each age group which
        has been vaccinated.
        """
        england = self.population[self.population['Name'] == 'ENGLAND']

        # Sum the populations of the age group catergories in which the
        # vaccinations are broken down into.
        age_group_pop = [
            england[england['age'].isin(range(30))]['population'].sum(),
            england[england['age'].isin(range(30, 35))]['population'].sum(),
            england[england['age'].isin(range(35, 40))]['population'].sum(),
            england[england['age'].isin(range(40, 45))]['population'].sum(),
            england[england['age'].isin(range(45, 50))]['population'].sum(),
            england[england['age'].isin(range(50, 55))]['population'].sum(),
            england[england['age'].isin(range(55, 60))]['population'].sum(),
            england[england['age'].isin(range(60, 65))]['population'].sum(),
            england[england['age'].isin(range(65, 70))]['population'].sum(),
            england[england['age'].isin(range(70, 75))]['population'].sum(),
            england[england['age'].isin(range(75, 80))]['population'].sum(),
            england[england['age'].isin(
                list(range(80, 90)) + ['90+'])]['population'].sum()
        ]

        def get_recent_thursday():
            """The URL for weekly deaths contains the date that it was
            updated, therefore the date of the most recent Thursday has
            to be found in the form 14-January-2021
            """
            today = date.today()
            week_ago = today - timedelta(days=6)

            for day in pd.date_range(week_ago, today):
                if day.weekday() == 3:
                    return day.strftime("%d-%B-%Y")

        self.recent_thursday = get_recent_thursday()
        

        vaccine_age_url = ("https://www.england.nhs.uk/statistics/wp-content/"
                           "uploads/sites/2/2021/05/"
                           "COVID-19-weekly-announced-vaccinations-"
                           + self.recent_thursday + ".xlsx")

        vaccine_age = pd.read_excel(
            vaccine_age_url,
            sheet_name='NHS Region',
            skiprows=11,
            usecols='B,D,E,F,G,H,I,J,K,L,M,N,O,S,T,U,V,W,X,Y,Z,AA,AB,AC,AD')

        # Drop NaN values in the region column so that the 'Total' for
        # can be found through a string contains filter. This is needed
        # as reference numbers are added, making it, for example,
        # 'Total4'.
        vaccine_age = vaccine_age.drop(
            vaccine_age[vaccine_age['NHS Region of Residence'].isna()].index)
        vaccine_age = vaccine_age[
            vaccine_age['NHS Region of Residence'].str.contains('Total')]

        vaccine_age = pd.DataFrame(
            {
                'age': ['Under 30', '30-34', '35-39', '40-45', '45-49', 
                        '50-54', '55-59', '60-64', '65-69', '70-74', '75-79', 
                        'Over 80'] * 2,
                'dose': ['2 Doses'] * 12 + ['1+ Doses'] * 12,
                'vaccinations': (list(vaccine_age.iloc[0, 13:25])
                                 + list(vaccine_age.iloc[0, 1:13])),
                'population': age_group_pop * 2
            }
        )

        vaccine_age['percent'] = (vaccine_age['vaccinations']
                                  / vaccine_age['population'] * 100)

        return vaccine_age

class PlotVaccinations:
    """Class containing methods to use the prepared data to save three
    graphs as html files:
        - total number vaccinated with 1 or 2 doses in the UK
        - percentage of each age group vaccinated
        - daily vaccinations
    """
    def __init__(self, data, population, thursday, template, plot_config):
        self.vaccine = data['vaccine']
        self.vaccine_age = data['vaccine_age']
        self.population = population
        self.recent_thursday = thursday
        self.template = template
        self.plot_config = plot_config


    def graph_vaccine_total(self):
        """Plot graph showing total number of people vaccinated with
        either 1 dose or both doses and save as an html file.

        File name: vaccine_total.html
        """
        df = self.vaccine

        fig = go.Figure()

        # Number of people vaccinated (1 dose)
        fig.add_trace(
            go.Scatter(
                x=list(df['date']),
                y=list(df['total_first']),
                marker=dict(color='rgb(150, 65, 65)'),
                name="At Least 1 Dose",
                text=df['total_first_str'],
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
                '<b>At Least 1 Dose</b>: %{text}'
            )
        )

        # Number of people vaccinated (2 dose)
        fig.add_trace(
            go.Scatter(
                x=list(df['date']),
                y=list(df['total_second']),
                marker=dict(color='darkblue'),
                name="2 Doses",
                text=df['total_second_str'],
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
                '<b>2 Doses</b>: %{text}'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Number of People Who Have Received the 1st and 2nd Dose"
                   " of Vaccine</b><br><sub>Number of vaccinations reported as"
                   " of " + self.vaccine['date'].max().strftime("%d %B %Y")
                   + "<br>Source: gov.uk"),
            height=600,
            margin=dict(t=100)
        )

        fig.write_html('graphs/vaccine/vaccine_total.html',
                       config=self.plot_config)


    def graph_percentage_vaccinated(self):
        """Plot graph showing the percentage of the population who have
        received either 1 dose or both doses and save as an html file.

        File name: percentage_vaccinated.html
        """
        # UK total population
        uk_pop = self.population[
            self.population['Name'] == 'UNITED KINGDOM']['population'].sum()

        dose_2_percent = self.vaccine['total_second'].max() / uk_pop * 100
        dose_1_percent = self.vaccine['total_first'].max() / uk_pop * 100

        x = [dose_2_percent, dose_1_percent]
        y = [100 - dose_2_percent, 100 - dose_1_percent]

        fig = go.Figure()

        # Percentage of people who have received either 1 or 2 doses
        fig.add_trace(
            go.Bar(
                name="Vaccinated",
                y=['2 Doses', 'At Least<br>1 Dose'],
                x=x,
                marker=dict(color='rgb(150, 65, 65)'),
                orientation='h',
                text=['2 Doses', 'At Least 1 Dose'],
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='gray',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{text}</b><br>'+
                '%{x:.3f}%'
            )
        )

        # Percentage of people who have not received either 1 or 2 doses
        fig.add_trace(
            go.Bar(
                name="Not Vaccinated",
                y=['2 Doses', 'At Least<br>1 Dose'],
                x=y,
                marker=dict(color='rgba(140, 140, 140, 0.8)'),
                orientation='h',
                hoverinfo='skip'
            )
        )

        fig.update_layout(
            title=dict(
                text=("<b>% of UK Population Who Have Received Vaccination</b>"
                      "<br><sub>Number of vaccinations reported as of "
                      + self.vaccine['date'].max().strftime("%d %B %Y")
                      + "<br>Source: gov.uk"),
                x=0,
                xref='paper',
                y=0.85,
                yref='container',
                yanchor='top'
            ),
            barmode='stack',
            legend_traceorder='normal',
            xaxis=dict(
                linewidth=2,
                linecolor='black',
                gridwidth=1,
                gridcolor='rgb(220, 220, 220)'
            ),
            yaxis=dict(
                linewidth=2,
                linecolor='black',
            ),
            height=200,
            margin=dict(t=90, b=0),
            plot_bgcolor='white'
        )

        fig.write_html('graphs/vaccine/percentage_vaccinated.html',
                       config=self.plot_config)

    def graph_daily_vaccinations(self):
        """Plot graph showing daily vaccinations and save as an html
        file.

        File name: daily_vaccinations.html
        """
        df = self.vaccine

        fig = go.Figure()

        # Bar chart - daily 1st doses
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['daily_1']),
                marker=dict(color='rgba(150, 65, 65, 0.3)'),
                showlegend=False,
                text=df['daily_1_str'],
                hoverinfo='skip'
            )
        )

        # Bar chart - daily 2nd doses
        fig.add_trace(
            go.Bar(
                x=list(df['date']),
                y=list(df['daily_2']),
                marker=dict(color='rgba(0, 0, 100, 0.3)'),
                showlegend=False,
                text=df['daily_2_str'],
                hoverinfo='skip'
            )
        )

        # Line chart - 1st doses 7 day average
        fig.add_trace(
            go.Scatter(
                x=list(df['date']),
                y=list(df['daily_1_7_day_avg']),
                line=dict(
                    width=3,
                    color='rgb(150, 65, 65)',
                ),
                name='1st Dose',
                customdata=np.stack(
                    (df['daily_1_7_day_avg_str'],
                     df['daily_1_str']),
                    axis=-1
                ),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='rgb(150, 65, 65)',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x}</b><br>'+
                '<b>Daily</b>: %{customdata[0]}<br>' +
                '<b>7 Day Avg.</b>: %{customdata[1]}'
            )
        )

        # Line chart - 2nd doses 7 day average
        fig.add_trace(
            go.Scatter(
                x=list(df['date']),
                y=list(df['daily_2_7_day_avg']),
                line=dict(
                    width=3,
                    color='darkblue',
                ),
                name='2nd Dose',
                customdata=np.stack(
                    (df['daily_2_7_day_avg_str'],
                     df['daily_2_str']),
                    axis=-1
                ),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='darkblue',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x}</b><br>'+
                '<b>Daily</b>: %{customdata[0]}<br>' +
                '<b>7 Day Avg.</b>: %{customdata[1]}'
            )
        )

        fig.update_layout(
            template=self.template,
            title=("<b>Vaccinations - Daily and 7 Day Daily Averages</b><br>"
                   "<sub>The date is the date the vaccination was reported."
                   "<br>Source: gov.uk"),
            margin=dict(t=100)
        )

        fig.write_html('graphs/vaccine/daily_vaccinations.html',
                       config=self.plot_config)

    def graph_percentage_vaccinated_age(self):
        """
        """
        df = self.vaccine_age
        fig = go.Figure()

        # At least 1 dose
        fig.add_trace(
            go.Bar(
                name="At Least 1 Dose",
                x=list(df['age'][df['dose']=='1+ Doses']),
                y=list(df['percent'][df['dose']=='1+ Doses']),
                marker=dict(color='rgb(200, 110, 110)'),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='gray',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x} - 1+ Doses</b><br>'+
                '%{y:.2f}%'
            )
        )

        # 2 Doses
        fig.add_trace(
            go.Bar(
                name="2 Doses",
                x=list(df['age'][df['dose']=='2 Doses']),
                y=list(df['percent'][df['dose']=='2 Doses']),
                marker=dict(color='rgb(150, 65, 65)'),
                hoverlabel=dict(
                    bgcolor='white',
                    bordercolor='gray',
                    font=dict(
                        color='black'
                    )
                ),
                hovertemplate=
                '<extra></extra>'+
                '<b>%{x} - 2 Doses</b><br>'+
                '%{y:.2f}%'
            )
        )

        fig.update_layout(
            title=dict(
                text=("<b>% of England's Population Who Have Received At Least"
                      " 1 Dose or 2 Doses<br>of Vaccination by Age Group</b>"
                      "<br><sub>Number of vaccinations reported as of "
                      + self.recent_thursday.replace("-", " ")
                      + "<br><i>Note: Vaccination totals may exceed ONS "
                      "mid-2019 age group population estimates.</i><br>"
                      "Sources: NHS England, Office for National Statistics"),
                x=0,
                xref='paper',
                y=0.96,
                yref='container',
                yanchor='top'
            ),
            barmode='group',
            height=600,
            margin=dict(t=130),
            plot_bgcolor='white',
            xaxis=dict(
                linewidth=2,
                linecolor='black',
            ),
            yaxis=dict(
                linewidth=2,
                linecolor='black',
                gridwidth=1,
                gridcolor='rgb(220, 220, 220)'
            )
        )

        fig.write_html('graphs/vaccine/percentage_vaccinated_age.html',
                       config=self.plot_config)


def main(population, template, plot_config):
    """Initiate VaccinationsData class and run methods to prepare cases
    data. Then initiate PlotVaccinations class and run methods to plot
    graphs.
    """
    vaccine = VaccinationsData(population)
    vaccine_df = vaccine.prepare_vaccination_data()
    vaccine_age = vaccine.prepare_age_group_vaccine_data()
    thursday = vaccine.recent_thursday

    data = {
        'vaccine': vaccine_df,
        'vaccine_age': vaccine_age,
    }

    vaccine = PlotVaccinations(data, population, thursday, template,
                               plot_config)
    vaccine.graph_vaccine_total()
    vaccine.graph_percentage_vaccinated()
    vaccine.graph_daily_vaccinations()
    vaccine.graph_percentage_vaccinated_age()
