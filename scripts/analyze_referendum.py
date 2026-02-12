
import pandas as pd
import numpy as np
import scipy.stats as stats
from statsmodels.stats.multitest import multipletests

def load_referendum():
    try:
        try:
             df = pd.read_csv('data/m_referendum_master.csv', encoding='utf-8')
        except:
             df = pd.read_csv('data/m_referendum_master.csv', encoding='tis-620')
        
        # Filter 2569? File usually implies year or has year col
        if 'year' in df.columns:
            df = df[df['year'] == 2569]
        
        # Ensure yes_rate
        if 'yes_rate' not in df.columns:
             # Calculate? yes_votes / voters_used
             # If voters_used missing, maybe sum yes+no+invalid?
             # For now assume yes_rate exists as seen in headers
             pass
             
        return df[['district_id', 'region', 'province', 'yes_rate']]
    except Exception as e:
        print(f"Error loading referendum: {e}")
        return pd.DataFrame()

def load_votes(ballot_type):
    try:
        try:
             df = pd.read_csv('data/m_votes_master.csv', encoding='utf-8')
        except:
             df = pd.read_csv('data/m_votes_master.csv', encoding='tis-620')
             
        # Filter Year 2569
        if 'year' in df.columns:
            df = df[df['year'] == 2569]
            
        # Filter Ballot
        b_col = 'ballot_code' if 'ballot_code' in df.columns else 'ballot_type'
        if ballot_type == 'CON':
            df = df[df[b_col].isin(['CON', 'CONS'])]
        else:
            df = df[df[b_col].isin(['PL', 'PARTY'])]
            
        # Get Turnout for voters_used
        try:
             df_turnout = pd.read_csv('data/m_turnout_master.csv', encoding='utf-8')
        except:
             df_turnout = pd.read_csv('data/m_turnout_master.csv', encoding='tis-620')
        
        t_col = 'ballot_code' if 'ballot_code' in df_turnout.columns else 'ballot_type'
        if ballot_type == 'CON':
             df_turnout = df_turnout[df_turnout[t_col].isin(['CON', 'CONS'])]
        else:
             df_turnout = df_turnout[df_turnout[t_col].isin(['PL', 'PARTY'])]
             
        turnout_map = df_turnout.set_index('district_id')['voters_used'].to_dict()
        df['voters_used'] = df['district_id'].map(turnout_map)
        
        # Aggregate Party Votes per District
        # Group by district_id, party_id (or name)
        # Use party_name for display
        grp = df.groupby(['district_id', 'party_name']).agg({
            'votes': 'sum',
            'voters_used': 'first' # Should be same for district
        }).reset_index()
        
        # Calculate Share
        grp['party_share'] = grp['votes'] / grp['voters_used']
        
        return grp
    except Exception as e:
        print(f"Error loading votes {ballot_type}: {e}")
        return pd.DataFrame()

def analyze_referendum():
    df_ref = load_referendum()
    if df_ref.empty: return

    for ballot_type in ['CON', 'PL']:
        print(f"Analyzing {ballot_type}...")
        df_votes = load_votes(ballot_type)
        if df_votes.empty: continue
        
        # Pivot votes to get one row per district, cols = party shares? 
        # Or just merge on district_id and iterate parties?
        # Iterate parties is better for coverage check
        
        # Join Ref + Votes
        merged = pd.merge(df_ref, df_votes, on='district_id')
        
        results = []
        
        parties = merged['party_name'].unique()
        
        for party in parties:
            sub = merged[merged['party_name'] == party]
            n = len(sub)
            if n < 200: continue
            
            # Correlation
            # Drop NA
            sub = sub.dropna(subset=['yes_rate', 'party_share'])
            if len(sub) < 200: continue
            
            r_p, p_p = stats.pearsonr(sub['yes_rate'], sub['party_share'])
            r_s, p_s = stats.spearmanr(sub['yes_rate'], sub['party_share'])
            
            # Robustness: Region Sign Consistency
            # Group by region, calc sign
            regions = sub['region'].unique()
            signs = []
            for reg in regions:
                sub_reg = sub[sub['region'] == reg]
                if len(sub_reg) > 10: # Minimum to calc corr
                    try:
                        rr, _ = stats.pearsonr(sub_reg['yes_rate'], sub_reg['party_share'])
                        if not np.isnan(rr):
                            signs.append(np.sign(rr))
                    except: pass
            
            # Stability score: % of regions matching the global sign
            global_sign = np.sign(r_p)
            if signs:
                stability = sum(1 for s in signs if s == global_sign) / len(signs)
            else:
                stability = 0
                
            stability_note = "Consistent" if stability > 0.7 else "Variable"
            
            results.append({
                'party_name': party,
                'coverage_n': n,
                'pearson_r': r_p,
                'pearson_p': p_p,
                'spearman_r': r_s,
                'spearman_p': p_s,
                'stability_score': stability,
                'stability_note': stability_note
            })
            
        if not results:
            print(f"No parties met coverage in {ballot_type}")
            continue
            
        df_res = pd.DataFrame(results)
        
        # FDR Correction
        # Apply to Pearson P
        reject, pvals_corrected, _, _ = multipletests(df_res['pearson_p'], alpha=0.05, method='fdr_bh')
        df_res['fdr_significant'] = reject
        
        # Sort by absolute Pearson R
        df_res['abs_r'] = df_res['pearson_r'].abs()
        df_res = df_res.sort_values('abs_r', ascending=False).drop(columns=['abs_r'])
        
        # Save
        df_res.to_csv(f'q10_ref_{ballot_type.lower()}_party_corr_summary.csv', index=False, encoding='utf-8-sig')
        
    print("Analysis Complete.")

if __name__ == "__main__":
    analyze_referendum()
