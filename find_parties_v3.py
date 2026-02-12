
import pandas as pd

def find_party_names():
    try:
        df = pd.read_csv('data/m_votes_master.csv', encoding='utf-8')
    except:
        try:
            df = pd.read_csv('data/m_votes_master.csv', encoding='tis-620')
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    # Check unique ballot codes
    print(f"Unique ballot codes: {df['ballot_code'].unique()}")

    # Use CONS if available
    if 'CONS' in df['ballot_code'].unique():
        df_con = df[df['ballot_code'] == 'CONS']
    elif 'CON' in df['ballot_code'].unique():
        df_con = df[df['ballot_code'] == 'CON']
    else:
        print("No CON/CONS data found.")
        return
    
    print(f"Searching in {len(df_con)} rows.")
    
    # Target IDs: P034, P063, P001. 
    target_ids = ['P034', 'P063', 'P001']
    numeric_targets = [34, 63, 1]

    # Check both string and numeric types
    if df_con['party_id'].dtype == object:
        result = df_con[df_con['party_id'].isin(target_ids)][['party_id', 'party_name']].drop_duplicates()
        if result.empty:
             print("No string matches found. Checking numeric strings...")
             result = df_con[df_con['party_id'].astype(str).isin(target_ids) | df_con['party_id'].isin(numeric_targets)][['party_id', 'party_name']].drop_duplicates()
    else:
        print("Party ID is numeric. Searching for numeric equivalents (34, 63, 1)...")
        result = df_con[df_con['party_id'].isin(numeric_targets)][['party_id', 'party_name']].drop_duplicates()
        
    print("Found parties:")
    print(result)

find_party_names()
