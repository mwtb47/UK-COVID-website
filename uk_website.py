# =============================================================================
# Creates plots summarising data on cases, deaths and hospitalisations using
# data gov.uk
#
# Contact: mwt.barnes@outlook.com
# =============================================================================

import datetime

from bs4 import BeautifulSoup
import config
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------
# Graph template
# --------------

template=dict(
    layout=go.Layout(
        title=dict(
            x=0,
            xref='paper',
            y=0.96,
            yref='container',
            yanchor='top'
        ),
        xaxis=dict(
            showline=True,
            linewidth=1.5,
            linecolor='black',
            gridwidth=1,
            gridcolor='whitesmoke'
        ),
        yaxis=dict(
            showline=True,
            linewidth=1.5,
            linecolor='black',
            gridwidth=1,
            gridcolor='whitesmoke'
        ),
        paper_bgcolor='white',
        plot_bgcolor='white',
        hovermode='closest'
    )
)

# Ploty mode bar configuration
config={
    'modeBarButtonsToRemove': [
        'toggleSpikelines', 'hoverClosestCartesian', 'hoverCompareCartesian',
        'lasso2d', 'toggleSpikelines', 'autoScale2d', 'zoom2d'
    ]
}

# =============================================================================
# UK data from gov.uk on hospital admissions, cases by specimen and publish
# date, and deaths.
# =============================================================================

uk_url = ("https://api.coronavirus.data.gov.uk/v2/data?areaType=overview"
          "&metric=newAdmissions"
          "&metric=hospitalCases"
          "&metric=newCasesByPublishDate"
          "&metric=newCasesBySpecimenDate"
          "&metric=newDeaths28DaysByDeathDate&format=csv")

uk = pd.read_csv(uk_url)
uk['date'] = pd.to_datetime(uk['date'], format='%Y-%m-%d')
uk = uk.sort_values('date')

# Population data from ONS
population = pd.read_excel(
    'data/uk_population.xlsx',
    sheet_name='MYE2 - Persons',
    skiprows=4)

# ---------------
# Cases data - UK
# ---------------

# Cases data is only available from 28th January 2020
uk_cases = uk[uk['date'] >= '2020-01-28'][
    ['date', 'newCasesBySpecimenDate', 'newCasesByPublishDate']].copy()

uk_cases.columns = ['date', 'specimen', 'publish']

# 7 day rolling averages for daily cases by specimen date and publish date
uk_cases['specimen_7_day'] = uk_cases['specimen'].rolling(window=7).mean()
uk_cases['publish_7_day'] = uk_cases['publish'].rolling(window=7).mean()

# Thousand comma separated strings to be displayed in labels on graphs for
# easier reading.
cols = ['specimen', 'publish', 'specimen_7_day', 'publish_7_day']
for c in cols:
    uk_cases[c + '_str'] = ["{:,}".format(
        round(x, 2)).replace(".0", "") for x in uk_cases[c]]

# ------------------------
# Graph - daily cases UK
# Filename: daily_cases_uk
# ------------------------

# 5 most recent days in grey as the data is incomplete
uk_cases['color'] = (['rgba(150, 65, 65, 0.5)'] * (len(uk_cases.index) - 5)
                     + ['rgb(200, 200, 200)'] * 5)

fig = go.Figure()

