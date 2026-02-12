import pandas as pd
import os

def read_csv_with_encoding(filepath):
    """
    Attempts to read a CSV file with multiple encodings.
    Tries utf-8, then tis-620, then cp874.
    """
    try:
        return pd.read_csv(filepath, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return pd.read_csv(filepath, encoding='tis-620')
        except UnicodeDecodeError:
            return pd.read_csv(filepath, encoding='cp874')

def get_turnout_data(data_dir='data'):
    """
    Loads and processes turnout data for CON, PL, and RFD for year 2569.
    Returns a dictionary of DataFrames keyed by ballot_code.
    """
    turnout_path = os.path.join(data_dir, 'm_turnout_master.csv')
    referendum_path = os.path.join(data_dir, 'm_referendum_master.csv')

    df_turnout = read_csv_with_encoding(turnout_path)
    df_referendum = read_csv_with_encoding(referendum_path)

    # Filter year 2569
    df_turnout = df_turnout[df_turnout['year'] == 2569].copy()
    # df_referendum might have year, check headers.txt: yes it has 'year'
    df_referendum = df_referendum[df_referendum['year'] == 2569].copy()
    
    # Ensure consistent columns for processing
    # required_cols = ['region', 'province', 'district_number', 'district_label', 'eligible_voters', 'voters_used']
    
    results = {}

    # --- Process CON ---
    df_con = df_turnout[df_turnout['ballot_code'] == 'CON'].copy()  # Assuming 'CONS' or 'CON'? prompt says CON, dashboard says CONS. Let's check dashboard again.
    # Dashboard line 37: turnout_cons = df_turnout_master[df_turnout_master['ballot_code'] == 'CONS'].copy()
    # Prompt says: "ballot_code in {CON, PL, RFD}". 
    # I should check what values are actually in the csv.
    # Assuming the prompt implies the OUTPUT ballot_code should be CON, PL, RFD.
    # But for input filtering, I need to match the data.
    # Let's check the unique values of ballot_code in m_turnout_master first.
    # I'll implement a mapping or check. For now, assuming standard codes, but will standardize to CON, PL, RFD in output.
    
    # Let's standardize the input dataframe first to be safe, or handle it downstrem.
    # Actually, better to inspect unique values first. 
    # For now, I'll write a small check at the beginning of main execution or assume the user prompt "CON, PL, RFD" maps to what's in DB or I rename.
    # Let's try to infer from dashboard code: 'CONS' is used. 'PARTY' is used for PL usually (dashboard line 96 matches 'PARTY').
    # So: CON -> CONS, PL -> PARTY. 
    # RFD -> RFD (likely).
    
    # Let's normalize to requested output codes: CON, PL, RFD.
    
    # 1. CON (from input 'CONS')
    df_con_in = df_turnout[df_turnout['ballot_code'] == 'CONS'].copy()
    if df_con_in.empty:
         df_con_in = df_turnout[df_turnout['ballot_code'] == 'CON'].copy()
    
    df_con_in['ballot_code'] = 'CON' # Force to requested output format
    results['CON'] = df_con_in

    # 2. PL (from input 'PARTY' or 'PL')
    df_pl_in = df_turnout[df_turnout['ballot_code'].isin(['PARTY', 'PL'])].copy()
    df_pl_in['ballot_code'] = 'PL'
    results['PL'] = df_pl_in

    # 3. RFD
    # logic: if turnout exists in m_turnout_master with ballot_code=RFD, use it.
    df_rfd_in_turnout = df_turnout[df_turnout['ballot_code'] == 'RFD'].copy()
    
    # If not, use m_referendum_master.
    # Strategy: Start with m_referendum_master (it likely has comprehensive RFD data). 
    # Then Update with m_turnout_master where available? Or preference?
    # Prompt: "if turnout exists in m_turnout_master ... use it. If not, use m_referendum_master"
    # This implies m_turnout_master is the primary source if record exists.
    
    # Let's check if m_referendum_master has the same district set.
    # merging...
    
    # Prepare base RFD from referendum master
    df_rfd_ref = df_referendum.copy()
    df_rfd_ref['ballot_code'] = 'RFD'
    
    # Align columns from referendum master to match turnout master structure
    # m_turnout_master cols: district_id, year, ballot_code, region, province, district_number, district_label, eligible_voters, voters_used, ...
    # m_referendum_master cols: district_id, ballot_code, yes_votes, no_votes, voters_used, year, region, province, district_number, district_label, eligible_voters, ...
    
    common_cols = ['district_id', 'year', 'ballot_code', 'region', 'province', 'district_number', 'district_label', 'eligible_voters', 'voters_used']
    
    df_rfd_ref = df_rfd_ref[common_cols]
    
    if not df_rfd_in_turnout.empty:
        # Use df_rfd_in_turnout, but fill missing districts from df_rfd_ref?
        # Or does "use it" mean "use this dataset instead of the other"?
        # Usually implies row-by-row preference.
        # Let's merge using district_id.
        
        # Taking all districts from both?
        # Let's assume we want comprehensive coverage. 
        # Base: all districts in turnout master OR referendum master.
        
        df_rfd_combined = pd.concat([df_rfd_in_turnout[common_cols], df_rfd_ref[common_cols]])
        # Drop duplicates, keeping m_turnout_master (which was first in concat? No, check logic)
        # We want m_turnout_master to take precedence.
        df_rfd_combined = df_rfd_combined.drop_duplicates(subset=['district_id'], keep='first')
        results['RFD'] = df_rfd_combined
    else:
        results['RFD'] = df_rfd_ref

    # Recalculate turnout_rate for all to be safe and ensure [0,1]
    for code, df in results.items():
        # Clean 0 eligible voters to avoid div by zero
        # Report them?
        zeros = df[df['eligible_voters'] == 0]
        if not zeros.empty:
            print(f"Warning: {len(zeros)} districts with 0 eligible voters for {code}")
            # print(zeros[['district_label', 'province']])
        
        df['turnout_rate'] = df.apply(
            lambda x: x['voters_used'] / x['eligible_voters'] if x['eligible_voters'] > 0 else 0, axis=1
        )
        
        # Sanity check
        mask_invalid = (df['turnout_rate'] < 0) | (df['turnout_rate'] > 1)
        if mask_invalid.any():
            print(f"Warning: Found invalid turnout rates (not in [0,1]) for {code}")
            # Clamp? or just warn?
            # Prompt says "Sanity checks: Turnout rates in [0,1]"
            # I will clamp for safety in output, but warning is logged.
            df.loc[df['turnout_rate'] > 1, 'turnout_rate'] = 1.0
            df.loc[df['turnout_rate'] < 0, 'turnout_rate'] = 0.0

        results[code] = df
        
    return results


def get_district_stats(df, top_n=10):
    """
    Returns top and bottom N district stats based on turnout_rate.
    """
    df_sorted = df.sort_values('turnout_rate', ascending=False)
    top_n_df = df_sorted.head(top_n).copy()
    top_n_df['rank_type'] = f'Top {top_n}'
    
    bottom_n_df = df_sorted.tail(top_n).sort_values('turnout_rate', ascending=True).copy()
    bottom_n_df['rank_type'] = f'Bottom {top_n}'
    
    return top_n_df, bottom_n_df

def get_province_stats(df, top_n=10):
    """
    Returns top and bottom N province stats based on turnout_rate.
    """
    prov_grp = df.groupby(['region', 'province']).agg(
        eligible_voters_sum=('eligible_voters', 'sum'),
        voters_used_sum=('voters_used', 'sum')
    ).reset_index()
    
    prov_grp['province_turnout_rate'] = prov_grp.apply(
        lambda x: x['voters_used_sum'] / x['eligible_voters_sum'] if x['eligible_voters_sum'] > 0 else 0, axis=1
    )
    
    prov_grp_sorted = prov_grp.sort_values('province_turnout_rate', ascending=False)
    
    top_n_df = prov_grp_sorted.head(top_n).copy()
    top_n_df['rank_type'] = f'Top {top_n}'
    
    bottom_n_df = prov_grp_sorted.tail(top_n).sort_values('province_turnout_rate', ascending=True).copy()
    bottom_n_df['rank_type'] = f'Bottom {top_n}'

    return top_n_df, bottom_n_df

def get_region_stats(df):
    """
    Returns region stats sorted by turnout_rate.
    """
    reg_grp = df.groupby(['region']).agg(
        eligible_voters_sum=('eligible_voters', 'sum'),
        voters_used_sum=('voters_used', 'sum')
    ).reset_index()
    
    reg_grp['region_turnout_rate'] = reg_grp.apply(
        lambda x: x['voters_used_sum'] / x['eligible_voters_sum'] if x['eligible_voters_sum'] > 0 else 0, axis=1
    )
    
    reg_grp_sorted = reg_grp.sort_values('region_turnout_rate', ascending=False)
    return reg_grp_sorted

def perform_analysis(output_dir='.'):
    results = get_turnout_data(data_dir='data') # Assuming running from root
    
    # A) District level Top/Bottom 10
    district_outputs = []
    
    for code, df in results.items():
        top10, bottom10 = get_district_stats(df, 10)
        
        # Add ballot_code
        top10['ballot_code'] = code
        bottom10['ballot_code'] = code
        
        district_outputs.append(top10)
        district_outputs.append(bottom10)

    df_district_final = pd.concat(district_outputs)
    final_cols_district = ['ballot_code', 'rank_type', 'region', 'province', 'district_number', 'district_label', 'eligible_voters', 'voters_used', 'turnout_rate']
    df_district_final = df_district_final[final_cols_district]
    
    df_district_final.to_csv(os.path.join(output_dir, 'q1_turnout_district_top_bottom.csv'), index=False, encoding='utf-8-sig')
    print("Created q1_turnout_district_top_bottom.csv")

    # B) Province level
    province_outputs = []
    
    for code, df in results.items():
        top10, bottom10 = get_province_stats(df, 10)
        
        top10['ballot_code'] = code
        bottom10['ballot_code'] = code
        
        province_outputs.append(top10)
        province_outputs.append(bottom10)
        
    df_province_final = pd.concat(province_outputs)
    final_cols_prov = ['ballot_code', 'rank_type', 'region', 'province', 'eligible_voters_sum', 'voters_used_sum', 'province_turnout_rate']
    df_province_final = df_province_final[final_cols_prov]
    
    df_province_final.to_csv(os.path.join(output_dir, 'q1_turnout_province_top_bottom.csv'), index=False, encoding='utf-8-sig')
    print("Created q1_turnout_province_top_bottom.csv")

    # C) Region ranking
    region_outputs = []
    
    for code, df in results.items():
        reg_stats = get_region_stats(df)
        reg_stats['ballot_code'] = code
        region_outputs.append(reg_stats)
        
    df_region_final = pd.concat(region_outputs)
    final_cols_reg = ['ballot_code', 'region', 'eligible_voters_sum', 'voters_used_sum', 'region_turnout_rate']
    df_region_final = df_region_final[final_cols_reg]
    
    df_region_final.to_csv(os.path.join(output_dir, 'q1_turnout_region_rank.csv'), index=False, encoding='utf-8-sig')
    print("Created q1_turnout_region_rank.csv")

if __name__ == "__main__":
    perform_analysis()

