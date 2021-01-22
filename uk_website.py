# =============================================================================
# Creates plots summarising data on cases, deaths and hospitalisations using
# data gov.uk
#
# Contact: mwt.barnes@outlook.com
# =============================================================================

from bs4 import BeautifulSoup
import config
import datetime
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests

# --------------
# Graph template
# --------------

template=dict(
    layout=go.Layout(
        title=dict(
            x=0,
            xref='paper'
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

# =============================================================================
# UK data from gov.uk on hospital admissions, cases by specimen and publish
# date, and deaths.
# =============================================================================

uk_url = "https://api.coronavirus.data.gov.uk/v2/data?areaType=overview" \
         "&metric=newAdmissions" \
         "&metric=newCasesByPublishDate" \
         "&metric=newCasesBySpecimenDate" \
         "&metric=newDeaths28DaysByDeathDate&format=csv"

uk = pd.read_csv(uk_url)
uk['date'] = pd.to_datetime(uk['date'], format='%Y-%m-%d')
uk = uk.sort_values('date')

# Population data from ONS
population = pd.read_excel('data/uk_population.xlsx',
                            sheet_name='MYE2 - Persons',
                            skiprows=4)

# ---------------
# Cases data - UK
# ---------------

# Cases data is only available from 28th January 2020
uk_cases = uk[uk['date'] >= '2020-01-28'][
    ['date', 'newCasesBySpecimenDate', 'newCasesByPublishDate']].copy()

# 7 day rolling averages for daily cases by specimen date and publish date
uk_cases['7_day_specimen'] = uk_cases['newCasesBySpecimenDate'].rolling(window=7).mean()
uk_cases['7_day_publish'] = uk_cases['newCasesByPublishDate'].rolling(window=7).mean()

# Thousand comma separated strings to be displayed in labels on graphs for
# easier reading.
uk_cases['newCasesBySpecimenDate_str'] = \
    uk_cases['newCasesBySpecimenDate'].apply(lambda x: "{:,}".format(x))
uk_cases['newCasesByPublishDate_str'] = \
    uk_cases['newCasesByPublishDate'].apply(lambda x: "{:,}".format(x))
uk_cases['7_day_specimen_str'] = \
    uk_cases['7_day_specimen'].apply(lambda x: "{:,}".format(round(x, 2)))
uk_cases['7_day_publish_str'] = \
    uk_cases['7_day_publish'].apply(lambda x: "{:,}".format(round(x, 2)))

# ------------------------
# Graph - daily cases UK
# Filename: daily_cases_uk
# ------------------------

fig = go.Figure()

# Daily cases (publish date) - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(uk_cases['date']),
        y=list(uk_cases['7_day_publish']),
        marker=dict(color='rgb(150, 65, 65)'),
        showlegend=False,
        customdata=np.stack((
            uk_cases['7_day_publish_str'], 
            uk_cases['newCasesByPublishDate_str']
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
        y=list(uk_cases['newCasesByPublishDate']),
        marker=dict(color='rgb(200, 200, 200)'),
        showlegend=False,
        hoverinfo='skip'
    )
)

# Daily cases (specimen date) - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(uk_cases['date']),
        y=list(uk_cases['7_day_specimen']),
        marker=dict(color='rgb(150, 65, 65)'),
        showlegend=False,
        visible=False,
        customdata=np.stack((
            uk_cases['7_day_specimen_str'], 
            uk_cases['newCasesBySpecimenDate_str']
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
        y=list(uk_cases['newCasesBySpecimenDate']),
        marker=dict(color='rgb(200, 200, 200)'),
        showlegend=False,
        visible=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    template=template,
    title="<b>Daily Cases by Published Date</b><br><sup>7 day average",
    yaxis=dict(
        title="Daily Cases",
    ),
    annotations=[
        dict(
            x=0, y=-0.1,
            text="Source: gov.uk",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ],
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                dict(label="Published",
                     method='update',
                     args=[{'visible': [True, True, False, False]},
                           {'title': "<b>Daily Cases by Published Date</b><br><sup>7 day average"}]),
                dict(label="Specimen",
                     method='update',
                     args=[{'visible': [False, False, True, True]},
                           {'title': "<b>Daily Cases by Specimen Date</b><br><sup>7 day average"}]),
            ])
        )
    ]
)

fig.write_html('graphs/cases/daily_cases_uk.html')

# ----------------
# Deaths data - UK
# ----------------

# Date is only available from the 6th March 2020
uk_deaths = uk[uk['date'] >= '2020-03-06'][['date', 'newDeaths28DaysByDeathDate']].copy()

# 7 day rolling average of deaths
uk_deaths['7_day_28_day'] = uk_deaths['newDeaths28DaysByDeathDate'].rolling(window=7).mean()

# Thousand comma separated strings to be displayed in labels on graphs for
# easier reading.
uk_deaths['newDeaths28DaysByDeathDate_str'] = \
    uk_deaths['newDeaths28DaysByDeathDate'].apply(lambda x: "{:,}".format(x).replace(".0", ""))
uk_deaths['7_day_28_day_str'] = \
    uk_deaths['7_day_28_day'].apply(lambda x: "{:,}".format(round(x, 2)))

# -------------------------
# Graph - daily deaths UK
# Filename: daily_deaths_uk
# -------------------------

fig = go.Figure()

# Daily deaths - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(uk_deaths['date']),
        y=list(uk_deaths['7_day_28_day']),
        marker=dict(color='rgb(150, 65, 65)'),
        showlegend=False,
        customdata=np.stack((
            uk_deaths['7_day_28_day_str'], 
            uk_deaths['newDeaths28DaysByDeathDate_str']
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
        y=list(uk_deaths['newDeaths28DaysByDeathDate']),
        marker=dict(color='rgb(200, 200, 200)'),
        showlegend=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    template=template,
    title="<b>Daily Deaths Within 28 Days of a Positive COVID-19 Test</b><br><sup>7 day average",
    yaxis=dict(
        title="Daily Deaths"
    ),
    annotations=[
        dict(
            x=0, y=-0.1,
            text="Source: gov.uk",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/deaths/daily_deaths_uk.html')

# -----------------------------
# Hospital admissions data - UK
# -----------------------------

# UK admissions data only available from 23rd March 2020
uk_admissions = uk[uk['date'] >= '2020-03-23'][['date', 'newAdmissions']].copy()

# 7 day rolling average of admissions
uk_admissions['7_day_admissions'] = uk_admissions['newAdmissions'].rolling(window=7).mean()

# Thousand comma separated strings to be displayed in labels on graphs for
# easier reading.
uk_admissions['newAdmissions_str'] = \
    uk_admissions['newAdmissions'].apply(lambda x: "{:,}".format(x).replace(".0", ""))
uk_admissions['7_day_admissions_str'] = \
    uk_admissions['7_day_admissions'].apply(lambda x: "{:,}".format(round(x, 2)))

# -----------------------------
# Graph - daily admissions UK
# Filename: daily_admissions_uk
# -----------------------------

fig = go.Figure()

# UK admissions - 7 day rolling average
fig.add_trace(
    go.Scatter(
        x=list(uk_admissions['date']),
        y=list(uk_admissions['7_day_admissions']),
        marker=dict(color='rgb(150, 65, 65)'),
        showlegend=False,
        customdata=np.stack((
            uk_admissions['7_day_admissions_str'], 
            uk_admissions['newAdmissions_str']
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
        y=list(uk_admissions['newAdmissions']),
        marker=dict(color='rgb(200, 200, 200)'),
        showlegend=False,
        hoverinfo='skip'
    )
)

fig.update_layout(
    template=template,
    title="<b>Daily Hospital Admissions</b><br><sup>7 day average",
    yaxis=dict(
        title="Daily Admissions"
    ),
    annotations=[
        dict(
            x=0, y=-0.1,
            text="Source: gov.uk",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/admissions/daily_admissions_uk.html')

# =============================================================================
# Vaccinations data from gov.uk
# =============================================================================

vaccine_url = "https://api.coronavirus.data.gov.uk/v2/data?areaType=overview" \
              "&metric=cumPeopleVaccinatedFirstDoseByPublishDate" \
              "&metric=cumPeopleVaccinatedSecondDoseByPublishDate&format=csv"

vaccine = pd.read_csv(vaccine_url)

vaccine = vaccine[vaccine['date'] >= '2021-01-10'].sort_values('date')

# Create thousand commas separated strings to use in the plots as they are
# easier to read.
vaccine['cumPeopleVaccinatedFirstDoseByPublishDate_str'] = \
    vaccine['cumPeopleVaccinatedFirstDoseByPublishDate'].apply(lambda x: "{:,}".format(int(x)))
vaccine['cumPeopleVaccinatedSecondDoseByPublishDate_str'] = \
    vaccine['cumPeopleVaccinatedSecondDoseByPublishDate'].apply(lambda x: "{:,}".format(int(x)))

# ------------------------------------
# Graph - total number of vaccinations
# Filename: vaccine_total
# ------------------------------------

fig = go.Figure()

# Number of people vaccinated (1 dose)
fig.add_trace(
    go.Scatter(
        x=list(vaccine['date']),
        y=list(vaccine['cumPeopleVaccinatedFirstDoseByPublishDate']),
        marker=dict(color='rgb(150, 65, 65)'),
        name="1st Dose",
        text=vaccine['cumPeopleVaccinatedFirstDoseByPublishDate_str'],
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
        y=list(vaccine['cumPeopleVaccinatedSecondDoseByPublishDate']),
        marker=dict(color='darkblue'),
        name="2nd Dose",
        text=vaccine['cumPeopleVaccinatedSecondDoseByPublishDate_str'],
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
    title="<b>Number Who Have Received the 1st and 2nd Vaccine Dose (Publication Date)</b>",
    yaxis=dict(
        title="Vaccinations"
    ),
    annotations=[
        dict(
            x=0, y=-0.10,
            text="Source: gov.uk",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/vaccine/vaccine_total.html')

# -------------------------------
# Graph - percentage vaccinated
# Filename: percentage_vaccinated
# -------------------------------

# UK total population
uk_pop = population.iloc[0]['All ages']

dose_2_percent = vaccine['cumPeopleVaccinatedSecondDoseByPublishDate'].max() / uk_pop * 100
dose_1_percent = vaccine['cumPeopleVaccinatedFirstDoseByPublishDate'].max() / uk_pop * 100

x = [dose_2_percent, dose_1_percent]
y = [100 - dose_2_percent, 100 - dose_1_percent]

fig = go.Figure()

# Percentage of people who have received either 1 or 2 doses
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
        '%{x:.3f}%'
    )
)

# Percentage of people who have not received either 1 or 2 doses
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
    title="<b>% of UK Population Who Have Received Vaccination</b><br>" \
          "<sup>Source: gov.uk (Vaccinations by Publish Date)",
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
    height=140,
    margin=dict(t=45, b=0),
    plot_bgcolor='white'
)

fig.write_html('graphs/vaccine/percentage_vaccinated.html')

# ----------------------------
# Graph - daily vaccinations
# Filename: daily_vaccinations
# ----------------------------

# Daily vaccinations
vaccine['daily_1'] = vaccine['cumPeopleVaccinatedFirstDoseByPublishDate'].diff()
vaccine['daily_2'] = vaccine['cumPeopleVaccinatedSecondDoseByPublishDate'].diff()

# Create thousand commas separated strings to use in the plots as they are
# easier to read.
vaccine['daily_1_str'] = vaccine['daily_1'].apply(lambda x: "{:,}".format(x).replace(".0", ""))
vaccine['daily_2_str'] = vaccine['daily_2'].apply(lambda x: "{:,}".format(x).replace(".0", ""))

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
    title="<b>Daily Vaccinations (by Published Date)</b>",
    yaxis=dict(
        title="Daily Vaccinations"
    ),
    annotations=[
        dict(
            x=0, y=-0.12,
            text="Source: gov.uk",
            showarrow=False,
            xref='paper',
            yref='paper',
            xanchor='left',
            yanchor='auto',
            xshift=0,
            yshift=0,
            font=dict(
                size=11,
                color='dimgray'
            )
        )
    ]
)

fig.write_html('graphs/vaccine/daily_vaccinations.html')

# ------------------------------------------
# % of England Population Over 80 Vaccinated
# ------------------------------------------

# Date is released every Thursday and the URL contains the date therefore the
# date of the most recent Thursday needs to be found in the form
# 14-January-2021
date_range = pd.Series(pd.date_range('14-01-2021', '31-12-2021', freq='7D'))
date_today = pd.to_datetime(datetime.date.today())
most_recent_thursday = date_range[date_range.le(date_today)].max().strftime("%d-%B-%Y")

vaccine_80_url = "https://www.england.nhs.uk/statistics/wp-content/uploads/" \
                 "sites/2/2021/01/COVID-19-weekly-announced-vaccinations-" \
                 + most_recent_thursday + ".xlsx"

vaccines_80 = pd.read_excel(vaccine_80_url,
                            sheet_name='Vaccinations by Region & Age',
                            skiprows=11,
                            usecols='B,D,E,G,H')

vaccines_80 = vaccines_80[vaccines_80['Region of Residence'] == 'Total']

vaccines_80.columns = ['Region', 'Under 80 1st Dose', '80+ 1st Dose',
                       'Under 80 2nd Dose', '80+ 2nd Dose']

# -------------------------------------
# Graph - percentage vaccinated over 80
# Filename: percentage_vaccinated_80
# -------------------------------------

# UK population 80+ years old
pop = population[population['Name'] == 'UNITED KINGDOM'][list(range(80, 90)) + ["90+"]]
pop_over_80 = pop.iloc[0,:].sum()

dose_2_percent = vaccines_80['80+ 2nd Dose'].max() / pop_over_80 * 100
dose_1_percent = vaccines_80['80+ 1st Dose'].max() / pop_over_80 * 100

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
    title="<b>% of England Population Aged 80 or Over Who Have Received Vaccination"  \
          "(as of " + most_recent_thursday.replace("-", " ") + ")</b><br>" \
          "<sup>Source: NHS England",
    barmode='stack',
    legend_traceorder='normal',
    font=dict(
        family='Arial'
    ),
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
    height=140,
    margin=dict(t=45, b=0),
    plot_bgcolor='white'
)

fig.write_html('graphs/vaccine/percentage_vaccinated_80.html')

# =============================================================================
# Regional data
# =============================================================================

# -----
# Cases
# -----

regional_url = "https://api.coronavirus.data.gov.uk/v2/data?areaType=region" \
               "&metric=newCasesBySpecimenDate" \
               "&metric=newCasesByPublishDate" \
               "&metric=newDeaths28DaysByDeathDate&format=csv"

regional = pd.read_csv(regional_url)

regional['date'] = pd.to_datetime(regional['date'], format='%Y-%m-%d')
regional = regional.sort_values('date')

# Due to a change in reporting method, there is a large spike in cases on 1st
# July 2020. To estimate the actual daily cases, the average of the 3 days
# either side of 1st July is taken.
def july_1(df):
    df = df.reset_index()
    row = df[df['date']=='2020-07-01'].index[0]
    rows = list(range(row-3,row)) + list(range(row+1,row+4))
    mean = df.iloc[rows, :]['newCasesByPublishDate'].mean()
    df.loc[df['date']=='2020-07-01', 'newCasesByPublishDate'] = mean
    return df

regional = regional.groupby('areaName', as_index=False).apply(july_1)

# 7 day rolling average for cases by specimen date and publish date, and daily
# deaths.
regional[
    ['7_day_specimen', '7_day_publish', '7_day_deaths']
        ] = regional.groupby(['areaName', 'areaCode'], as_index=False)[
    ['newCasesBySpecimenDate', 'newCasesByPublishDate', 'newDeaths28DaysByDeathDate']
        ].apply(lambda x: x.rolling(window=7, min_periods=1).mean())

regional = regional.merge(population[['Code', 'All ages']],
                          left_on='areaCode',
                          right_on='Code',
                          how='left')

regional['specimen_per_100000'] = regional['7_day_specimen'] / regional['All ages'] * 100000
regional['publish_per_100000'] = regional['7_day_publish'] / regional['All ages'] * 100000
regional['deaths_per_100000'] = regional['7_day_deaths'] / regional['All ages'] * 100000

regional['7_day_specimen_str'] = regional['7_day_specimen'].apply(lambda x: "{:,}".format(round(x, 2)))
regional['7_day_publish_str'] = regional['7_day_publish'].apply(lambda x: "{:,}".format(round(x, 2)))
regional['7_day_deaths_str'] = regional['7_day_deaths'].apply(lambda x: "{:,}".format(round(x, 2)))

regional['specimen_per_100000_str'] = regional['specimen_per_100000'].apply(lambda x: "{:,}".format(round(x, 2)))
regional['publish_per_100000_str'] = regional['publish_per_100000'].apply(lambda x: "{:,}".format(round(x, 2)))
regional['deaths_per_100000_str'] = regional['deaths_per_100000'].apply(lambda x: "{:,}".format(round(x, 3)))


# --------------------------------------
# Graph - regional cases by publish date
# Filename: region_cases_publish
# --------------------------------------

regions = [
    'North West', 'Yorkshire and The Humber', 'North East',
    'West Midlands', 'East Midlands', 'East of England',
    'South West', 'London', 'South East'
]

rows = [1,1,1,2,2,2,3,3,3]
cols = [1,2,3,1,2,3,1,2,3]

fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

# Daily cases by region (publish date)
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['areaName'] == region]),
            y=list(regional['7_day_publish'][regional['areaName'] == region]),
            showlegend=False,
            text=regional['7_day_publish_str'],
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
        row, col
    )

# Daily cases by region per 100,000 (publish date)
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['areaName'] == region]),
            y=list(regional['publish_per_100000'][regional['areaName'] == region]),
            showlegend=False,
            visible=False,
            text=regional['publish_per_100000_str'],
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
        row, col
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
    title="<b>Cases by Published Date</b><br><sup>7 day average",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=800,
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                    dict(label="Cases",
                         method='update',
                         args=[{'visible': [True]*9 + [False]*9},
                                 {'title': "<b>Cases by Published Date</b><br><sup>7 day average"}]),
                    dict(label="Cases per 100,000",
                         method='update',
                         args=[{'visible': [False]*9 + [True]*9},
                                 {'title': "<b>Cases per 100,000 by Published Date</b><br><sup>7 day average"}]),
                        ]
            )
    )]
)

