
import pandas as pd
import sys

def get_headers(file_path, f_out):
    f_out.write(f"--- {file_path} ---\n")
    try:
        df = pd.read_csv(file_path, nrows=2, encoding='utf-8')
        f_out.write(str(df.columns.tolist()) + "\n")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, nrows=2, encoding='tis-620')
            f_out.write(f"Read with tis-620\n")
            f_out.write(str(df.columns.tolist()) + "\n")
        except Exception as e:
            f_out.write(f"Failed to read with tis-620: {e}\n")
    except Exception as e:
        f_out.write(f"Failed to read: {e}\n")

with open('headers.txt', 'w', encoding='utf-8') as f:
    get_headers('data/m_turnout_master.csv', f)
    get_headers('data/m_referendum_master.csv', f)
