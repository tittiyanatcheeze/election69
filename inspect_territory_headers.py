
import pandas as pd

def get_headers():
    print("--- m_votes_master.csv ---")
    try:
        df = pd.read_csv('data/m_votes_master.csv', nrows=2, encoding='tis-620')
        print(df.columns.tolist())
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- คะแนนเลือกตั้ง2566.xlsx ---")
    try:
        df = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', nrows=2)
        print(df.columns.tolist())
        # Print a sample row to see data format
        print(df.iloc[0].to_dict())
    except Exception as e:
        print(f"Error: {e}")

get_headers()
