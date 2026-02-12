
import pandas as pd
import numpy as np

def load_data():
    """
    Loads 2569 CON data.
    """
    try:
        try:
             df = pd.read_csv('data/m_votes_master.csv', encoding='utf-8')
        except:
             df = pd.read_csv('data/m_votes_master.csv', encoding='tis-620')
        
        # Filter CON
        ballot_col = 'ballot_code' if 'ballot_code' in df.columns else 'ballot_type'
        if 'CONS' in df[ballot_col].unique():
            df = df[df[ballot_col] == 'CONS']
        elif 'CON' in df[ballot_col].unique():
            df = df[df[ballot_col] == 'CON']
            
        # Get voters_used map
        try:
             df_turnout = pd.read_csv('data/m_turnout_master.csv', encoding='utf-8')
        except:
             df_turnout = pd.read_csv('data/m_turnout_master.csv', encoding='tis-620')
        
        # Filter Turnout CON
        t_col = 'ballot_code' if 'ballot_code' in df_turnout.columns else 'ballot_type'
        if 'CONS' in df_turnout[t_col].unique():
            df_turnout = df_turnout[df_turnout[t_col] == 'CONS']
        elif 'CON' in df_turnout[t_col].unique():
            df_turnout = df_turnout[df_turnout[t_col] == 'CON']
            
        turnout_map = df_turnout.set_index('district_id')['voters_used'].to_dict()
        df['voters_used'] = df['district_id'].map(turnout_map)
        
        # Ensure 'votes' column
        vote_col = 'votes' if 'votes' in df.columns else 'score'
        if vote_col != 'votes':
            df = df.rename(columns={vote_col: 'votes'})
            
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def analyze_typology():
    df = load_data()
    if df.empty: return

    # Target Parties
    # P000/000 = People's Party
    # P034 = Move Forward (2566) -> used as proxy or if present? 
    # Prompt says P034. In 2569 data, likely P000 is the successor.
    # But let's follow prompt strictly: P000, P034, P001.
    # Note: P034 might not exist in 2569 if dissolved? 
    # If not exist, shares will be 0.
    
    target_ids = ['P000', 'P034', 'P001']
    
    results = []
    
    grouped = df.groupby(['province', 'district_number'])
    
    for (prov, dist), group in grouped:
        group = group.sort_values('votes', ascending=False)
        candidates = group.to_dict('records')
        
        if not candidates: continue
        
        voters_used = candidates[0]['voters_used']
        if pd.isna(voters_used) or voters_used == 0:
            voters_used = sum(c['votes'] for c in candidates) # Fallback
            
        # Ranks
        rk1 = candidates[0]
        rk2 = candidates[1] if len(candidates) > 1 else None
        rk3 = candidates[2] if len(candidates) > 2 else None
        
        share_rk1 = rk1['votes'] / voters_used
        share_rk2 = (rk2['votes'] / voters_used) if rk2 else 0
        share_rk3 = (rk3['votes'] / voters_used) if rk3 else 0
        
        # Party Shares
        shares = {}
        votes = {}
        for pid in target_ids:
            # Match by ID (approx)
            # P000 might be '000'
            party_votes = 0
            for c in candidates:
                c_pid = str(c['party_id']).replace('.0', '')
                if c_pid == pid or c_pid == pid.replace('P', ''):
                    party_votes += c['votes']
            
            votes[pid] = party_votes
            shares[pid] = party_votes / voters_used
            
        # 9.1 P000 + P034 Analysis
        # Category A: P000 Winner & Share > (Rk2+Rk3)
        # Category B: P034 Winner & Share > (Rk2+Rk3)
        # Category C: Combined (Non-Winner) > Rk1
        # Category D: Others
        
        cat_91 = 'D' # Default
        
        # Check Winner Dominance
        winner_pid = str(rk1['party_id']).replace('.0', '')
        # Normalize to match target_ids
        if winner_pid == '000': winner_pid = 'P000'
        if winner_pid == '034': winner_pid = 'P034'
        
        combined_nw_91 = 0
        if winner_pid not in ['P000']: combined_nw_91 += shares['P000']
        if winner_pid not in ['P034']: combined_nw_91 += shares['P034']
        
        if winner_pid == 'P000' and share_rk1 > (share_rk2 + share_rk3):
            cat_91 = 'A'
        elif winner_pid == 'P034' and share_rk1 > (share_rk2 + share_rk3):
            cat_91 = 'B'
        elif combined_nw_91 > share_rk1:
            cat_91 = 'C'
        else:
            cat_91 = 'D'
            
        # 9.2 P000 + P034 + P001 Analysis
        # A: P000 Winner & Dominant
        # B: P034 Winner & Dominant
        # C: P001 Winner & Dominant
        # D: Combined (Non-Winner) > Rk1
        # E: Others
        
        cat_92 = 'E'
        
        combined_nw_92 = 0
        if winner_pid not in ['P000']: combined_nw_92 += shares['P000']
        if winner_pid not in ['P034']: combined_nw_92 += shares['P034']
        if winner_pid not in ['P001']: combined_nw_92 += shares['P001']
        
        if winner_pid == 'P000' and share_rk1 > (share_rk2 + share_rk3):
            cat_92 = 'A'
        elif winner_pid == 'P034' and share_rk1 > (share_rk2 + share_rk3):
            cat_92 = 'B'
        elif winner_pid == 'P001' and share_rk1 > (share_rk2 + share_rk3):
            cat_92 = 'C'
        elif combined_nw_92 > share_rk1:
            cat_92 = 'D'
        else:
            cat_92 = 'E'

        # 9.3 Rk2 + Rk3 > Rk1
        flag_93 = (share_rk2 + share_rk3) > share_rk1
        
        results.append({
            'province': prov,
            'district_number': dist,
            'district_label': f"{prov} เขต {dist}",
            'winner_party': rk1['party_name'],
            'cat_91': cat_91,
            'cat_92': cat_92,
            'flag_93': flag_93,
            'share_rk1': share_rk1,
            'share_rk2': share_rk2,
            'share_rk3': share_rk3
        })
        
    df_res = pd.DataFrame(results)
    
    # Save Outputs
    # 9.1
    df_res[['province', 'district_label', 'cat_91']].to_csv('q9_typology_91.csv', index=False, encoding='utf-8-sig')
    # 9.2
    df_res[['province', 'district_label', 'cat_92']].to_csv('q9_typology_92.csv', index=False, encoding='utf-8-sig')
    # 9.3
    df_93 = df_res[df_res['flag_93']].copy()
    df_93.to_csv('q9_rank23_gt_rank1.csv', index=False, encoding='utf-8-sig')
    
    print("Analysis Complete.")

if __name__ == "__main__":
    analyze_typology()
