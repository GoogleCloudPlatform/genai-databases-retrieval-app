import pandas as pd
import datetime

# Create a pandas dataframe
df = pd.read_csv(
    "/Users/duwenxin/Desktop/SenseAI/database-query-extension/data/flights_dataset.csv",
    dtype=str,
)

df = df.iloc[:, 4:]
# Change the 'departure_time' and 'arrival_time' year from 2015 to 2023
df["departure_time"] = pd.to_datetime(df["departure_time"]) + pd.to_timedelta(
    2, unit="D"
)
df["arrival_time"] = pd.to_datetime(df["arrival_time"]) + pd.to_timedelta(2, unit="D")


# Print the dataframe
print(df.head(5))

df.to_csv(
    "/Users/duwenxin/Desktop/SenseAI/database-query-extension/data/flights_dataset.csv",
    index=False,
)