# Daily cases (publish date) - 7 day rolling average. Most recent 5 days are
# not included as the data is incomplete.
fig.add_trace(
    go.Scatter(
        x=list(uk_cases['date'][:-5]),
        y=list(uk_cases['publish_7_day'][:-5]),
        name="7 Day Average",
        marker=dict(color='rgb(150, 65, 65)'),
        customdata=np.stack((
            uk_cases['publish_7_day_str'][:-5],
            uk_cases['publish_str'][:-5]
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
        x=list(uk_cases['date']),
        y=list(uk_cases['publish']),
        name="Daily Cases",
        marker=dict(color=list(uk_cases['color'])),
        hoverinfo='skip'
    )
)

# Daily cases (specimen date) - 7 day rolling average. Most recent 5 days are
# not included as the data is incomplete.
fig.add_trace(
    go.Scatter(
        x=list(uk_cases['date'][:-5]),
        y=list(uk_cases['specimen_7_day'][:-5]),
        name="7 Day Average",
        marker=dict(color='rgb(150, 65, 65)'),
        visible=False,
        customdata=np.stack((
            uk_cases['specimen_7_day_str'][:-5],
            uk_cases['specimen_str'][:-5]
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
        x=list(uk_cases['date']),
        y=list(uk_cases['specimen']),
        name="Daily Cases",
        marker=dict(color=uk_cases['color']),
        visible=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    template=template,
    title=("<b>Daily Cases by Published Date</b><br>"
           "<sub>7 day average and daily numbers of cases by date published."
           "<br>The data for the most recent 5 days is incomplete, with the "
           "<br>daily cases shown in grey."
           "<br>Source: gov.uk"),
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
                           {'title': ("<b>Daily Cases by Published Date</b><br>"
                                      "<sub>7 day average and daily numbers "
                                      "of cases by date published.<br>The "
                                      "data for the most recent 5 days is "
                                      "incomplete, with the<br>daily cases "
                                      "shown in grey.<br>Source: gov.uk")}]),
                dict(label="By Specimen Date",
                     method='update',
                     args=[{'visible': [False, False, True, True]},
                           {'title': ("<b>Daily Cases by Specimen Date</b><br>"
                                      "<sub>7 day average and daily numbers "
                                      "of cases by specimen date.<br>The "
                                      "data for the most recent 5 days is "
                                      "incomplete, with the<br>daily cases "
                                      "shown in grey.<br>Source: gov.uk")}]),
            ])
        )
    ]
)

fig.write_html('graphs/cases/daily_cases_uk.html', config=config)

# ----------------
# Deaths data - UK
# ----------------

# Date is only available from the 6th March 2020
uk_deaths = uk[uk['date'] >= '2020-03-06'][
    ['date', 'newDeaths28DaysByDeathDate']].copy()

uk_deaths.columns = ['date', 'deaths']

# 7 day rolling average of deaths
uk_deaths['deaths_7_day'] = uk_deaths['deaths'].rolling(window=7).mean()

# Thousand comma separated strings to be displayed in labels on graphs for
# easier reading.
uk_deaths['deaths_str'] = ["{:,}".format(x).replace(".0", "")
                           for x in uk_deaths['deaths']]
uk_deaths['deaths_7_day_str'] = ["{:,}".format(round(x, 2))
                                 for x in uk_deaths['deaths_7_day']]

# -------------------------
# Graph - daily deaths UK
# Filename: daily_deaths_uk
# -------------------------

# 5 most recent days in grey as the data is incomplete
uk_deaths['color'] = (['rgba(150, 65, 65, 0.5)'] * (len(uk_deaths.index) - 5)
                      + ['rgb(200, 200, 200)'] * 5)

fig = go.Figure()

# Daily deaths - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(uk_deaths['date'][:-5]),
        y=list(uk_deaths['deaths_7_day'][:-5]),
        name="7 Day Average",
        marker=dict(color='rgb(150, 65, 65)'),
        customdata=np.stack((
            uk_deaths['deaths_7_day_str'][:-5],
            uk_deaths['deaths_str'][:-5]
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
        x=list(uk_deaths['date']),
        y=list(uk_deaths['deaths']),
        name="Daily Deaths",
        marker=dict(color=uk_deaths['color']),
        hoverinfo='skip'
    )
)

fig.update_layout(
    template=template,
    title=("<b>Daily Deaths Within 28 Days of a Positive COVID-19 Test</b><br>"
           "<sub>7 day average and daily numbers of deaths by date of death."
           "<br>The data for the most recent 5 days is incomplete, with the "
           "<br>daily deaths shown in grey."
           "<br>Source: gov.uk"),
    height=600,
    margin=dict(t=140),
    legend=dict(
        orientation='h',
        x=0.5,
        xanchor='center'
    )
)

fig.write_html('graphs/deaths/daily_deaths_uk.html', config=config)

# -----------------------------
# Hospital admissions data - UK
# -----------------------------

# UK admissions data only available from 23rd March 2020
uk_admissions = uk[uk['date'] >= '2020-03-23'][
    ['date', 'newAdmissions', 'hospitalCases']].copy()

