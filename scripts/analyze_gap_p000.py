
import pandas as pd
import os
import numpy as np

def load_data():
    """
    Loads 2569 data.
    """
    try:
        try:
             df_votes = pd.read_csv('data/m_votes_master.csv', encoding='utf-8')
        except:
             df_votes = pd.read_csv('data/m_votes_master.csv', encoding='tis-620')
             
        # Filter CON
        if 'CONS' in df_votes['ballot_code'].unique():
            df_votes = df_votes[df_votes['ballot_code'] == 'CONS']
        elif 'CON' in df_votes['ballot_code'].unique():
            df_votes = df_votes[df_votes['ballot_code'] == 'CON']
            
        return df_votes
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def bucket_value(val):
    if val <= 500: return '0-500'
    if val <= 2500: return '501-2500'
    if val <= 5000: return '2501-5000'
    if val <= 10000: return '5001-10000'
    return '10000+'

def main():
    df = load_data()
    if df.empty: return
    
    # Target: P000 / ประชาชน
    target_ids = ['P000', '000'] # Just in case
    target_names = ['ประชาชน']
    
    # Identify target rows
    # Normalize party_id
    df['party_id_str'] = df['party_id'].astype(str).str.replace(r'\.0$', '', regex=True)
    mask_target = (df['party_id_str'].isin(target_ids)) | (df['party_name'].isin(target_names))
    
    # Prepare results lists
    gap_list = [] # Lost
    margin_list = [] # Won
    
    # Group by District
    grouped = df.groupby(['province', 'district_number'])
    
    for (prov, dist), group in grouped:
        # Sort by rank/votes
        group = group.sort_values('rank')
        candidates = group.to_dict('records')
        
        if not candidates: continue
        
        # Find Target
        target_cand = None
        for c in candidates:
            pid = str(c['party_id']).replace('.0', '')
            if pid in target_ids or c['party_name'] in target_names:
                target_cand = c
                break
        
        if not target_cand: continue
        
        # Check if Won or Lost
        rank1 = candidates[0]
        
        # Case 1: Target Won
        if target_cand == rank1:
            # Margin = Target - Rank 2
            if len(candidates) > 1:
                rank2 = candidates[1]
                margin = target_cand['votes'] - rank2['votes']
                votes_rk2 = rank2['votes']
                runner_up = rank2['party_name']
            else:
                margin = target_cand['votes'] # Only 1 candidate?
                votes_rk2 = 0
                runner_up = 'None'
            
            margin_list.append({
                'region': target_cand['region'],
                'province': prov,
                'district_number': dist,
                'district_label': f"{prov} เขต {dist}",
                'winner_party': target_cand['party_name'],
                'runner_up_party': runner_up,
                'votes_target': target_cand['votes'],
                'votes_rank2': votes_rk2,
                'margin': margin,
                'bucket': bucket_value(margin)
            })
            
        # Case 2: Target Lost
        else:
            # Gap = Rank 1 - Target
            gap = rank1['votes'] - target_cand['votes']
            
            gap_list.append({
                'region': target_cand['region'],
                'province': prov,
                'district_number': dist,
                'district_label': f"{prov} เขต {dist}",
                'winner_party': rank1['party_name'],
                'target_party': target_cand['party_name'],
                'votes_rank1': rank1['votes'],
                'votes_target': target_cand['votes'],
                'gap': gap,
                'bucket': bucket_value(gap)
            })

    # Convert to DF and Save
    df_gap = pd.DataFrame(gap_list)
    df_margin = pd.DataFrame(margin_list)
    
    # Sort for niceness (smallest gap first, largest margin first?)
    if not df_gap.empty:
        df_gap = df_gap.sort_values('gap')
        df_gap.to_csv('q7_p000_gap_list.csv', index=False, encoding='utf-8-sig')
        # Summary
        summary_gap = df_gap['bucket'].value_counts().reindex(['0-500', '501-2500', '2501-5000', '5001-10000', '10000+']).fillna(0)
        summary_gap.to_csv('q7_p000_gap_summary.csv', header=['count'], encoding='utf-8-sig')

    if not df_margin.empty:
        df_margin = df_margin.sort_values('margin', ascending=False)
        df_margin.to_csv('q7_p000_margin_list.csv', index=False, encoding='utf-8-sig')
        # Summary
        summary_margin = df_margin['bucket'].value_counts().reindex(['0-500', '501-2500', '2501-5000', '5001-10000', '10000+']).fillna(0)
        summary_margin.to_csv('q7_p000_margin_summary.csv', header=['count'], encoding='utf-8-sig')

    print(f"Analysis Complete. Won: {len(df_margin)}, Lost: {len(df_gap)}")

if __name__ == "__main__":
    main()
