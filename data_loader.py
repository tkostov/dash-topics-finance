import json

import pandas as pd
from cassandra.cluster import Cluster
from sklearn.decomposition import PCA


def get_json_data():
    """
    Loads test data
    :return:
    """
    with open("data_example/document_topics.json", "rt") as f:
        document_topics_dict = json.load(f)

    with open("data_example/topic_model.json", "rt") as f:
        all_topics = json.load(f)

    return all_topics, document_topics_dict


def preprocess_data(db=True):
    """

    :param db:
    :return:
    """
    if db:
        all_topics, document_topics_dict = get_db_data()
    else:
        all_topics, document_topics_dict = get_json_data()

    for x in all_topics.keys():
        accu = 0
        for j in all_topics[x].keys():
            accu += all_topics[x][j]
        for j in all_topics[x].keys():
            all_topics[x][j] /= accu # normalize


    for ix, x in enumerate(document_topics_dict["Document_Topics"]):
        accu = 0
        for j in document_topics_dict["Document_Topics"][ix]["_2"]["values"]:
            accu+= j
        for ij, j in enumerate(document_topics_dict["Document_Topics"][ix]["_2"]["values"]):
            document_topics_dict["Document_Topics"][ix]["_2"]["values"][ij] /= accu # normalize


    all_topics_ = {}
    for x in all_topics.keys():
        all_topics_[int(x)] = all_topics[x]

    document_topics = {}
    for x in document_topics_dict["Document_Topics"]:
        document_topics[x["_1"]] = x["_2"]["values"]

    # topics_dataframe = pd.DataFrame.from_dict(all_topics_)

    return all_topics_, document_topics


def get_db_data():
    """

    :return:
    """
    # TODO change the cluster Location when deploy
    cluster = Cluster()  # TODO ADD location

    # select cluster name
    session = cluster.connect("seminar")
    session.execute("USE seminar")  # Keyspace
    rows = session.execute('SELECT id, json_document_topics, topics_json_str FROM results')  # Do select
    # only one result !
    for result_row_ in rows:
        result_row = result_row_  # only one, load it and forget
    return json.loads(result_row[2]), json.loads(result_row[1])


def prep_data_viz():
    all_topics, document_topics = preprocess_data(db=False)
    document_topics = pd.DataFrame(document_topics).transpose()
    all_topics = pd.DataFrame.from_dict(all_topics)
    n_topics = len(all_topics.columns)
    topics_flat = get_flat_topic_df(all_topics, n_topics)
    return topics_flat, document_topics


def convertTupleStr(tup):
    return '<br>'.join(map(str, tup))


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


def postprocess_data():
    flat_data, document_topics = prep_data_viz()
    iw = flat_data.index.get_level_values("Word").values.tolist()
    it = flat_data.index.get_level_values("TopicID").values.tolist()
    pca_ = PCA(n_components=len(set(it)))
    document_projections = pd.DataFrame(pca_.fit_transform(document_topics), index=document_topics.index.copy())

    topic_vis = document_topics.transpose()
    topic_vis = PCA(2).fit_transform(topic_vis)
    topic_vis = pd.DataFrame(topic_vis, columns=["pc1", "pc2"])

    topics_words = flat_data.unstack()
    topics_words.columns = [x[1:] for x in topics_words.columns]
    salient_words = topics_words.idxmax(axis=1)
    topic_vis["Salient Word"] = salient_words.values

    kelly_colors = [(255, 179, 0),
                    (128, 62, 117),
                    (255, 104, 0),
                    (166, 189, 215),
                    (193, 0, 32),
                    (206, 162, 98),
                    (129, 112, 102),
                    (0, 125, 52),
                    (246, 118, 142),
                    (0, 83, 138),
                    (255, 122, 92),
                    (83, 55, 122),
                    (255, 142, 0),
                    (179, 40, 81),
                    (244, 200, 0),
                    (127, 24, 13),
                    (147, 170, 0),
                    (89, 51, 21),
                    (241, 58, 19),
                    (35, 44, 22)
                    ]
    topics_weight = document_topics.transpose().sum(axis=1)
    topics_weight /= topics_weight.sum()
    topic_vis["overall weight"] = topics_weight
    return kelly_colors, document_projections, it, iw, flat_data, document_topics, topic_vis


if __name__ == "__main__":
    # pass
    preprocess_data(db=True)