uk_admissions.columns = ['date', 'admissions', 'in_hospital']

# 7 day rolling average of admissions
uk_admissions['admissions_7_day'] = uk_admissions['admissions'].rolling(
    window=7).mean()

# Thousand comma separated strings to be displayed in labels on graphs for
# easier reading.
uk_admissions['admissions_str'] = [
    "{:,}".format(x).replace(".0", "") for x in uk_admissions['admissions']]
uk_admissions['admissions_7_day_str'] = [
    "{:,}".format(round(x, 2)) for x in uk_admissions['admissions_7_day']]
uk_admissions['in_hospital_str'] = [
    "{:,}".format(x).replace(".0", "") for x in uk_admissions['in_hospital']]

# -----------------------------
# Graph - daily admissions UK
# Filename: daily_admissions_uk
# -----------------------------

fig = go.Figure()

# UK admissions - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(uk_admissions['date']),
        y=list(uk_admissions['admissions_7_day']),
        name="7 Day Average",
        marker=dict(color='rgb(150, 65, 65)'),
        customdata=np.stack((
            uk_admissions['admissions_7_day_str'],
            uk_admissions['admissions_str']
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
        x=list(uk_admissions['date']),
        y=list(uk_admissions['admissions']),
        name="Daily Admissions",
        marker=dict(color='rgba(150, 65, 65, 0.5)'),
        hoverinfo='skip'
    )
)

