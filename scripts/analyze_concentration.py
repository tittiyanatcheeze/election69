
import pandas as pd
import os
import numpy as np

def load_2566_data():
    """
    Loads 2566 data and prepares a standard DataFrame.
    Returns DF with: year, key (Province_Dist), province, district_number, party, votes, voters_used
    """
    try:
        # Load Candidates
        df_cand = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', sheet_name='candidate_2566')
        # Load Turnout
        df_cons = pd.read_excel('data/คะแนนเลือกตั้ง2566.xlsx', sheet_name='constituency_2566')
        
        # Prepare Turnout Map: Key -> Voters Used
        # Sheet columns: 'จังหวัด', 'เขต', 'ผู้มาใช้สิทธิ'
        df_cons['key'] = df_cons['จังหวัด'] + "_" + df_cons['เขต'].astype(str)
        turnout_map = df_cons.set_index('key')['ผู้มาใช้สิทธิ'].to_dict()
        
        # Prepare Candidate Data
        df_cand['key'] = df_cand['province'] + "_" + df_cand['province_number'].astype(str)
        df_cand['voters_used'] = df_cand['key'].map(turnout_map)
        
        # Rename/Select
        df = df_cand.rename(columns={
            'province_number': 'district_number',
            'scores': 'votes'
        })
        df['year'] = 2566
        
        return df[['year', 'key', 'province', 'district_number', 'party', 'votes', 'voters_used']]
    except Exception as e:
        print(f"Error loading 2566 data: {e}")
        return pd.DataFrame()

def load_2569_data():
    """
    Loads 2569 data and prepares a standard DataFrame.
    Returns DF with: year, key (Province_Dist), province, district_number, party, votes, voters_used
    """
    try:
        # Load Votes
        try:
             df_votes = pd.read_csv('data/m_votes_master.csv', encoding='utf-8')
        except:
             df_votes = pd.read_csv('data/m_votes_master.csv', encoding='tis-620')
             
        # Filter CON
        if 'CONS' in df_votes['ballot_code'].unique():
            df_votes = df_votes[df_votes['ballot_code'] == 'CONS']
        elif 'CON' in df_votes['ballot_code'].unique():
            df_votes = df_votes[df_votes['ballot_code'] == 'CON']
            
        # Load Turnout
        try:
             df_turnout = pd.read_csv('data/m_turnout_master.csv', encoding='utf-8')
        except:
             df_turnout = pd.read_csv('data/m_turnout_master.csv', encoding='tis-620')
             
        # Filter Turnout CON
        # Check if ballot_type or ballot_code
        col_name = 'ballot_code' if 'ballot_code' in df_turnout.columns else 'ballot_type'
        
        if 'CONS' in df_turnout[col_name].unique():
            df_turnout = df_turnout[df_turnout[col_name] == 'CONS']
        elif 'CON' in df_turnout[col_name].unique():
            df_turnout = df_turnout[df_turnout[col_name] == 'CON']
            
        # Prepare Turnout Map: District ID? Or Prov_Dist?
        # m_votes has district_id. m_turnout has district_id.
        turnout_map = df_turnout.set_index('district_id')['voters_used'].to_dict()
        
        df_votes['voters_used'] = df_votes['district_id'].map(turnout_map)
        
        # Create Key
        df_votes['key'] = df_votes['province'] + "_" + df_votes['district_number'].astype(str)
        
        # Rename
        df_votes = df_votes.rename(columns={'party_name': 'party'})
        # Ensure votes is numeric (it might be in 'score' or 'votes' depending on file, strictly 'votes' here per prompt? )
        # Inspect columns says: ... party, party_name, scores/votes?
        # Let's check headers from earlier logs. 
        # previous `inspect_headers.py` on m_turnout showed... wait m_votes.
        # m_votes_master usually has `calories`... no, `votes` or `score`.
        # I'll check if 'votes' exists, if not use 'score' or 'points'.
        # Actually I can check the `rank` column which implies a score exists.
        # Let's assume 'votes' or 'score'.
        vote_col = 'votes' if 'votes' in df_votes.columns else 'score'
        if vote_col not in df_votes.columns:
             # Find numeric column that looks like votes
             pass
        
        df_votes = df_votes.rename(columns={vote_col: 'votes'})
        
        df_votes['year'] = 2569
        
        return df_votes[['year', 'key', 'province', 'district_number', 'party', 'votes', 'voters_used']]
        
    except Exception as e:
        print(f"Error loading 2569 data: {e}")
        return pd.DataFrame()

