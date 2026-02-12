
import pandas as pd
import os

def load_2566_winners(filepath='data/คะแนนเลือกตั้ง2566.xlsx'):
    """
    Loads 2566 winners from Excel.
    Returns DataFrame with columns: province, province_number, party, scores
    """
    try:
        df = pd.read_excel(filepath, sheet_name='candidate_2566')
        # Find winner per district (Province + Province Number)
        # Group by province and province_number, find max scores
        idx = df.groupby(['province', 'province_number'])['scores'].idxmax()
        winners = df.loc[idx].copy()
        return winners
    except Exception as e:
        print(f"Error loading 2566 data: {e}")
        return pd.DataFrame()

def load_2569_winners(filepath='data/m_votes_master.csv'):
    """
    Loads 2569 winners from CSV (Ballot CON, Rank 1).
    Returns DataFrame with columns: district_id, province, district_number, party_id, party_name
    """
    try:
        try:
             df = pd.read_csv(filepath, encoding='utf-8')
        except:
             df = pd.read_csv(filepath, encoding='tis-620')
             
        # Filter for CON ballot and Rank 1
        # Check ballot_code column content (CONS vs CON)
        if 'CONS' in df['ballot_code'].unique():
            df = df[df['ballot_code'] == 'CONS']
        elif 'CON' in df['ballot_code'].unique():
            df = df[df['ballot_code'] == 'CON']
            
        winners = df[df['rank'] == 1].copy()
        return winners
    except Exception as e:
        print(f"Error loading 2569 data: {e}")
        return pd.DataFrame()