fig.update_layout(
    template=template,
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

fig.write_html('graphs/admissions/daily_admissions_uk.html', config=config)

# -----------------------------
# Graph - daily admissions UK
# Filename: daily_admissions_uk
# -----------------------------

fig = go.Figure()

# UK COVID-19 patients - bar plot
fig.add_trace(
    go.Bar(
        x=list(uk_admissions['date']),
        y=list(uk_admissions['in_hospital']),
        marker=dict(color='rgba(150, 65, 65, 0.8)'),
        text=uk_admissions['in_hospital_str'],
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
    template=template,
    title=("<b>Total Number of Confirmed COVID-19 Patients in Hospital</b>"
           "<br><sub>Note - the definition of a COVID-19 patient differs "
           "between England, Wales, Scotland and Northern Ireland."
           "<br>Source: gov.uk"),
    height=600,
    margin=dict(t=100),
    legend=dict(
        orientation='h',
        x=0.5,
        xanchor='center'
    )
)

fig.write_html('graphs/admissions/in_hospital_uk.html', config=config)

# =============================================================================
# Vaccinations data from gov.uk
# =============================================================================

vaccine_url = ("https://api.coronavirus.data.gov.uk/v2/data?areaType=overview"
               "&metric=cumPeopleVaccinatedFirstDoseByPublishDate"
               "&metric=cumPeopleVaccinatedSecondDoseByPublishDate&format=csv")

vaccine = pd.read_csv(vaccine_url)

vaccine['date'] = pd.to_datetime(vaccine['date'], format='%Y-%m-%d')

vaccine = vaccine[vaccine['date'] >= '2021-01-10'].sort_values('date')

vaccine.columns = ['date', 'area_type', 'area_code', 'area_name',
                   'total_first', 'total_second']

# Create thousand commas separated strings to use in the plots as they are
# easier to read.
cols = ['total_first', 'total_second']
for c in cols:
    vaccine[c + '_str'] = ["{:,}".format(int(x)) for x in vaccine[c]]

# ------------------------------------
# Graph - total number of vaccinations
# Filename: vaccine_total
# ------------------------------------

fig = go.Figure()

# Number of people vaccinated (1 dose)
fig.add_trace(
    go.Scatter(
        x=list(vaccine['date']),
        y=list(vaccine['total_first']),
        marker=dict(color='rgb(150, 65, 65)'),
        name="1st Dose",
        text=vaccine['total_first_str'],
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
        '<b>1st Vaccine Dose</b>: %{text}'
    )
)

# Number of people vaccinated (2 doss)
fig.add_trace(
    go.Scatter(
        x=list(vaccine['date']),
        y=list(vaccine['total_second']),
        marker=dict(color='darkblue'),
        name="2nd Dose",
        text=vaccine['total_second_str'],
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
        '<b>2nd Vaccine Dose</b>: %{text}'
    )
)

fig.update_layout(
    template=template,
    title=("<b>Number of People Who Have Received the 1st and 2nd Vaccine "
           "Dose</b>"
           "<br><sub>Number of vaccinations reported as of "
           + vaccine['date'].max().strftime("%d %B %Y")
           + "<br>Source: gov.uk"),
    height=600,
    margin=dict(t=100)
)

fig.write_html('graphs/vaccine/vaccine_total.html', config=config)

# -------------------------------
# Graph - percentage vaccinated
# Filename: percentage_vaccinated
# -------------------------------

# UK total population
uk_pop = population.iloc[0]['All ages']

dose_2_percent = vaccine['total_second'].max() / uk_pop * 100
dose_1_percent = vaccine['total_first'].max() / uk_pop * 100

x = [dose_2_percent, dose_1_percent]
y = [100 - dose_2_percent, 100 - dose_1_percent]

fig = go.Figure()

# Percentage of people who have received either 1 or 2 doses
fig.add_trace(
    go.Bar(
        name="Vaccinated",
        y=['2 Doses', 'At least<br>1 Dose'],
        x=x,
        marker=dict(color='rgb(150, 65, 65)'),
        orientation='h',
        text=['2 Doses', '1 Dose'],
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
        y=['2 Doses', 'At least<br>1 Dose'],
        x=y,
        marker=dict(color='rgba(140, 140, 140, 0.8)'),
        orientation='h',
        hoverinfo='skip'
    )
)

fig.update_layout(
    title=dict(
        text=("<b>% of UK Population Who Have Received Vaccination</b><br>"
              "<sub>Number of vaccinations reported as of "
              + vaccine['date'].max().strftime("%d %B %Y")
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

fig.write_html('graphs/vaccine/percentage_vaccinated.html', config=config)

# ----------------------------
# Graph - daily vaccinations
# Filename: daily_vaccinations
# ----------------------------

# Daily vaccinations
vaccine['daily_1'] = vaccine['total_first'].diff()
vaccine['daily_2'] = vaccine['total_second'].diff()

# Create thousand commas separated strings to use in the plots as they are
# easier to read.
cols = ['daily_1', 'daily_2']
for c in cols:
    vaccine[c + '_str'] = [
        "{:,}".format(x).replace(".0", "") for x in vaccine[c]]

fig = go.Figure()

# Daily 1st dose vaccinations
fig.add_trace(
    go.Scatter(
        x=list(vaccine['date']),
        y=list(vaccine['daily_1']),
        marker=dict(color='rgb(150, 65, 65)'),
        name='1st Dose',
        text=vaccine['daily_1_str'],
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
        '<b>Vaccinations</b>: %{text}'
    )
)

# Daily 2nd dose vaccinations
fig.add_trace(
    go.Scatter(
        x=list(vaccine['date']),
        y=list(vaccine['daily_2']),
        marker=dict(color='darkblue'),
        name='2nd Dose',
        text=vaccine['daily_2_str'],
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
        '<b>Vaccinations</b>: %{text}'
    )
)

fig.update_layout(
    template=template,
    title=("<b>Daily Vaccinations</b>"
           "<br><sub>The date is the date the vaccination was reported."
           "<br>Source: gov.uk"),
    margin=dict(t=100)
)

fig.write_html('graphs/vaccine/daily_vaccinations.html', config=config)

# ------------------------------------------
# % of England Population Over 80 Vaccinated
# ------------------------------------------

# Date is released every Thursday and the URL contains the date therefore the
# date of the most recent Thursday needs to be found in the form
# 14-January-2021
date_range = pd.Series(pd.date_range('14-01-2021', '31-12-2021', freq='7D'))
date_today = pd.to_datetime(datetime.date.today())
most_recent_thursday = date_range[date_range.le(date_today)].max()
most_recent_thursday = most_recent_thursday.strftime("%d-%B-%Y")

vaccine_80_url = ("https://www.england.nhs.uk/statistics/wp-content/uploads/"
                  "sites/2/2021/01/COVID-19-weekly-announced-vaccinations-"
                  + most_recent_thursday + ".xlsx")

vaccine_80 = pd.read_excel(
    vaccine_80_url,
    sheet_name='Vaccinations by Region & Age',
    skiprows=11,
    usecols='B,D,E,G,H')

vaccine_80 = vaccine_80[vaccine_80['Region of Residence'] == 'Total']

vaccine_80.columns = ['region', 'under_80_first', 'over_80_first',
                      'under_80_second', 'over_80_second']

# -------------------------------------
# Graph - percentage vaccinated over 80
# Filename: percentage_vaccinated_80
# -------------------------------------

# UK population 80+ years old
pop = population[population['Name'] == 'UNITED KINGDOM'][
    list(range(80, 90)) + ["90+"]]
pop_over_80 = pop.iloc[0,:].sum()

dose_2_percent = vaccine_80['over_80_second'].max() / pop_over_80 * 100
dose_1_percent = vaccine_80['over_80_first'].max() / pop_over_80 * 100

x = [dose_2_percent, dose_1_percent]
y = [100 - dose_2_percent, 100 - dose_1_percent]

fig = go.Figure()

# Percentage of people 80+ who have received either 1 or 2 doses
fig.add_trace(
    go.Bar(
        name="Vaccinated",
        y=['2 Doses', '1 Dose'],
        x=x,
        marker=dict(color='rgb(150, 65, 65)'),
        orientation='h',
        text=['2 Doses', '1 Dose'],
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
        '%{x:.2f}%'
    )
)

# Percentage of people 80+ who have not received either 1 or 2 doses
fig.add_trace(
    go.Bar(
        name="Not Vaccinated",
        y=['2 Doses', '1 Dose'],
        x=y,
        marker=dict(color='rgba(140, 140, 140, 0.8)'),
        orientation='h',
        hoverinfo='skip'
    )
)

fig.update_layout(
    title=dict(
        text=("<b>% of England's Population Aged 80 or Over Who Have Received "
              "Vaccination</b><br><sub>Number of vaccinations reported as of "
              + most_recent_thursday.replace("-", " ")
              + "<br>Source: NHS England"),
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
    height=210,
    margin=dict(t=100, b=0),
    plot_bgcolor='white'
)

fig.write_html('graphs/vaccine/percentage_vaccinated_80.html', config=config)

# =============================================================================
# Regional data
# =============================================================================

# -----
# Cases
# -----

regional_url = ("https://api.coronavirus.data.gov.uk/v2/data?areaType=region"
                "&metric=newCasesBySpecimenDate"
                "&metric=newCasesByPublishDate"
                "&metric=newDeaths28DaysByDeathDate&format=csv")

regional = pd.read_csv(regional_url)

regional.columns = ['date', 'area_type', 'area_code', 'area_name', 'specimen',
                    'publish', 'deaths']

regional['date'] = pd.to_datetime(regional['date'], format='%Y-%m-%d')
regional = regional.sort_values('date')

# Due to a change in reporting method, there is a large spike in cases on 1st
# July 2020. To estimate the actual daily cases, the average of the 3 days
# either side of 1st July is taken.
def july_1(df):
    df = df.reset_index()
    row_july_1 = df[df['date']=='2020-07-01'].index[0]
    rows = (list(range(row_july_1 - 3, row_july_1))
            + list(range(row_july_1 + 1, row_july_1 + 4)))
    mean = df.iloc[rows, :]['publish'].mean()
    df.loc[df['date']=='2020-07-01', 'publish'] = mean
    return df

regional = regional.groupby('area_name', as_index=False).apply(july_1)

# 7 day rolling average for cases by specimen date and publish date, and daily
# deaths.
grouped_regions = regional.groupby(['area_name', 'area_code'], as_index=False)
grouped_regions = grouped_regions[['specimen', 'publish', 'deaths']].apply(
    lambda x: x.rolling(window=7, min_periods=1).mean())
regional[['specimen_7_day', 'publish_7_day', 'deaths_7_day']] = grouped_regions

regional = regional.merge(
    population[['Code', 'All ages']],
    left_on='area_code',
    right_on='Code',
    how='left')

regional['specimen_per_100k'] = (regional['specimen_7_day']
                                 / regional['All ages'] * 100000)
regional['publish_per_100k'] = (regional['publish_7_day']
                                / regional['All ages'] * 100000)
regional['deaths_per_100k'] = (regional['deaths_7_day']
                               / regional['All ages'] * 100000)

# Create thousand commas separated strings to use in the plots as they are
# easier to read.
for c in ['specimen_7_day', 'publish_7_day', 'deaths_7_day',
          'specimen_per_100k', 'publish_per_100k', 'deaths_per_100k']:
    regional[c + '_str'] = ["{:,}".format(round(x, 2)) for x in regional[c]]

# --------------------------------------
# Graph - regional cases by publish date
# Filename: region_cases_publish
# --------------------------------------

regions = [
    'North West', 'Yorkshire and The Humber', 'North East',
    'West Midlands', 'East Midlands', 'East of England',
    'South West', 'London', 'South East'
]

fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

# Daily cases by region (publish date)
for value, region in enumerate(regions, start=3):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['area_name'] == region]),
            y=list(regional['publish_7_day'][regional['area_name'] == region]),
            showlegend=False,
            text=regional['publish_7_day_str'],
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

# Daily cases by region per 100,000 (publish date)
for value, region in enumerate(regions, start=3):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['area_name'] == region]),
            y=list(regional['publish_per_100k'][regional['area_name'] == region]),
            showlegend=False,
            visible=False,
            text=regional['publish_per_100k_str'],
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
        text=("<b>Daily Cases by Region (Cases Reported by Publish Date)</b>"
              "<br><sub>7 day rolling average of daily cases by publish date."
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
                dict(label="Cases",
                     method='update',
                     args=[{'visible': [True]*9 + [False]*9},
                             {'title': ("<b>Daily Cases by Region "
                                        "(Cases Reported by Publish Date)</b>"
                                        "<br><sub>7 day rolling average of "
                                        "daily cases by publish date."
                                        "<br>Source: gov.uk")}]),
                dict(label="Cases per 100,000",
                     method='update',
                     args=[{'visible': [False]*9 + [True]*9},
                             {'title': ("<b>Daily Cases per 100,000 by Region "
                                        "(Cases Reported by Publish Date)</b>"
                                        "<br><sub>7 day rolling average of "
                                        "daily cases per 100,000 by publish "
                                        "date."
                                        "<br>Source: gov.uk")}]),
            ])
        )
    ]
)