def calculate_district_metrics(df_year):
    """
    Calculates share_rk1, share_rk2, etc. and ENC for each district in the df.
    """
    results = []
    
    grouped = df_year.groupby('key')
    
    for key, group in grouped:
        # Sort by votes descending
        group = group.sort_values('votes', ascending=False)
        
        # Basic info
        province = group['province'].iloc[0]
        dist_num = group['district_number'].iloc[0]
        year = group['year'].iloc[0]
        voters_used = group['voters_used'].iloc[0] if pd.notna(group['voters_used'].iloc[0]) else group['votes'].sum() # Fallback
        
        # Ranks
        candidates = group.to_dict('records') # List of dicts
        
        if len(candidates) == 0: continue
        
        c1 = candidates[0]
        c2 = candidates[1] if len(candidates) > 1 else None
        c3 = candidates[2] if len(candidates) > 2 else None
        
        votes_rk1 = c1['votes']
        votes_rk2 = c2['votes'] if c2 else 0
        votes_rk3 = c3['votes'] if c3 else 0
        
        # Shares (denominator = voters_used)
        share_rk1 = votes_rk1 / voters_used if voters_used > 0 else 0
        share_rk2 = votes_rk2 / voters_used if voters_used > 0 else 0
        share_rk3 = votes_rk3 / voters_used if voters_used > 0 else 0
        
        # Share Others
        # Sum of votes of rank 4+ (index 3+)
        votes_others = sum(c['votes'] for c in candidates[3:])
        share_others = votes_others / voters_used if voters_used > 0 else 0
        
        # ENC Calculation (denominator = sum of candidate votes)
        total_candidate_votes = sum(c['votes'] for c in candidates)
        if total_candidate_votes > 0:
            sum_sq_prop = sum((c['votes'] / total_candidate_votes)**2 for c in candidates)
            enc = 1 / sum_sq_prop if sum_sq_prop > 0 else 0
            
            # Additional ENC outputs
            share_rk1_cand = votes_rk1 / total_candidate_votes
            margin12_cand = (votes_rk1 - votes_rk2) / total_candidate_votes
        else:
            enc = 0
            share_rk1_cand = 0
            margin12_cand = 0
            
        results.append({
            'year': year,
            'key': key,
            'province': province,
            'district_number': dist_num,
            'winner_party': c1['party'],
            'votes_rk1': votes_rk1,
            'share_rk1': share_rk1,
            'share_rk2': share_rk2,
            'share_rk3': share_rk3,
            'share_others': share_others,
            'enc': enc,
            'n_candidates': len(candidates),
            'share_rk1_cand': share_rk1_cand,
            'margin12_cand': margin12_cand
        })
        
    return pd.DataFrame(results)

