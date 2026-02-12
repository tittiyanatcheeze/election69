
import pandas as pd

def find_party_names():
    # Try reading with utf-8 first, then tis-620
    try:
        df = pd.read_csv('data/m_votes_master.csv', encoding='utf-8')
    except:
        try:
            df = pd.read_csv('data/m_votes_master.csv', encoding='tis-620')
        except Exception as e:
            print(f"Error reading file: {e}")
            return

    target_ids = ['P034', 'P063', 'P001']
    result = df[df['party_id'].isin(target_ids)][['party_id', 'party_name']].drop_duplicates()
    
    print("Found parties:")
    print(result)
    
    # Also print all unique parties to see what's available if none found
    if result.empty:
        print("\nAll unique party_ids and first party_name:")
        print(df[['party_id', 'party_name']].drop_duplicates().head(20))

find_party_names()