fig.write_html('graphs/cases/region_cases_publish.html', config=config)

# ---------------------------------------
# Graph - regional cases by specimen date
# Filename: region_cases_specimen
# ---------------------------------------

fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

# Daily cases by region (specimen date)
for value, region in enumerate(regions, start=3):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['area_name'] == region]),
            y=list(regional['specimen_7_day'][regional['area_name'] == region]),
            showlegend=False,
            text=regional['specimen_7_day_str'],
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

# Daily cases by region per 100,000 (specimen date)
for value, region in enumerate(regions, start=3):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['area_name'] == region]),
            y=list(regional['specimen_per_100k'][regional['area_name'] == region]),
            showlegend=False,
            visible=False,
            text=regional['specimen_per_100k_str'],
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
        text=("<b>Daily Cases by Region (Cases Reported by Specimen Date)</b>"
              "<br><sub>7 day rolling average of daily cases by specimen date."
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
                dict(label="Cases",
                     method='update',
                     args=[{'visible': [True]*9 + [False]*9},
                             {'title': ("<b>Daily Cases by Region "
                                        "(Cases Reported by Specimen Date)</b>"
                                        "<br><sub>7 day rolling average of "
                                        "daily cases by specimen date."
                                        "<br>Source: gov.uk")}]),
                dict(label="Cases per 100,000",
                     method='update',
                     args=[{'visible': [False]*9 + [True]*9},
                             {'title': ("<b>Daily Cases per 100,000 by Region "
                                        "(Cases Reported by Specimen Date)</b>"
                                        "<br><sub>7 day rolling average of "
                                        "daily cases per 100,000 by specimen "
                                        "date."
                                        "<br>Source: gov.uk")}]),
            ])
        )
    ]
)