fig.add_annotation(
    dict(
        x=0, y=-0.08,
        text="Source: gov.uk, ONS",
        showarrow=False,
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='auto',
        xshift=0,
        yshift=0,
        font=dict(
            size=11,
            color='dimgray'
        )
    )
)

fig.write_html('graphs/cases/region_cases_publish.html')

# ---------------------------------------
# Graph - regional cases by specimen date
# Filename: region_cases_specimen
# ---------------------------------------

fig = make_subplots(3, 3, subplot_titles=(regions), shared_xaxes=True)

# Daily cases by region (specimen date)
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['areaName'] == region]),
            y=list(regional['7_day_specimen'][regional['areaName'] == region]),
            showlegend=False,
            text=regional['7_day_specimen_str'],
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
        row, col
    )

# Daily cases by region per 100,000 (specimen date)
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['areaName'] == region]),
            y=list(regional['specimen_per_100000'][regional['areaName'] == region]),
            showlegend=False,
            visible=False,
            text=regional['specimen_per_100000_str'],
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
        row, col
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
    title="<b>Cases by Specimen Date</b><br><sup>7 day average",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=800,
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                    dict(label="Cases",
                         method='update',
                         args=[{'visible': [True]*9 + [False]*9},
                                 {'title': "<b>Cases by Specimen Date</b><br><sup>7 day average"}]),
                    dict(label="Cases per 100,000",
                         method='update',
                         args=[{'visible': [False]*9 + [True]*9},
                                 {'title': "<b>Cases per 100,000 by Specimen Date</b><br><sup>7 day average"}]),
                        ]
            )
    )]
)

