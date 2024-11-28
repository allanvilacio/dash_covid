from dash import Dash, html, dcc, Output, Input, callback_context, register_page, callback
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import plotly.graph_objects as go
from decouple import config
from numerize import numerize
import pandas as pd
import json

theme = 'cyborg'
brasil_geo = json.load(open('geojson/brazil_geo.json', 'r'))
load_figure_template(theme)
register_page(__name__, path='/')

TOKEN_MAPBOX = config('TOKEN_MAPBOX')
dados = {'casosAcumulado':'Casos acumulado' , 'casosNovos':'Casos novos',
          'obitosAcumulado':'Obitos acumulado', 'obitosNovos':'Obitos novos'}

layout = dbc.Row([
    dbc.Col([
        html.Div([
                html.H5('Evolução do COVID-19'),
                dbc.Button(id='location-button', children='BRASIL', className='btn btn-primary btn-lg')
            ]),
        html.Div([
            html.P('Informe a data na qual deseja obter as informações', className='m-0'),
            dcc.DatePickerRange(
                id='data-select',
                start_date=pd.Timestamp(year=pd.Timestamp.today().year, month=1, day=1).date(),
                end_date=pd.Timestamp.today().date(),
                display_format='DD/MM/YYYY'
            ),
            
        ], className='pt-3 pb-3'),
        dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.Samp('Casos Acumulados'),
                            html.H4(id='casos-acumulados-data', style={"color": "#FFFF66"}),  
                        ], className='p-3' ), className='h-100 text-center'
                    )
                    ],
                    className='col-12 col-md-6'
                ),
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.Samp('Óbitos Acumulados'),
                            html.H4(id='obitos-acumulados-data', style={"color": "#DF2935"}),
                        ], className='p-3'), className='h-100 text-center p-0'
                    )
                    ],
                    className='col-12 col-md-6'
                )
        ], className='g-2'),
        dbc.Row([
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Samp('Novos casos na data'),
                        html.H5(id='casos-data', style={"color": "#FFFF66"})
                    ], className='p-3'), className='h-100 text-center'
                ),
            ], className='col-12 col-md-6'),
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.Samp('Óbitos na data'),
                        html.H5(id='obitos-data', style={"color": "#DF2935"})
                    ], className='p-3'), className='h-100 text-center'
                ),
            ], className='col-12 col-md-6'),
        ], className='g-2 pt-2'),

        html.Div([
            html.P('Selecione qual tipo de dado deseja visualizar' ,className='m-0'),
            dcc.Dropdown(id='select-type', value='casosAcumulado', options=dados, clearable=False),
        ], className='pt-3 pb-2'),

        dcc.Loading(
            dcc.Graph(id='graph-bar', config={'displayModeBar':False, 'showTips':False})
        )
        
    ], className='col-12 col-md-5'),


    dbc.Col([
        dcc.Loading(
            [dcc.Graph(id='graph-map', config={'displayModeBar': False, 'showTips': False}, 
                       style={'height':'930px'})]
            ),
        ], 
            className='col-12 col-md-7')
], className='g-2')


@callback(
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

@callback(
    [
        Output('casos-acumulados-data','children'),
        Output('casos-data','children'),
        Output('obitos-acumulados-data','children'),
        Output('obitos-data','children'),
    ],
    [
        Input('data-select', 'start_date'),
        Input('data-select', 'end_date'),
        Input('location-button', 'children')
    ]
)
def update_cards(start_date, end_date, location):

    range_date = pd.date_range(start_date, end_date)
    
    df_fig = pd.read_parquet('dataset/HIST_COVID.parquet.gzip', 
                             columns=['estado','casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos'],
                             filters=[('data', 'in', range_date)])
 
    df_fig = df_fig if location=='BRASIL' else df_fig[df_fig['estado']==location]


    df_fig = (df_fig[['casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos']]
                   .sum()
                   .apply(lambda x:numerize.numerize(x, 2).replace('.',',') ))

    return (df_fig['casosAcumulado'], df_fig['casosNovos'], 
            df_fig['obitosAcumulado'], df_fig['obitosNovos'])

@callback(
    Output('graph-bar', 'figure'),
    [
        Input('select-type', 'value'),
        Input('location-button', 'children'),
        Input('data-select', 'start_date'),
        Input('data-select', 'end_date'),
    ]
)
def update_graph_bar(select_type, location, start_date, end_date ):
    range_date = pd.date_range(start_date, end_date)
    
    df_fig = pd.read_parquet('dataset/HIST_COVID.parquet.gzip', 
                             columns=['estado','data','casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos'],
                             filters=[('data', 'in', range_date)])
 
    df_fig = df_fig if location=='BRASIL' else df_fig[df_fig['estado']==location]

    df_fig = df_fig.groupby('data')[select_type].sum()

    fig = go.Figure()

    if select_type in ['casosAcumulado', 'obitosAcumulado']:
        fig.add_trace(go.Scatter(x=df_fig.index, y=df_fig, line_shape='spline', name=''))
        
    else:
        fig.add_trace(go.Bar(x=df_fig.index, y=df_fig, name=''))

    fig.update_traces(
                      hovertemplate='<br>'.join([
                          '%{x|%d/%m/%y}: %{y:,.4s}',
                          ])
                )
    fig.update_layout(autosize=True,
                     margin={'l':10,'t':10, 'r':10, 'b':10},
                     template=theme)
    return fig

@callback(
    Output('graph-map','figure'),
    [
        Input('data-select', 'start_date'),
        Input('data-select', 'end_date'),        
    ]
)
def graph_map(start_date, end_date):
    range_date = pd.date_range(start_date, end_date)
    
    df_fig = pd.read_parquet('dataset/HIST_COVID.parquet.gzip', 
                             columns=['estado','casosAcumulado', 'casosNovos', 'obitosAcumulado', 'obitosNovos'],
                             filters=[('data', 'in', range_date)])

    fig = px.choropleth_mapbox(df_fig, locations='estado', 
                               color='casosNovos', geojson=brasil_geo,
                               center={"lat": -14.95, "lon": -54.38},
                               zoom=3.5, opacity=0.4,
                               color_continuous_scale='Redor',
                               hover_data={'estado':True, 
                                            'casosNovos':True,
                                            'casosAcumulado': True,
                                            'obitosNovos':True,
                                            'obitosAcumulado':True
                                            },
                                labels={ 'casosNovos': 'Novos Casos', 'casosAcumulado': 'Casos Acumulados',
                                         'obitosNovos': 'Óbitos Novos', 'obitosAcumulado': 'Óbitos Acumulados'}
                            )
    fig.update_traces(
                      hovertemplate='<br>'.join([
                          'Estado: %{customdata[0]}',
                          'Casos novos: %{customdata[1]:,.4s}',
                          'Casos acumulado: %{customdata[2]:,.4s}',
                          'Obitos novos: %{customdata[3]:,.4s}',
                          'Obitos acumulado: %{customdata[4]:,.4s}'])
                )

    fig.update_layout(mapbox_accesstoken=TOKEN_MAPBOX, separators=',',
                      margin={'l':0, 't':0,'r':0,'b':0},
                      template=theme, autosize=True)
    
    return fig