fig.write_html('graphs/cases/region_cases_specimen.html', config=config)

# ------
# Deaths
# ------

# -----------------------------
# Graph - regional daily deaths
# Filename: region_daily_deaths
# -----------------------------

regional = regional[regional['date'] >= '2020-03-01']

fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

# Daily deaths by region
for value, region in enumerate(regions, start=3):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['area_name'] == region]),
            y=list(regional['deaths_7_day'][regional['area_name'] == region]),
            showlegend=False,
            text=regional['deaths_7_day_str'],
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

# Daily deaths by region per 100,000
for value, region in enumerate(regions, start=3):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['area_name'] == region]),
            y=list(regional['deaths_per_100k'][regional['area_name'] == region]),
            showlegend=False,
            visible=False,
            text=regional['deaths_per_100k_str'],
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
                     args=[{'visible': [True]*9 + [False]*9},
                             {'title': ("<b>Daily Deaths by Region</b>"
                                        "<br><sub>7 day rolling average of "
                                        "daily deaths."
                                        "<br>Source: gov.uk")}]),
                dict(label="Deaths per 100,000",
                     method='update',
                     args=[{'visible': [False]*9 + [True]*9},
                             {'title': ("<b>Daily Deaths per 100,000 by Region "
                                        "</b>"
                                        "<br><sub>7 day rolling average of "
                                        "daily deaths per 100,000."
                                        "<br>Source: gov.uk")}]),
            ])
        )
    ]
)

