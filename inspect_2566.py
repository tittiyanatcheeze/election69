
import pandas as pd

def get_headers():
    print("--- 2566 (Sheet: รายชื่อผู้สมัคร ส.ส. แบ่งเขต 66) ---")
    try:
        # Based on previous output, likely sheet names were 'ผลการเลือกตั้ง ส.ส. ปี 66', 'ภาพรวมรายเขต'.
        # Wait, the output for sheet names was NOT shown clearly in the previous step (it was background command).
        # Let me re-verify sheet names first. Ah, I see `['constituency_2566', ...]` in the output of the previous command.
        # But I need to be sure about the sheet name.
        # Let's list sheet names again and then read the first sheet or the one that looks like candidate data.
        xls = pd.ExcelFile('data/คะแนนเลือกตั้ง2566.xlsx')
        print(f"Sheets: {xls.sheet_names}")
        
        for sheet in xls.sheet_names:
             print(f"\n--- Sheet: {sheet} ---")
             df = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', sheet_name=sheet, nrows=2)
             print(df.columns.tolist())
    except Exception as e:
        print(f"Error: {e}")

get_headers()
