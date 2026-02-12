
import pandas as pd
import sys

def get_headers(file_path_out):
    with open(file_path_out, 'w', encoding='utf-8') as f:
        f.write("--- m_votes_master.csv ---\n")
        try:
            df = pd.read_csv('data/m_votes_master.csv', nrows=2, encoding='tis-620')
            f.write(str(df.columns.tolist()) + "\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

        f.write("\n--- คะแนนเลือกตั้ง2566.xlsx ---\n")
        try:
            df = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', nrows=2)
            f.write(str(df.columns.tolist()) + "\n")
            f.write("Sample Row:\n")
            f.write(str(df.iloc[0].to_dict()) + "\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

get_headers('headers_territory.txt')
