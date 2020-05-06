import json
import pandas as pd

def get_json_data():
    with open("data_example/document_topics.json", "rt") as f:
        document_topics_dict = json.load(f)

    with open("data_example/topic_model.json", "rt") as f:
        all_topics = json.load(f)

    return all_topics, document_topics_dict

def preprocess_data(db=True):
    if db:
        pass
    else:
        all_topics, document_topics_dict = get_json_data()

    for x in all_topics.keys():
        accu = 0
        for j in all_topics[x].keys():
            accu+= all_topics[x][j]
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

    #topics_dataframe = pd.DataFrame.from_dict(all_topics_)

    return all_topics_, document_topics


def get_db_data():
    pass

if __name__ == "__main__":
    print("test me")
    preprocess_data(db=False)
