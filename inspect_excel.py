import pandas as pd
import sys

def inspect_excel(file_path):
    try:
        # Try reading with pandas (supports xls and xlsx)
        df = pd.read_excel(file_path, nrows=5)
        print("Columns found:", df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.to_string())
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_excel(sys.argv[1])
    else:
        print("Please provide a file path.")

