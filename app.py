from dash import Dash, html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
import json

# Dataset
df = pd.read_parquet('dataset/HIST_COVID.parquet.gzip')


brasil_geo = json.load(open('geojson/brazil_geo.json', 'r'))
token = open(".mapbox_token").read()
dados = ['casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos']
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H5('Evolução do COVID-19'),
                dbc.Button(id='location-button', children='Brasil', color='primary', size='lg')
            ]),
            html.P('informe a data na qual deseja obter as informações', style={'margin-top':'30px'}),
            dcc.DatePickerSingle(id='data-select', 
                                min_date_allowed=df['data'].min(),
                                max_date_allowed=df['data'].max(),
                                date=df['data'].max(),
                                display_format='MMMM D, YYYY', style={"border":"opx solid black"}),
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Samp('Casos Acumulados'),
                            html.H3(id='casos-acumulados-data'),
                            html.Samp('Novos casos na data'),
                            html.H5(id='casos-data')
                        ])
                    )
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Samp('Óbitos Acumulados'),
                            html.H3(id='obitos-acumulados-data'),
                            html.Samp('Óbitos na data'),
                            html.H5(id='obitos-data')
                        ])
                    )
                )
            ]),
            html.P('Selecione qual tipo de dado deseja visualizar'),
            dcc.Dropdown(id='select-type', value=dados[0], options=dados),
            dcc.Loading(dcc.Graph(id='graph-bar', config={'displayModeBar':False, 'showTips':False}))
        ], md=5),
        dbc.Col([
            dcc.Loading(dcc.Graph(id='graph-map', config={'displayModeBar':False, 'showTips':False}, style={'height':'100vh'}))
        ], md=7)    
    ])
], fluid=True)

@app.callback(
    Output('graph-map','figure'),
    Input('data-select', 'date')
)
def graph_map(data):
    df_filtered = df[df['data']==data]
    fig = px.choropleth_mapbox(df_filtered, locations='estado', 
                               color='casosNovos', geojson=brasil_geo,
                               center={"lat": -14.95, "lon": -55.78},
                               zoom=3.9, opacity=0.4,
                               color_continuous_scale='Redor',
                               hover_data={'estado':True, 
                                           'casosAcumulado': True, 
                                           'obitosNovos':True})
    fig.update_layout(mapbox_accesstoken=token,
                      margin={'l':0, 't':0,'r':0,'b':0},
                      showlegend=False, paper_bgcolor='#242424', 
                      plot_bgcolor='#242424', autosize=True)
    return fig

@app.callback(
    Output('graph-bar', 'figure'),
    Input('select-type', 'value')
)
def graph_col_1(select_type):
    df_fig = df.groupby('data')[select_type].sum()
    fig = go.Figure(go.Scatter(x=df_fig.index, y=df_fig))
    fig.update_layout(autosize=True,
                      margin={'l':10,'t':10, 'r':10, 'b':10},
                      paper_bgcolor='#242424', plot_bgcolor='#242424',
                      height=350)
    return fig

@app.callback(
    [
        Output('casos-acumulados-data','children'),
        Output('casos-data','children'),
        Output('obitos-acumulados-data','children'),
        Output('obitos-data','children'),
    ],
    Input('data-select', 'date')
)
def update_cards(data):
    df_filtered = df[df['data']==data]

    casos_acumulado = f"{int(df_filtered['casosAcumulado'].sum()):,}".replace(',','.')
    casos_novos = f"{int(df_filtered['casosNovos'].sum()):,}".replace(',','.')
    obitos_acumulado = f"{int(df_filtered['obitosAcumulado'].sum()):,}".replace(',','.')
    obito_novos =  f"{int(df_filtered['obitosNovos'].sum()):,}".replace(',','.')
    return casos_acumulado, casos_novos, obitos_acumulado, obito_novos

if __name__ == '__main__':
    app.run(debug=True)