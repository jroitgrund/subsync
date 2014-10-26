import yaml


def get_dataset():
    with open('data/files.yaml') as data_file:
        return yaml.load(data_file)
