import pandas as pd

def inspect_excel(file_path):
    try:
        # Try reading as standard excel
        df = pd.read_excel(file_path, nrows=5)
        print("Columns:", df.columns.tolist())
        print("First 5 rows:")
        print(df.head())
    except Exception as e:
        print(f"Error reading excel: {e}")

if __name__ == "__main__":
    inspect_excel("прайс.xls")





