import pandas as pd

csv_path = "data/df_merged_clean.csv"   # Path to your big CSV
parquet_path = "data/df_merged_clean.parquet"

print("Loading CSV... Please wait.")
df = pd.read_csv(csv_path, low_memory=False)

print("Saving as Parquet (this will compress the file)...")
df.to_parquet(parquet_path, index=False)

print("DONE! File converted successfully!")
print("Saved as:", parquet_path)
