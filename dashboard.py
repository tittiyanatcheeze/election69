import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import scripts.analyze_turnout as at

# --- setup ---
st.set_page_config(layout="wide", page_title="Thailand Election 2569")

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

def get_national_data():
    """Loads the master tables from the data/ directory for National Overview."""
    m_district_geo = read_csv_with_encoding('data/m_district_geo.csv')
    m_turnout_master = read_csv_with_encoding('data/m_turnout_master.csv')
    m_votes_master = read_csv_with_encoding('data/m_votes_master.csv')
    m_referendum_master = read_csv_with_encoding('data/m_referendum_master.csv')
    return m_district_geo, m_turnout_master, m_votes_master, m_referendum_master

def show_national_overview():
    st.title("Thailand Election 2569 - National Overview")
    
    df_district_geo, df_turnout_master, df_votes_master, df_referendum_master = get_national_data()
    
    # --- National KPIs ---
    st.header("National KPIs")
    
    # Use CONS ballot for national turnout figures
    turnout_cons = df_turnout_master[df_turnout_master['ballot_code'] == 'CONS'].copy()
    
    total_eligible_voters = turnout_cons['eligible_voters'].sum()
    total_voters_used = turnout_cons['voters_used'].sum()
    turnout_rate = (total_voters_used / total_eligible_voters) * 100 if total_eligible_voters > 0 else 0
    total_valid_votes = turnout_cons['valid_votes'].sum()
    total_invalid_votes = turnout_cons['invalid_votes'].sum()
    total_no_vote = turnout_cons['no_vote'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Eligible Voters", f"{total_eligible_voters:,.0f}")
    col2.metric("Total Turnout", f"{total_voters_used:,.0f}", f"{turnout_rate:.2f}%")
    col3.metric("Valid Votes", f"{total_valid_votes:,.0f}")
    
    col4, col5, col6 = st.columns(3)
    col4.metric("Invalid Votes", f"{total_invalid_votes:,.0f}")
    col5.metric("No-Votes", f"{total_no_vote:,.0f}")
    
    # --- Load Shapefile ---
    shapefile_path = "data/ECT Constituencies/2569/ShapeFile/2569_Election_Constituencies.shp"
    try:
        gdf_constituencies = gpd.read_file(shapefile_path)
        st.write("### Constituency Shapefile Data Sample")
        # Drop geometry for display to avoid Arrow serialization errors
        st.dataframe(gdf_constituencies.drop(columns='geometry').head())
    except Exception as e:
        st.error(f"Could not load shapefile: {e}")
    
    # --- Top 10 Parties by Party-List Votes ---
    st.header("Top 10 Parties by Party-List Votes")
    
    # Filter for party-list votes and sum votes per party
    party_list_votes = df_votes_master[(df_votes_master['ballot_code'] == 'PARTY') & (df_votes_master['actor_type'] == 'party')]
    top_parties = party_list_votes.groupby('party_name')['votes'].sum().nlargest(10).reset_index()
    
    fig_bar = px.bar(
        top_parties,
        x='party_name',
        y='votes',
        title='Top 10 Parties by Party-List Votes (National)',
        labels={'party_name': 'Party', 'votes': 'Total Votes'},
        text='votes'
    )
    fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig_bar.update_layout(xaxis_title="Party", yaxis_title="Total Votes", uniformtext_minsize=8, uniformtext_mode='hide')
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # --- Regional Summary Table ---
    st.header("Regional Summary")
    
    # Group turnout data by region and ballot_code (CONS)
    regional_turnout = df_turnout_master[df_turnout_master['ballot_code'] == 'CONS'].groupby('region').agg(
        total_eligible_voters=('eligible_voters', 'sum'),
        total_voters_used=('voters_used', 'sum')
    ).reset_index()
    
    regional_turnout['turnout_rate'] = (regional_turnout['total_voters_used'] / regional_turnout['total_eligible_voters']) * 100
    regional_turnout['turnout_rate'] = regional_turnout['turnout_rate'].round(2)
    
    st.dataframe(regional_turnout.style.format({
        'total_eligible_voters': "{:,.0f}",
        'total_voters_used': "{:,.0f}",
        'turnout_rate': "{:.2f}%"
    }))

def show_turnout_analysis():
    st.title("Turnout Analysis (Q1)")
    st.markdown("""
    Analysis of turnout rates for year 2569 across different ballot types:
    - **CON**: Constituency
    - **PL**: Party-List
    - **RFD**: Referendum
    """)
    
    # Load data using the analysis script logic
    with st.spinner("Loading and processing data..."):
        results = at.get_turnout_data(data_dir='data')
    
    # Sidebar control
    ballot_type = st.sidebar.radio("Select Ballot Type", ["CON", "PL", "RFD"])
    
    if ballot_type in results:
        df = results[ballot_type]
        
        st.subheader(f"Turnout Analysis: {ballot_type}")
        
        # --- District Level ---
        st.markdown("### District Level: Top & Bottom 10")
        top10, bottom10 = at.get_district_stats(df, 10)
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Top 10 Districts by Turnout**")
            st.dataframe(top10[['region', 'province', 'district_label', 'turnout_rate']].style.format({'turnout_rate': '{:.4f}'}))
        
        with c2:
            st.write("**Bottom 10 Districts by Turnout**")
            st.dataframe(bottom10[['region', 'province', 'district_label', 'turnout_rate']].style.format({'turnout_rate': '{:.4f}'}))

        # --- Province Level ---
        st.markdown("### Province Level: Top & Bottom 10")
        top10_prov, bottom10_prov = at.get_province_stats(df, 10)
        
        c3, c4 = st.columns(2)
        with c3:
            st.write("**Top 10 Provinces by Turnout**")
            st.dataframe(top10_prov[['region', 'province', 'province_turnout_rate']].style.format({'province_turnout_rate': '{:.4f}'}))
        
        with c4:
            st.write("**Bottom 10 Provinces by Turnout**")
            st.dataframe(bottom10_prov[['region', 'province', 'province_turnout_rate']].style.format({'province_turnout_rate': '{:.4f}'}))

        # --- Region Ranking ---
        st.markdown("### Regional Ranking")
        reg_stats = at.get_region_stats(df)
        st.dataframe(reg_stats[['region', 'eligible_voters_sum', 'voters_used_sum', 'region_turnout_rate']].style.format({
            'eligible_voters_sum': '{:,.0f}',
            'voters_used_sum': '{:,.0f}',
            'region_turnout_rate': '{:.4f}'
        }))
        
    
    else:
        st.error(f"No data found for {ballot_type}")

def show_territory_comparison():
    st.title("Territory Comparison (2566 vs 2569)")
    st.markdown("""
    Analysis of seats Held, Lost, and Gained between 2566 and 2569 elections.
    - **Held**: Party won in both 2566 and 2569.
    - **Lost**: Party won in 2566 but lost in 2569.
    - **Gained**: Party won in 2569 but did not win in 2566.
    """)
    
    comparisons = {
        "MFP (2566) vs People's (2569)": "q2_",
        "Pheu Thai": "q3_p034_",
        "Bhumjaithai": "q4_p063_",
        "Democrat": "q5_p001_"
    }
    
    selection = st.sidebar.selectbox("Select Comparison", list(comparisons.keys()))
    prefix = comparisons[selection]
    
    # Load summary
    try:
        summary = pd.read_csv(f'{prefix}summary_counts.csv')
        held = summary['held'].iloc[0]
        lost = summary['lost'].iloc[0]
        gained = summary['gained'].iloc[0]
        total_2569 = held + gained
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Held Seats", held)
        c2.metric("Lost Seats", lost)
        c3.metric("Gained/New Seats", gained)
        c4.metric("Total Won (2569)", total_2569)
    except:
        st.error("Summary data not found. Please run analysis script.")
        return

    # Tabs for details
    tab1, tab2, tab3, tab4 = st.tabs(["Held", "Lost", "Gained", "Province Delta"])
    
    with tab1:
        st.subheader("Held Districts")
        try:
            df = pd.read_csv(f'{prefix}held.csv')
            st.dataframe(df)
        except:
            st.info("No data or file missing.")

    with tab2:
        st.subheader("Lost Districts")
        try:
            df = pd.read_csv(f'{prefix}lost.csv')
            st.dataframe(df)
        except:
            st.info("No data or file missing.")

    with tab3:
        st.subheader("Gained Districts")
        try:
            if prefix == 'q2_':
                df = pd.read_csv('q2_new_districts.csv')
            else:
                df = pd.read_csv(f'{prefix}gained.csv')
            st.dataframe(df)
        except:
            st.info("No data or file missing.")

    with tab4:
        st.subheader("Province Seat Changes")
        try:
            # Filename logic
            if prefix == 'q2_':
                # I changed script to use prefix, but let's check if I kept q2_ compatibility or fully prefixed
                # script says: f'{prefix}province_seat_changes.csv'
                # so q2_province_seat_changes.csv is consistent.
                filename = f'{prefix}province_seat_changes.csv'
            else:
                filename = f'{prefix}province_seat_changes.csv'
                
            df = pd.read_csv(filename)
            st.dataframe(df)
        except:
             st.info("No data or file missing. Try running analysis script.")


def show_concentration_screening():
    st.title("Concentration Screening (Q6)")
    st.markdown("""
    Identification of districts with unusually concentrated vote patterns or low competition.
    - **Criteria 6.1 (Dominant Winner)**: Winner share > All others combined.
    - **Criteria 6.2 (Concentrated)**: Top 2 candidates share >= {70%, 75%, 80%}.
    - **Criteria 6.3 (Cross-Year)**: Vote pattern consistency check (2566 vs 2569).
    - **Criteria 6.4 (Low ENC)**: Effective Number of Candidates indicates low competition.
    """)
    
    # Load Main Data
    try:
        df_combined = pd.read_csv('q6_combined_flags.csv')
        df_enc_stats = pd.read_csv('q6_enc_stats.csv')
    except:
        st.error("Missing Q6 output files. Please run `scripts/analyze_concentration.py`.")
        return

    # Sidebar Filters
    years = sorted(df_combined['year'].unique())
    selected_year = st.sidebar.selectbox("Select Year", years)
    
    regions = sorted(df_combined['province'].unique()) # Using province as proxy if region col missing
    # Actually checking if region column exists in combined flags. 
    # Script does not explicitly add region to 2566 data (only province). 
    # We can filter by Province.
    search_prov = st.sidebar.text_input("Search Province", "")
    
    # Filter Data
    df_filtered = df_combined[df_combined['year'] == selected_year]
    if search_prov:
        df_filtered = df_filtered[df_filtered['province'].str.contains(search_prov, na=False)]
    
    # Summary Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Flagged Districts", len(df_filtered))
    c2.metric("Dominant Winner", len(df_filtered[df_filtered['flags'].str.contains('Dominant')]))
    c3.metric("High Concentration", len(df_filtered[df_filtered['flags'].str.contains('Concentrated')]))
    c4.metric("Low ENC", len(df_filtered[df_filtered['flags'].str.contains('Low ENC')]))
    
    st.subheader("Flagged Districts List")
    st.dataframe(df_filtered[['province', 'district_number', 'winner_party', 'share_rk1', 'enc', 'flags']])
    
    # Detailed Views
    with st.expander("ENC Statistics"):
        st.write("Effective Number of Candidates (ENC) Distribution")
        st.dataframe(df_enc_stats)
        
    with st.expander("Criteria 6.1: Dominant Winners"):
        try:
            df_61 = pd.read_csv('q6_criteria_6_1.csv')
            st.dataframe(df_61)
        except: st.info("No data.")

    with st.expander("Criteria 6.2: High Concentration Lists"):
        try:
            df_62 = pd.read_csv('q6_criteria_6_2_lists.csv')
            st.dataframe(df_62)
        except: st.info("No data.")

    with st.expander("Criteria 6.3: Cross-Year Pattern Anomalies"):
        try:
            df_63 = pd.read_csv('q6_criteria_6_3.csv')
            st.dataframe(df_63)
        except: st.info("No data.")
        
    with st.expander("Criteria 6.4: Low ENC Lists"):
        try:
            df_64 = pd.read_csv('q6_enc_low_lists.csv')
            st.dataframe(df_64)
        except: st.info("No data.")


def show_gap_analysis():
    st.title("Gap Analysis: People's Party (2569)")
    st.markdown("""
    Analysis of vote gaps for lost districts and win margins for won districts.
    - **Gap (Lost)**: Votes Winner - Votes People's Party
    - **Margin (Won)**: Votes People's Party - Votes Runner-up
    """)
    
    tab1, tab2 = st.tabs(["Gap (Lost Districts)", "Margin (Won Districts)"])
    
    with tab1:
        st.subheader("Votes Gap in Lost Districts")
        try:
            df_gap = pd.read_csv('q7_p000_gap_list.csv')
            
            # Summary Chart
            summary = df_gap['bucket'].value_counts().reindex(['0-500', '501-2500', '2501-5000', '5001-10000', '10000+']).fillna(0)
            st.bar_chart(summary)
            
            # Filter
            buckets = ['All'] + list(summary.index)
            sel_bucket = st.selectbox("Filter by Gap Bucket", buckets, key='gap_filter')
            
            if sel_bucket != 'All':
                df_show = df_gap[df_gap['bucket'] == sel_bucket]
            else:
                df_show = df_gap
                
            st.dataframe(df_show[['province', 'district_label', 'winner_party', 'target_party', 'votes_target', 'gap', 'bucket']])
        except:
            st.info("No data (Target party won all or files missing)")

    with tab2:
        st.subheader("Win Margin in Won Districts")
        try:
            df_margin = pd.read_csv('q7_p000_margin_list.csv')
            
            # Summary Chart
            summary = df_margin['bucket'].value_counts().reindex(['0-500', '501-2500', '2501-5000', '5001-10000', '10000+']).fillna(0)
            st.bar_chart(summary)
            
            # Filter
            buckets = ['All'] + list(summary.index)
            sel_bucket = st.selectbox("Filter by Margin Bucket", buckets, key='margin_filter')
            
            if sel_bucket != 'All':
                df_show = df_margin[df_margin['bucket'] == sel_bucket]
            else:
                df_show = df_margin
                
            st.dataframe(df_show[['province', 'district_label', 'winner_party', 'runner_up_party', 'votes_target', 'votes_rank2', 'margin', 'bucket']])
        except:
             st.info("No data (Target party lost all or files missing)")


def show_no_vote_analysis():
    st.title("No Vote Analysis (Q8)")
    st.markdown("Comparison of 'No Vote' rates between 2566 and 2569 for Constituency (CON) and Party List (PL).")
    
    tab1, tab2 = st.tabs(["National & Regional", "District Changes"])
    
    with tab1:
        st.subheader("National Comparison")
        try:
            df_nat = pd.read_csv('q8_no_vote_national_comparison.csv')
            # Pivot for better view
            # year, ballot_code, rate
            # We want columns: 2566, 2569, Delta
            df_nat_pivot = df_nat.pivot(index='ballot_code', columns='year', values='rate')
            df_nat_pivot['Delta'] = df_nat_pivot[2569] - df_nat_pivot[2566]
            st.dataframe(df_nat_pivot.style.format("{:.2%}"))
        except:
            st.info("National data missing.")
            
        st.subheader("Regional Comparison")
        try:
            df_reg = pd.read_csv('q8_no_vote_region_comparison.csv') # columns: region, no_vote, voters_used, rate, year, ballot_code
             # Filter by ballot
            b_code = st.radio("Select Ballot Type", ["CON", "PL"], horizontal=True, key='reg_ballot')
            
            df_r = df_reg[df_reg['ballot_code'] == b_code]
            if not df_r.empty:
                # Pivot: index=region, col=year, val=rate
                pv = df_r.pivot(index='region', columns='year', values='rate')
                if 2566 in pv.columns and 2569 in pv.columns:
                     pv['Delta'] = pv[2569] - pv[2566]
                st.dataframe(pv.style.format("{:.2%}"))
            else:
                st.info("No regional data for selected ballot type.")
        except:
            st.info("Regional data missing.")

    with tab2:
        st.subheader("District-level Changes (2569 - 2566)")
        try:
            df_dist = pd.read_csv('q8_no_vote_district_changes.csv')
            
            b_code_d = st.radio("Select Ballot Type", ["CON", "PL"], horizontal=True, key='dist_ballot')
            df_d = df_dist[df_dist['ballot_code'] == b_code_d].copy()
            
            # Search
            search = st.text_input("Search Province/District", "")
            if search:
                df_d = df_d[df_d['district_label'].str.contains(search, na=False)]
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.write("Top 10 Increase")
                top_inc = df_d.sort_values('delta_rate', ascending=False).head(10)
                st.dataframe(top_inc[['district_label', 'rate_2566', 'rate_2569', 'delta_rate']].style.format({'rate_2566': '{:.2%}', 'rate_2569': '{:.2%}', 'delta_rate': '{:.2%}'}))
                
            with c2:
                st.write("Top 10 Decrease")
                top_dec = df_d.sort_values('delta_rate', ascending=True).head(10)
                st.dataframe(top_dec[['district_label', 'rate_2566', 'rate_2569', 'delta_rate']].style.format({'rate_2566': '{:.2%}', 'rate_2569': '{:.2%}', 'delta_rate': '{:.2%}'}))
                
            with st.expander("Full Data"):
                st.dataframe(df_d)
                
        except:
            st.info("District data missing.")

            with st.expander("Full Data"):
                st.dataframe(df_d)
                

def show_typology_analysis():
    st.title("District Typology (Q9)")
    st.markdown("Classification of districts based on vote share patterns.")
    
    tab1, tab2, tab3 = st.tabs(["Typology 9.1 (P000/P034)", "Typology 9.2 (P000/P034/P001)", "Typology 9.3 (Rank 2+3 > Rank 1)"])
    
    with tab1:
        st.subheader("Typology 9.1 (P000 + P034)")
        st.markdown("""
        - **A**: P000 Winner & Dominant (> Rank 2+3)
        - **B**: P034 Winner & Dominant (> Rank 2+3)
        - **C**: Combined Non-Winner (P000+P034) > Winner
        - **D**: Others
        """)
        try:
            df91 = pd.read_csv('q9_typology_91.csv')
            counts = df91['cat_91'].value_counts()
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("Counts:")
                st.dataframe(counts)
            with c2:
                # Simple pie chart
                # Prepare for st.bar_chart or use map? Streamlit native charts are limited for Pie.
                # Use Bar chart for simplicity and robustness.
                st.bar_chart(counts)
                
            st.dataframe(df91)
        except:
             st.info("Data for 9.1 missing.")

    with tab2:
        st.subheader("Typology 9.2 (P000 + P034 + P001)")
        st.markdown("""
        - **A**: P000 Winner & Dominant
        - **B**: P034 Winner & Dominant
        - **C**: P001 Winner & Dominant
        - **D**: Combined Non-Winner (All 3) > Winner
        - **E**: Others
        """)
        try:
            df92 = pd.read_csv('q9_typology_92.csv')
            counts = df92['cat_92'].value_counts()
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("Counts:")
                st.dataframe(counts)
            with c2:
                st.bar_chart(counts)
                
            st.dataframe(df92)
        except:
             st.info("Data for 9.2 missing.")

    with tab3:
        st.subheader("Typology 9.3: Rank 2 + Rank 3 > Rank 1")
        st.markdown("Districts where the combined vote of the 2nd and 3rd place candidates exceeds the winner's vote.")
        try:
            df93 = pd.read_csv('q9_rank23_gt_rank1.csv')
            st.metric("Districts Matching Criteria", len(df93))
            st.dataframe(df93)
        except:
             st.info("Data for 9.3 missing.")


def show_referendum_analysis():
    st.title("Referendum Correlation (Q10)")
    st.markdown("Association between 2569 Referendum 'Yes' Rate and Party Vote Shares.")
    st.info("Note: These are district-level associations, not individual-level causality.")
    
    tab1, tab2 = st.tabs(["Constituency (CON)", "Party List (PL)"])
    
    with tab1:
        st.subheader("Correlation with CON Vote Shares")
        try:
            df = pd.read_csv('q10_ref_con_party_corr_summary.csv')
            st.dataframe(df.style.format({
                'pearson_r': '{:.2f}', 'pearson_p': '{:.4f}', 
                'spearman_r': '{:.2f}', 'stability_score': '{:.2f}'
            }))
            
            # Scatter Plot
            party = st.selectbox("Select Party for Scatter Plot (CON)", df['party_name'].unique())
            if party:
                # Need raw data which we don't load here to save memory, 
                # but we can advise user or load on demand if critical.
                # For now just show summary stats is sufficient per prompt outputs.
                # Prompt asked for: q10_ref_con_party_corr_summary
                # If scatter needed, we'd need to load full data.
                # Let's show specific correlation detail text.
                row = df[df['party_name'] == party].iloc[0]
                st.write(f"Pearson R: {row['pearson_r']:.2f} (p={row['pearson_p']:.4f})")
                st.write(f"Stability: {row['stability_note']} ({row['stability_score']:.2f})")
                
        except:
            st.info("CON correlation data missing.")

    with tab2:
        st.subheader("Correlation with PL Vote Shares")
        try:
            df = pd.read_csv('q10_ref_pl_party_corr_summary.csv')
            st.dataframe(df.style.format({
                'pearson_r': '{:.2f}', 'pearson_p': '{:.4f}', 
                'spearman_r': '{:.2f}', 'stability_score': '{:.2f}'
            }))
            
            party = st.selectbox("Select Party for Scatter Plot (PL)", df['party_name'].unique())
            if party:
                row = df[df['party_name'] == party].iloc[0]
                st.write(f"Pearson R: {row['pearson_r']:.2f} (p={row['pearson_p']:.4f})")
                st.write(f"Stability: {row['stability_note']} ({row['stability_score']:.2f})")
        except:
             st.info("PL correlation data missing.")

# --- Navigation ---
page = st.sidebar.radio("Go to", ["National Overview", "Turnout Analysis", "Territory Comparison", "Concentration Screening", "Gap Analysis (P000)", "No Vote Analysis (Q8)", "District Typology (Q9)", "Referendum Correlation (Q10)"])

if page == "National Overview":
    show_national_overview()
elif page == "Turnout Analysis":
    show_turnout_analysis()
elif page == "Territory Comparison":
    show_territory_comparison()
elif page == "Concentration Screening":
    show_concentration_screening()
elif page == "Gap Analysis (P000)":
    show_gap_analysis()
elif page == "No Vote Analysis (Q8)":
    show_no_vote_analysis()
elif page == "District Typology (Q9)":
    show_typology_analysis()
elif page == "Referendum Correlation (Q10)":
    show_referendum_analysis()

st.sidebar.markdown("---")
st.sidebar.markdown("Dashboard v1.7")
