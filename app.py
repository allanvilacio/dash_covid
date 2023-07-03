from dash import Dash, html, dcc, Output, Input, callback_context
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
            ], style={'padding': '20px 0px'}),
            html.P('informe a data na qual deseja obter as informações'),
            dcc.DatePickerSingle(id='data-select', 
                                min_date_allowed=df['data'].min(),
                                max_date_allowed=df['data'].max(),
                                date=df['data'].max(),
                                display_format='MMMM D, YYYY'),
            dbc.Row([
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Samp('Casos Acumulados'),
                            html.H3(id='casos-acumulados-data', style={"color": "#FFFF66"}),
                            html.Samp('Novos casos na data'),
                            html.H5(id='casos-data', style={"color": "#FFFF66"})
                        ], style={'padding':'10px'})
                    )
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody([
                            html.Samp('Óbitos Acumulados'),
                            html.H3(id='obitos-acumulados-data', style={"color": "#DF2935"}),
                            html.Samp('Óbitos na data'),
                            html.H5(id='obitos-data', style={"color": "#DF2935"})
                        ], style={'padding':'10px'})
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
        Output('location-button', 'children'),
        [
            Input('graph-map', 'clickData'),
            Input('location-button', 'n_clicks')
        ]
    )
def update_location_button(clickData, n_clicks):
    evento = callback_context.triggered[0]['prop_id']
    location = 'BRASIL'
    if evento == 'graph-map.clickData':
        location = clickData['points'][0]['location']
    return location

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
    [
        Input('select-type', 'value'),
        Input('location-button', 'children')
    ]
)
def graph_col_1(select_type, location):
    df_fig = df.copy() if location=='BRASIL' else df[df['estado']==location]
    df_fig = df_fig.groupby('data')[select_type].sum()
    fig = go.Figure()
    if select_type in ['casosAcumulado', 'obitosAcumulado']:
        fig.add_trace(go.Scatter(x=df_fig.index, y=df_fig))
    else:
        fig.add_trace(go.Bar(x=df_fig.index, y=df_fig))

    fig.update_layout(autosize=True,
                      margin={'l':10,'t':10, 'r':10, 'b':10},
                      paper_bgcolor='#242424', plot_bgcolor='#242424',
                      height=400)
    return fig

@app.callback(
    [
        Output('casos-acumulados-data','children'),
        Output('casos-data','children'),
        Output('obitos-acumulados-data','children'),
        Output('obitos-data','children'),
    ],
    [
        Input('data-select', 'date'),
        Input('location-button', 'children')
    ]
)
def update_cards(data, location):
    data='2022-07-05'
    df_filtered = df[df['data']==data]
    df_filtered = df_filtered if location=='BRASIL' else df_filtered[df_filtered['estado']==location]
    df_filtered = (df_filtered[['casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos']]
                   .sum()
                   .apply(lambda x: f'{int(x):,}'.replace(',','.')))

    return (df_filtered['casosAcumulado'], df_filtered['casosNovos'], 
            df_filtered['obitosAcumulado'], df_filtered['obitosNovos'])


if __name__ == '__main__':
    app.run(debug=True)