fig.add_annotation(
    dict(
        x=0, y=-0.08,
        text="Source: gov.uk, ONS",
        showarrow=False,
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='auto',
        xshift=0,
        yshift=0,
        font=dict(
            size=11,
            color='dimgray'
        )
    )
)

fig.write_html('graphs/cases/region_cases_specimen.html')

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
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['areaName'] == region]),
            y=list(regional['7_day_deaths'][regional['areaName'] == region]),
            showlegend=False,
            text=regional['7_day_deaths_str'],
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
        row, col
    )

# Daily deaths by region per 100,000
for region, row, col in zip(regions, rows, cols):
    fig.add_trace(
        go.Scatter(
            x=list(regional['date'][regional['areaName'] == region]),
            y=list(regional['deaths_per_100000'][regional['areaName'] == region]),
            showlegend=False,
            visible=False,
            text=regional['deaths_per_100000_str'],
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
        row, col
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
    title="<b>Deaths</b><br><sup>7 day average",
    font=dict(
        family='Arial'
    ),
    plot_bgcolor='white',
    height=800,
    updatemenus=[
        dict(
            direction='down',
            x=1,
            xanchor='right',
            y=1.1,
            yanchor='top',
            buttons=list([
                    dict(label="Deaths",
                         method='update',
                         args=[{'visible': [True]*9 + [False]*9},
                                 {'title': "<b>Deaths</b><br><sup>7 day average"}]),
                    dict(label="Deaths per 100,000",
                         method='update',
                         args=[{'visible': [False]*9 + [True]*9},
                                 {'title': "<b>Deaths per 100,000</b><br><sup>7 day average"}]),
                        ]
            )
    )]
)

fig.add_annotation(
    dict(
        x=0, y=-0.08,
        text="Source: gov.uk, ONS",
        showarrow=False,
        xref='paper',
        yref='paper',
        xanchor='left',
        yanchor='auto',
        xshift=0,
        yshift=0,
        font=dict(
            size=11,
            color='dimgray'
        )
    )
)

fig.write_html('graphs/deaths/region_daily_deaths.html')

# =============================================================================
# Council data
# =============================================================================

council_url = "https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla" \
              "&metric=newCasesByPublishDate" \
              "&metric=newDeaths28DaysByDeathDate&format=csv"

council = pd.read_csv(council_url)

council['date'] = pd.to_datetime(council['date'], format='%Y-%m-%d')
council = council.sort_values('date')

# Group by area and take the sum of cases in the past 7 days
council_week = council.groupby(
    ['areaCode', 'areaName'], as_index=False)[
    ['newCasesByPublishDate', 'newDeaths28DaysByDeathDate']
        ].apply(lambda x: x.iloc[-7:].sum())

council_week = council_week.merge(population[['Code', 'All ages']],
                                  left_on='areaCode',
                                  right_on='Code',
                                  how='left')

council_week['cases_per_100000'] = council_week['newCasesByPublishDate'] / council_week['All ages'] * 100000
council_week['deaths_per_100000'] = council_week['newDeaths28DaysByDeathDate'] / council_week['All ages'] * 100000

# --------------------------------------------
# Table - cases in the past 7 days per 100,000
# Filename: cases_local_area
# --------------------------------------------

table_config = {'displayModeBar': False}
colors = ['rgb(240,240,240)', 'rgb(240,230,230)']*150

# Sort by cases and create a rank column for display in the table
df_cases = council_week.sort_values('cases_per_100000', ascending=False).reset_index()
df_cases['rank'] = df_cases.index+1

# Sort councils alphabetically and create a rank column for display in the
# table
df_alpha = council_week.sort_values('areaName').reset_index()
df_alpha['rank'] = df_alpha.index+1

table = go.Figure()

# Table with values sorted cases
table.add_trace(
    go.Table(
        header=dict(
            values=['', '<b>Area</b>', '<b>Cases in Past 7 Days / 100,000</b>'],
            font=dict(
                color='white'
            ),
            align='left',
            height=30,
            fill_color='rgba(150, 65, 65, 0.9)'
        ),
        cells=dict(
            values=[list(df_cases['rank']),
                    list(df_cases['areaName']),
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
            values=['', '<b>Area</b>', '<b>Cases in Past 7 Days / 100,000</b>'],
            font=dict(
                color='white'
            ),
            align='left',
            height=30,
            fill_color='rgba(150, 65, 65, 0.9)'
        ),
        cells=dict(
            values=[list(df_alpha['rank']),
                    list(df_alpha['areaName']),
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
    title="<b>Cases in the Past 7 Days per 100,000</b><br><sup>Cases by Date Published",
    font=dict(
        family='Arial'
    ),
    width=600,
    height=600,
    margin=dict(
        b=0,
        t=50,
        l=0,
        r=0
    ),
    updatemenus=[
        dict(
            direction='down',
            x=0.95,
            xanchor='right',
            y=1.10,
            yanchor='top',
            buttons=list([
                dict(label="Sort: Cases",
                     method='update',
                     args=[{'visible': [True, False]}]),
                dict(label="Sort: Area Name",
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
df_deaths = council_week.sort_values('deaths_per_100000', ascending=False).reset_index()
df_deaths['rank'] = df_deaths.index+1

table = go.Figure()

# Table with values sorted by deaths
table.add_trace(
    go.Table(
        header=dict(
            values=['', '<b>Area</b>', '<b>Deaths in Past 7 Days / 100,000</b>'],
            font=dict(
                color='white'
            ),
            align='left',
            height=30,
            fill_color='rgba(150, 65, 65, 0.9)'
        ),
        cells=dict(
            values=[list(df_deaths['rank']),
                    list(df_deaths['areaName']),
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
            values=['', '<b>Area</b>', '<b>Deaths in Past 7 Days / 100,000</b>'],
            font=dict(
                color='white'
            ),
            align='left',
            height=30,
            fill_color='rgba(150, 65, 65, 0.9)'
        ),
        cells=dict(
            values=[list(df_alpha['rank']),
                    list(df_alpha['areaName']),
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
    title="<b>Deaths in the Past 7 Days per 100,000</b>",
    font=dict(
        family='Arial'
    ),
    width=600,
    height=600,
    margin=dict(
        b=0,
        t=20,
        l=0,
        r=0
    ),
    updatemenus=[
        dict(
            direction='down',
            x=0.95,
            xanchor='right',
            y=1.10,
            yanchor='top',
            buttons=list([
                dict(label="Sort: Deaths",
                     method='update',
                     args=[{'visible': [True, False]}]),
                dict(label="Sort: Area Name",
                     method='update',
                     args=[{'visible': [False, True]}]),
            ])
        )
    ]
)

table.write_html('graphs/deaths/deaths_local_area.html', config=table_config)