fig.write_html('graphs/deaths/region_daily_deaths.html', config=config)

# =============================================================================
# Council data
# =============================================================================

council_url = ("https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla"
               "&metric=newCasesByPublishDate"
               "&metric=newDeaths28DaysByDeathDate&format=csv")

council = pd.read_csv(council_url)

council.columns = ['date', 'area_type', 'area_code', 'area_name', 'publish',
                   'deaths']

council['date'] = pd.to_datetime(council['date'], format='%Y-%m-%d')
council = council.sort_values('date')

# Group by area and take the sum of cases in the past 7 days
grouped_council = council.groupby(['area_code', 'area_name'], as_index=False)

council_week = grouped_council[['publish', 'deaths']].apply(
    lambda x: x.iloc[-7:].sum())

council_week = council_week.merge(
    population[['Code', 'All ages']],
    left_on='area_code',
    right_on='Code',
    how='left')

council_week['cases_per_100000'] = (council_week['publish']
                                    / council_week['All ages'] * 100000)
council_week['deaths_per_100000'] = (council_week['deaths']
                                     / council_week['All ages'] * 100000)

# --------------------------------------------
# Table - cases in the past 7 days per 100,000
# Filename: cases_local_area
# --------------------------------------------

table_config = {'displayModeBar': False}
colors = ['rgb(240,240,240)', 'rgb(240,230,230)']*150

# Sort by cases and create a rank column for display in the table
df_cases = council_week.sort_values(
    'cases_per_100000', ascending=False).reset_index()
df_cases['rank'] = df_cases.index+1

# Sort councils alphabetically and create a rank column for display in the
# table
df_alpha = council_week.sort_values('area_name').reset_index()
df_alpha['rank'] = df_alpha.index+1

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
              "<br><sub>Cases are by date reported."
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
        b=0,
        t=90,
        l=0,
        r=0
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

table.write_html('graphs/cases/cases_local_area.html', config=table_config)

# --------------------------------------------
# Table - cases in the past 7 days per 100,000
# Filename: cases_local_area
# --------------------------------------------

# Sort by deaths and create a rank column for display in the table
df_deaths = council_week.sort_values(
    'deaths_per_100000', ascending=False).reset_index()
df_deaths['rank'] = df_deaths.index+1

table = go.Figure()

# Table with values sorted by deaths
table.add_trace(
    go.Table(
        header=dict(
            values=['', '<b>Area</b>',
                    '<b>Deaths in Past 7 Days / 100,000</b>'],
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
              "<br><sub>Source: gov.uk"),
        x=0.05,
        xref='paper',
        y=0.96,
        yref='container',
        yanchor='top'
    ),
    width=600,
    height=600,
    margin=dict(
        b=0,
        t=70,
        l=0,
        r=0
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

table.write_html('graphs/deaths/deaths_local_area.html', config=table_config)