def compare_parties(winners_2566, winners_2569, config, output_dir='.'):
    """
    Compares 2566 and 2569 winners for a specific party configuration.
    config: {
        'prefix': 'q2_',
        '2566_name': 'ก้าวไกล',
        '2569_ids': ['P000'],
        '2569_names': ['ประชาชน']
    }
    """
    prefix = config['prefix']
    target_2566_name = config['2566_name']
    target_2569_ids = [str(x) for x in config['2569_ids']] # Ensure strings for comparison if needed
    target_2569_names = config['2569_names']

    print(f"--- Processing {target_2566_name} / {target_2569_names} ---")

    # Filter 2566 winners for target party
    # 2566 columns: province, province_number, name, party, scores
    w2566_target = winners_2566[winners_2566['party'] == target_2566_name].copy()
    
    # Filter 2569 winners for target party (won in 2569)
    # 2569 columns: district_id, year, ballot_code, party_id, party_name, region, province, district_number, ...
    
    # Normalize party_id to string for checking
    winners_2569['party_id_str'] = winners_2569['party_id'].astype(str)
    # Handle .0 float strings if any
    winners_2569['party_id_str'] = winners_2569['party_id_str'].str.replace(r'\.0$', '', regex=True)

    w2569_target = winners_2569[
        (winners_2569['party_id_str'].isin(target_2569_ids)) | 
        (winners_2569['party_name'].isin(target_2569_names))
    ].copy()

    # Pre-calculate verify count for 2566 (MFP specifically requested 112)
    if 'ก้าวไกล' in target_2566_name:
        count_2566 = len(w2566_target)
        print(f"2566 {target_2566_name} seat count: {count_2566}")
        if count_2566 != 112:
            print(f"WARNING: Expected 112 seats for {target_2566_name}, found {count_2566}")

    # Merge to compare
    # Key: province, district_number (2569) vs province_number (2566)
    # Note: 2569 'district_number' vs 2566 'province_number'. Assuming they map 1:1.
    
    # We need to match ALL districts to see Held/Lost/Gained.
    # Strategy: 
    # 1. Identify "Won 2566" set (Province, DistNum)
    # 2. Identify "Won 2569" set (Province, DistNum)
    # 3. Intersect = Held
    # 4. Won 2569 - Won 2566 = Gained (New)
    # 5. Won 2566 - Won 2569 = Lost
    
    # Prepare keys
    w2566_target['key'] = w2566_target['province'] + "_" + w2566_target['province_number'].astype(str)
    w2569_target['key'] = w2569_target['province'] + "_" + w2569_target['district_number'].astype(str)
    
    set_2566 = set(w2566_target['key'])
    set_2569 = set(w2569_target['key'])
    
    held_keys = set_2566.intersection(set_2569)
    lost_keys = set_2566.difference(set_2569)
    gained_keys = set_2569.difference(set_2566) # New
    
    # --- Generate Detail Tables ---
    
    # HELD
    # We can pull details from w2569_target (it has all current info)
    df_held = w2569_target[w2569_target['key'].isin(held_keys)].copy()
    # Add 2566 info if useful? Prompt says "Held: district won by 2566 MFP and won by P000 in 2569".
    # Just list them.
    df_held.to_csv(os.path.join(output_dir, f'{prefix}held.csv'), index=False, encoding='utf-8-sig')

    # LOST
    # "Lost: won by 2566 MFP but not won by P000 in 2569. Include winner party_id and party_name (of 2569)."
    # We need to find who won these districts in 2569.
    # Get all 2569 winners for these keys
    winners_2569['key'] = winners_2569['province'] + "_" + winners_2569['district_number'].astype(str)
    df_lost = winners_2569[winners_2569['key'].isin(lost_keys)].copy()
    # Add info about who won in 2566 (Target Party)
    df_lost['2566_winner'] = target_2566_name
    df_lost.to_csv(os.path.join(output_dir, f'{prefix}lost.csv'), index=False, encoding='utf-8-sig')
    
    # GAINED (NEW)
    # "New: won by P000 in 2569 but not won by 2566 MFP."
    # List them (from w2569_target).
    # Optional: "include 2566 winner party".
    # We need to look up who won in 2566 for these keys.
    # Provide logic to look up 2566 winner:
    #   Load all 2566 winners, create map Key -> Party
    df_gained = w2569_target[w2569_target['key'].isin(gained_keys)].copy()
    
    # Look up 2566 winner
    all_2566 = winners_2566.copy()
    all_2566['key'] = all_2566['province'] + "_" + all_2566['province_number'].astype(str)
    map_2566 = all_2566.set_index('key')['party'].to_dict()
    
    df_gained['2566_winner'] = df_gained['key'].map(map_2566).fillna('Unknown')
    if prefix == 'q2_':
         filename = 'q2_new_districts.csv' # Special name for Q2
    else:
         filename = f'{prefix}gained.csv'
         
    df_gained.to_csv(os.path.join(output_dir, filename), index=False, encoding='utf-8-sig')
    
    # SUMMARY COUNTS
    summary = pd.DataFrame([{
        'held': len(held_keys),
        'lost': len(lost_keys),
        'gained': len(gained_keys)
    }])
    summary.to_csv(os.path.join(output_dir, f'{prefix}summary_counts.csv'), index=False, encoding='utf-8-sig')

    # --- Province/Region Stats (Explicitly for Q2, but useful for others) ---
    # "seats_2566_mfp = count of districts with MFP rank=1 in 2566"
    # "seats_2569_p000 = count of districts with P000 rank=1 in 2569"
    # Use w2566_target and w2569_target
    
    # Group 2566 by Province
    s2566_prov = w2566_target.groupby('province').size().reset_index(name='seats_2566')
    # Group 2566 by Region? 2566 file doesn't have region. Need to map from 2569 or other source.
    # Map Province -> Region using winners_2569 (as it has region)
    prov_region_map = winners_2569[['province', 'region']].drop_duplicates().set_index('province')['region'].to_dict()
    w2566_target['region'] = w2566_target['province'].map(prov_region_map)
    
    # Group 2569 by Province
    s2569_prov = w2569_target.groupby('province').size().reset_index(name='seats_2569')
    
    # Merge
    stats_prov = pd.merge(s2566_prov, s2569_prov, on='province', how='outer').fillna(0)
    stats_prov['region'] = stats_prov['province'].map(prov_region_map)
    stats_prov['delta'] = stats_prov['seats_2569'] - stats_prov['seats_2566']
    stats_prov['status'] = stats_prov['delta'].apply(lambda x: 'Increased' if x > 0 else ('Decreased' if x < 0 else 'Stable'))
    
    # Filter: "For provinces where 2566 MFP won at least one district" (For Q2)
    # Applying general logic: keep if seats_2566 > 0 OR seats_2569 > 0
    # Ideally we show all relevant provinces.
    
    # For Q2 (MFP), prompt said: "For provinces where 2566 MFP won at least one district"
    # For others, user just asked to "add province delta". I'll apply the same logic or just show all non-zero.
    # Let's show all provinces where EITHER 2566 or 2569 had a seat.
    
    stats_prov_filtered = stats_prov[(stats_prov['seats_2566'] > 0) | (stats_prov['seats_2569'] > 0)].copy()
    
    # Save with prefix
    stats_prov_filtered.to_csv(os.path.join(output_dir, f'{prefix}province_seat_changes.csv'), index=False, encoding='utf-8-sig')

    # Region Stats (also save for all)
    stats_region = stats_prov.groupby('region')[['seats_2566', 'seats_2569']].sum().reset_index()
    stats_region['delta'] = stats_region['seats_2569'] - stats_region['seats_2566']
    stats_region.to_csv(os.path.join(output_dir, f'{prefix}region_seat_changes.csv'), index=False, encoding='utf-8-sig')

def perform_analysis():
    w2566 = load_2566_winners()
    w2569 = load_2569_winners()
    
    if w2566.empty or w2569.empty:
        print("Failed to load data. Aborting.")
        return

    # Helper for extracting stats for dashboard
    # (Not strictly needed if we just output CSVs, but good structure)

    configs = [
        {
            'prefix': 'q2_',
            '2566_name': 'ก้าวไกล',
            '2569_ids': ['P000'],
            '2569_names': ['ประชาชน'] # Name might be different in CSV?
        },
        {
            'prefix': 'q3_p034_',
            '2566_name': 'เพื่อไทย',
            '2569_ids': ['P034', '34'],
            '2569_names': ['เพื่อไทย']
        },
        {
            'prefix': 'q4_p063_',
            '2566_name': 'ภูมิใจไทย',
            '2569_ids': ['P063', '63'],
            '2569_names': ['ภูมิใจไทย']
        },
        {
            'prefix': 'q5_p001_',
            '2566_name': 'ประชาธิปัตย์',
            '2569_ids': ['P001', '1'],
            '2569_names': ['ประชาธิปัตย์']
        }
    ]

    for conf in configs:
        compare_parties(w2566, w2569, conf)

if __name__ == "__main__":
    perform_analysis()
