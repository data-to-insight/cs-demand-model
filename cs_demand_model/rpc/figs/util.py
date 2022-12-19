import pandas as pd


def column_index(config, columns):
    return pd.MultiIndex.from_tuples(
        [(config.AgeBrackets[c[0]], config.PlacementCategories[c[1]]) for c in columns]
    )
