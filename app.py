from dash import Dash, page_container, html
import dash_bootstrap_components as dbc

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.CYBORG])

app.layout = html.Div([
   page_container
], className='container-xxl mt-2 mb-2')

if __name__ == '__main__':
    app.run(debug=True)