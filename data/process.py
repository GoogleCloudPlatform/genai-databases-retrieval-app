import pandas as pd
import random
import numpy as np


df = pd.read_csv(
    "/Users/duwenxin/Desktop/SenseAI/database-query-extension/data/flights_dataset.csv",
    dtype=str,
)

df = df[(df["departure_airport"] == "SFO") | (df["arrival_airport"] == "SFO")]
# Get the number of rows in the DataFrame
n_rows = df.shape[0]


df.to_csv(
    "/Users/duwenxin/Desktop/SenseAI/database-query-extension/data/flights_dataset.csv",
    index=False,
)
print(n_rows)
