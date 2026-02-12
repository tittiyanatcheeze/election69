
import pandas as pd
import sys

def get_headers(file_path_out):
    with open(file_path_out, 'w', encoding='utf-8') as f:
        try:
            xls = pd.ExcelFile('data/คะแนนเลือกตั้ง2566.xlsx')
            f.write(f"Sheets: {xls.sheet_names}\n")
            
            for sheet in xls.sheet_names:
                 f.write(f"\n--- Sheet: {sheet} ---\n")
                 df = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', sheet_name=sheet, nrows=2)
                 f.write(str(df.columns.tolist()) + "\n")
                 f.write("Sample Row:\n")
                 f.write(str(df.iloc[0].to_dict()) + "\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

get_headers('headers_2566.txt')
