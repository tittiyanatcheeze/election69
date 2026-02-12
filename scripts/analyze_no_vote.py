
import pandas as pd
import os
import numpy as np

def load_2566_data():
    """
    Loads 2566 data and extracts No Vote counts and Turnout.
    Returns Dictionary of DataFrames for CON and PL.
    """
    try:
        # Load Constituency (CON)
        # Sheet: constituency_2566
        # Columns: 'จังหวัด', 'เขต', 'ผู้มาใช้สิทธิ', 'บัตรไม่เลือกผู้ใด', 'key'
        df_con = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', sheet_name='constituency_2566')
        df_con = df_con.rename(columns={
            'จังหวัด': 'province',
            'เขต': 'district_number',
            'ผู้มาใช้สิทธิ': 'voters_used',
            'บัตรไม่เลือกผู้ใด': 'no_vote'
        })
        df_con['key'] = df_con['province'] + "_" + df_con['district_number'].astype(str)
        df_con['year'] = 2566
        df_con['ballot_code'] = 'CON'
        
        # Load Party List (PL)
        # Sheet: partylist_by_constituency_2566
        # Columns: 'จังหวัด', 'เขต', 'ผู้มาใช้สิทธิ', 'ไม่เลือกผู้ใด'
        df_pl = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', sheet_name='partylist_by_constituency_2566')
        df_pl = df_pl.rename(columns={
            'จังหวัด': 'province',
            'เขต': 'district_number',
            'ผู้มาใช้สิทธิ': 'voters_used',
            'ไม่เลือกผู้ใด': 'no_vote'
        })
        df_pl['key'] = df_pl['province'] + "_" + df_pl['district_number'].astype(str)
        df_pl['year'] = 2566
        df_pl['ballot_code'] = 'PL'
        
        return {'CON': df_con, 'PL': df_pl}
        
    except Exception as e:
        print(f"Error loading 2566 data: {e}")
        return {}

def load_2569_data():
    """
    Loads 2569 data from Turnout Master.
    Returns Dictionary of DataFrames for CON and PL.
    """
    try:
        try:
             df = pd.read_csv('data/m_turnout_master.csv', encoding='utf-8')
        except:
             df = pd.read_csv('data/m_turnout_master.csv', encoding='tis-620')
        
        # Check ballot column
        ballot_col = 'ballot_code' if 'ballot_code' in df.columns else 'ballot_type'
        
        # Filter CON
        df_con = df[df[ballot_col].isin(['CON', 'CONS'])].copy()
        df_con['ballot_code'] = 'CON' # Normalize
        df_con['district_label'] = df_con['province'] + " เขต " + df_con['district_number'].astype(str)
        df_con['key'] = df_con['province'] + "_" + df_con['district_number'].astype(str)
        
        # Filter PL
        df_pl = df[df[ballot_col].isin(['PL', 'PARTY'])].copy()
        df_pl['ballot_code'] = 'PL' # Normalize
        df_pl['district_label'] = df_pl['province'] + " เขต " + df_pl['district_number'].astype(str)
        df_pl['key'] = df_pl['province'] + "_" + df_pl['district_number'].astype(str)

        return {'CON': df_con, 'PL': df_pl}
        
    except Exception as e:
        print(f"Error loading 2569 data: {e}")
        return {}

def analyze_no_vote():
    data_2566 = load_2566_data()
    data_2569 = load_2569_data()
    
    if not data_2566 or not data_2569: return

    # --- National Level ---
    national_rows = []
    
    for code in ['CON', 'PL']:
        # 2566
        d66 = data_2566.get(code)
        if d66 is not None:
             rate66 = d66['no_vote'].sum() / d66['voters_used'].sum()
             national_rows.append({'year': 2566, 'ballot_code': code, 'no_vote_total': d66['no_vote'].sum(), 'voters_total': d66['voters_used'].sum(), 'rate': rate66})
        
        # 2569
        d69 = data_2569.get(code)
        if d69 is not None:
             rate69 = d69['no_vote'].sum() / d69['voters_used'].sum()
             national_rows.append({'year': 2569, 'ballot_code': code, 'no_vote_total': d69['no_vote'].sum(), 'voters_total': d69['voters_used'].sum(), 'rate': rate69})

    df_national = pd.DataFrame(national_rows)
    df_national.to_csv('q8_no_vote_national_comparison.csv', index=False, encoding='utf-8-sig')

    # --- Region Level ---
    region_rows = []
    # Note: 2566 data keys do not have region. Need to map from 2569 (which has region).
    # Create Map
    if 'CON' in data_2569:
        region_map = data_2569['CON'].set_index('key')['region'].to_dict()
    else:
        region_map = {}

    for code in ['CON', 'PL']:
        # 2566
        d66 = data_2566.get(code)
        if d66 is not None:
            d66['region'] = d66['key'].map(region_map)
            # Groupby Region
            grp = d66.groupby('region')[['no_vote', 'voters_used']].sum().reset_index()
            grp['rate'] = grp['no_vote'] / grp['voters_used']
            grp['year'] = 2566
            grp['ballot_code'] = code
            region_rows.append(grp)

        # 2569
        d69 = data_2569.get(code)
        if d69 is not None:
            # Groupby Region
            grp = d69.groupby('region')[['no_vote', 'voters_used']].sum().reset_index()
            grp['rate'] = grp['no_vote'] / grp['voters_used']
            grp['year'] = 2569
            grp['ballot_code'] = code
            region_rows.append(grp)
    
    if region_rows:
        df_region = pd.concat(region_rows)
        # Pivot for comparison view? Or just list. List is fine for now, dashboard can pivot.
        df_region.to_csv('q8_no_vote_region_comparison.csv', index=False, encoding='utf-8-sig')

    # --- District Level Changes ---
    district_changes = []
    
    for code in ['CON', 'PL']:
        if code in data_2566 and code in data_2569:
            d66 = data_2566[code][['key', 'no_vote', 'voters_used']].copy()
            d66['rate_2566'] = d66['no_vote'] / d66['voters_used']
            
            d69 = data_2569[code][['key', 'region', 'province', 'district_label', 'no_vote', 'voters_used']].copy()
            d69['rate_2569'] = d69['no_vote'] / d69['voters_used']
            
            # Merge
            merged = pd.merge(d66[['key', 'rate_2566']], d69[['key', 'region', 'province', 'district_label', 'rate_2569']], on='key')
            merged['delta_rate'] = merged['rate_2569'] - merged['rate_2566']
            merged['ballot_code'] = code
            
            district_changes.append(merged)
            
    if district_changes:
        df_dist = pd.concat(district_changes)
        
        # Get Top 10 Increase/Decrease per ballot code (or combined list but labeled)
        # We save full list, dashboard filters top 10.
        df_dist.to_csv('q8_no_vote_district_changes.csv', index=False, encoding='utf-8-sig')
        
    print("Analysis Complete.")

if __name__ == "__main__":
    analyze_no_vote()
