# ======================================================================
# Creates plots summarising data on cases, deaths, hospitalisations and
# vaccinations using data from Folkhälsomyndigheten, Socialstyrelsen and
# Statistiska centralbyrån.
# ======================================================================

import pandas as pd
import plotly.graph_objects as go

import covid_cases
import covid_deaths
import covid_hospitalisations
import covid_vaccinations


# Graph template
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

# Configuration of the mode bar buttons for the Plotly plots.
plot_config={
    'modeBarButtonsToRemove': [
        'toggleSpikelines', 'hoverClosestCartesian', 'hoverCompareCartesian',
        'lasso2d', 'toggleSpikelines', 'autoScale2d', 'zoom2d'
    ]
}

# Population data from ONS
population = pd.read_excel(
    'data/uk_population.xlsx',
    sheet_name='MYE2 - Persons',
    skiprows=4)

population = population.melt(
    id_vars=['Name', 'Code'],
    value_vars=list(range(90)) + ['90+'],
    var_name='age',
    value_name='population')

# Dictionary of modules where the value for each dictionary item is a
# list. The first item of the list is the name of the method's main
# function. The second is a list containing the arguments for the main
# function.
modules_dict = {
    'cases': [covid_cases.main, [population, template, plot_config]],
    'deaths': [covid_deaths.main, [population, template, plot_config]],
    'hospital': [covid_hospitalisations.main, [template, plot_config]],
    'vaccinations': [covid_vaccinations.main, [population, template,
                                               plot_config]],
}


def main():
    """Ask which modules to run and then run them."""
    print("Choose from: [all, cases, deaths, hospital, vaccinations]")
    modules = input("              ")

    if modules == 'all':
        for m in modules_dict:
            modules_dict[m][0](*modules_dict[m][1])
    else:
        for m in modules.split(', '):
            modules_dict[m][0](*modules_dict[m][1])


if __name__ == "__main__":
    main()
