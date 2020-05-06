import dash
import dash_core_components as dcc
import dash_html_components as html
from data_loader import preprocess_data
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

all_topics, document_topics = preprocess_data(db=False)
print(all_topics)
all_topics_ = all_topics.sum(axis=1).values.reshape([-1,1])
all_topics_[:,1] = 0
for x in all_topics.columns:
    for j in range(len(all_topics_)):
        if all_topics.iloc[j,:].loc[:]

graph_left = dcc.Graph(
    id='example-graph',
    figure={
        'data': [
            {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
            {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
        ],
        'layout': {
            'title': 'Dash Data Visualization'
        }
    }
)

left_div = html.Div(
    dcc.Graph(id='value-index'),
    className='col s12 m6',

)
right_div = html.Div(
    graph_left,
    className='col s12 m6',
)

app.layout = html.Div(children=[
    html.H1(children='Hello Dash'),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    # Start the left right mode
    html.Div(className='row',
             style={'display': 'flex'},
             children=[left_div, right_div])

])

if __name__ == '__main__':
    app.run_server(debug=True)
