
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

    # User IDs: P034, P063, P001. 
    # Logic: Search for specific codes. Also search for '34', '63', '1' if they are ints.
    target_ids = ['P034', 'P063', 'P001', '34', '63', '1']
    
    # Filter for candidate/CON to be sure
    df_con = df[df['ballot_code'] == 'CON']
    
    print(f"Searching in CON ballot rows (Total: {len(df_con)})")
    
    # Check party_id types
    print(f"Party ID type: {df_con['party_id'].dtype}")

    # Search for regular string matches or int matches
    if df_con['party_id'].dtype == object:
        result = df_con[df_con['party_id'].isin(target_ids)][['party_id', 'party_name']].drop_duplicates()
    else:
        # if numeric, convert targets to numeric
        numeric_targets = []
        for t in target_ids:
            if t.isdigit(): numeric_targets.append(int(t))
            # Handle P034 -> 34?
            if t.startswith('P') and t[1:].isdigit(): numeric_targets.append(int(t[1:]))
            
        result = df_con[df_con['party_id'].isin(numeric_targets)][['party_id', 'party_name']].drop_duplicates()
        
    print("Found parties:")
    print(result)

find_party_names()
