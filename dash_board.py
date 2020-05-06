import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

from data_loader import preprocess_data

# Styles
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
colors = {
    'background': '#ffffff',
    'text': '#4f5250'
}

# End styles #####################################################################
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def prep_data_viz():
    all_topics, document_topics = preprocess_data(db=True)
    # All topics part
    all_topics = pd.DataFrame.from_dict(all_topics)
    n_topics = len(all_topics.columns)
    topics_flat = get_flat_topic_df(all_topics, n_topics)
    return topics_flat, None


def get_flat_topic_df(all_topics, n_topics):
    """
    Get df with Multiindex to plot easier
    :param all_topics: the IDs of the topics as list
    :param n_topics: the number of topics in the model
    :return: df with index [TopicID, Word] and weight
    """
    init_topic = all_topics.columns[0]
    # TODO refator due duplication.
    topics_flat = all_topics[[init_topic]].copy().dropna(axis=0)
    topics_flat.index.rename("Word", inplace=True)
    topics_flat.columns = ["weight"]
    topics_flat["TopicID"] = init_topic
    topics_flat.set_index("TopicID", inplace=True, append=True)  # ADD the index
    topics_flat = topics_flat.reorder_levels(["TopicID", "Word"])
    for init_topic in all_topics.columns[1:]:
        tf = all_topics[[init_topic]].copy().dropna(axis=0)
        tf.index.rename("Word", inplace=True)
        tf.columns = ["weight"]
        tf["TopicID"] = init_topic
        tf.set_index("TopicID", inplace=True, append=True)  # ADD the index
        tf = tf.reorder_levels(["TopicID", "Word"])
        topics_flat = pd.concat([topics_flat, tf], axis=0)
    topics_flat = pd.concat(
        [topics_flat.
             iloc[topics_flat.index.get_level_values("TopicID") == x, :]
             .copy().sort_values(by="weight", ascending=False) for x in range(n_topics)],
        axis=0)

    return topics_flat


# Define working data
flat_data, document_topics = prep_data_viz()
# print("upd")

print(f"Rows {flat_data['weight'].shape}")
All_topics = dcc.Graph(
    id='topic_model-graph',
    figure={
        'data': [go.Bar(x=flat_data["weight"].values.tolist(),
                        y=flat_data.index.get_level_values("Word").values.tolist(),
                        orientation='h')],
        'layout': {
            'title': 'Dash Data Visualization',
            "height": "500"
        }
    }
)

left_div = html.Div(
    dcc.Graph(id='value-index'),
    className='col s12 m6',
    style={"width": "50%", "float": "left"}
)
right_div = html.Div(
    All_topics,
    className='col s12 m6',
    style={"width": "50%", "float": "right", "height": "800px"}
)

app.layout = html.Div(children=[
    html.H1(children='LDA Topic Models by TK', style={
        'textAlign': 'center',
        'color': colors['text'],
        'width': "100%"
    }),

    html.Div(children='''
        Dash: A web application framework for Python.
    '''),

    # Start the left right mode
    html.Div(className='row',
             style={"width": "100%", 'display': 'flex', 'align-items': 'center', 'justify-content': 'center',
                    "margin": "auto"},
             children=[left_div, right_div])
],
    style={'backgroundColor': colors['background'], "height": "800px"}
)

if __name__ == '__main__':
    app.run_server(debug=True)