def main():
    print("Loading data...")
    df2566 = load_2566_data()
    df2569 = load_2569_data()
    
    print("Calculating metrics 2566...")
    metrics_2566 = calculate_district_metrics(df2566)
    print("Calculating metrics 2569...")
    metrics_2569 = calculate_district_metrics(df2569)
    
    all_metrics = pd.concat([metrics_2566, metrics_2569])
    
    # Save Base Tables
    metrics_2566.to_csv('q6_con_topk_2566.csv', index=False, encoding='utf-8-sig')
    metrics_2569.to_csv('q6_con_topk_2569.csv', index=False, encoding='utf-8-sig')
    
    print("Applying criteria...")
    flags = []
    
    # Process by district (some checks need cross-year)
    # We iterate through the combined metrics or merge them
    
    # 6.1 Dominant Winner: share_rk1 > share_others
    crit_6_1 = all_metrics[all_metrics['share_rk1'] > all_metrics['share_others']].copy()
    crit_6_1.to_csv('q6_criteria_6_1.csv', index=False, encoding='utf-8-sig')
    
    # 6.2 Top 2 Concentration
    thresholds = [0.70, 0.75, 0.80]
    result_6_2 = []
    for t in thresholds:
        mask = (all_metrics['share_rk1'] + all_metrics['share_rk2']) >= t
        df_t = all_metrics[mask].copy()
        df_t['threshold'] = t
        result_6_2.append(df_t)
        
    if result_6_2:
        crit_6_2 = pd.concat(result_6_2)
        crit_6_2.to_csv('q6_criteria_6_2_lists.csv', index=False, encoding='utf-8-sig')
    
    # 6.3 Cross-year pattern
    # Merge 2566 and 2569 on key
    m66 = metrics_2566[['key', 'share_rk2', 'share_rk3']].rename(columns={'share_rk2': 's2_66', 'share_rk3': 's3_66'})
    m69 = metrics_2569[['key', 'province', 'district_number', 'share_rk1', 'winner_party']].rename(columns={'share_rk1': 's1_69'})
    
    merged_63 = pd.merge(m66, m69, on='key')
    merged_63['s_2566'] = merged_63['s2_66'] + merged_63['s3_66']
    merged_63['s_2569'] = merged_63['s1_69']
    merged_63['diff'] = merged_63['s_2566'] - merged_63['s_2569']
    
    # Flag if -0.05 < diff < 0.05 (abs(diff) < 0.05)
    crit_6_3 = merged_63[merged_63['diff'].abs() < 0.05].copy()
    crit_6_3.to_csv('q6_criteria_6_3.csv', index=False, encoding='utf-8-sig')
    
    # 6.4 ENC
    # Save ENC quantiles
    enc_stats = all_metrics.groupby('year')['enc'].describe(percentiles=[0.05, 0.1, 0.25, 0.5])
    enc_stats.to_csv('q6_enc_stats.csv', encoding='utf-8-sig')
    all_metrics.to_csv('q6_enc_by_district_year.csv', index=False, encoding='utf-8-sig')
    
    # Flag low ENC
    # A) Absolute <= 1.5, <= 2.0
    # B) Relative <= p10 of that year
    low_enc_rows = []
    
    p10_map = enc_stats['10%'].to_dict() # Year -> p10 value
    
    for idx, row in all_metrics.iterrows():
        reasons = []
        if row['enc'] <= 1.5: reasons.append('ENC<=1.5')
        if row['enc'] <= 2.0: reasons.append('ENC<=2.0')
        if row['enc'] <= p10_map.get(row['year'], 0): reasons.append('ENC<=p10')
        
        if reasons:
            r = row.to_dict()
            r['reasons'] = ", ".join(reasons)
            low_enc_rows.append(r)
            
    crit_6_4 = pd.DataFrame(low_enc_rows)
    if not crit_6_4.empty:
        crit_6_4.to_csv('q6_enc_low_lists.csv', index=False, encoding='utf-8-sig')

    # Combined Flags
    # For each district/year, list triggered criteria
    # We can perform a master merge or just iterate
    # Let's use the all_metrics as base
    
    combined = all_metrics.copy()
    combined['flags'] = ''
    
    # 6.1
    set_6_1 = set(zip(crit_6_1['key'], crit_6_1['year']))
    # 6.2 (Any threshold? "List districts that satisfy any criteria")
    set_6_2 = set(zip(crit_6_2['key'], crit_6_2['year'])) if result_6_2 else set()
    # 6.3 (Only 2569 rows effectively, or tag both? "For the same district_id... Report counts and list districts")
    # Let's tag the 2569 row as the anomaly carrier
    set_6_3 = set(zip(crit_6_3['key'], [2569]*len(crit_6_3)))
    # 6.4
    set_6_4 = set(zip(crit_6_4['key'], crit_6_4['year'])) if not crit_6_4.empty else set()
    
    def get_flags(row):
        f = []
        k = (row['key'], row['year'])
        if k in set_6_1: f.append('Dominant')
        if k in set_6_2: f.append('Concentrated')
        if k in set_6_3: f.append('Cross-Year')
        if k in set_6_4: f.append('Low ENC')
        return ", ".join(f)

    combined['flags'] = combined.apply(get_flags, axis=1)
    final = combined[combined['flags'] != ''].copy()
    final.to_csv('q6_combined_flags.csv', index=False, encoding='utf-8-sig')
    print(f"Analysis complete. Found {len(final)} flagged districts.")

if __name__ == "__main__":
    main()
