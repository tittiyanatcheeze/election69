import json
import pandas as pd

def load_data():
    """Loads all the raw data files into pandas DataFrames."""
    
    # Load constituency info
    with open('info_constituency.txt', 'r', encoding='utf-8') as f:
        info_constituency_json = json.load(f)
    df_constituency_info = pd.DataFrame(info_constituency_json)
    
    # Load province info
    with open('info_province.txt', 'r', encoding='utf-8') as f:
        info_province_json = json.load(f)
    df_province_info = pd.DataFrame(info_province_json['province'])

    # Load main election stats
    with open('stats_cons.txt', 'r', encoding='utf-8') as f:
        stats_cons_json = json.load(f)
    
    # Load referendum stats
    with open('stat_referendum.txt', 'r', encoding='utf-8') as f:
        stat_referendum_json = json.load(f)

    # Load party info
    with open('info_party_overview.txt', 'r', encoding='utf-8') as f:
        info_party_overview_json = json.load(f)
    df_party_info = pd.DataFrame(info_party_overview_json)

    print("Data loaded successfully")
    return df_constituency_info, df_province_info, stats_cons_json, stat_referendum_json, df_party_info

def create_region_mapping():
    """Creates a mapping of provinces to regions."""
    region_mapping = {
        # Northern
        'เชียงใหม่': 'North', 'เชียงราย': 'North', 'ลำปาง': 'North', 'ลำพูน': 'North',
        'แม่ฮ่องสอน': 'North', 'น่าน': 'North', 'พะเยา': 'North', 'แพร่': 'North',
        'อุตรดิตถ์': 'North', 'ตาก': 'West', 'สุโขทัย': 'Central', 'พิษณุโลก': 'Central',
        'พิจิตร': 'Central', 'กำแพงเพชร': 'Central', 'เพชรบูรณ์': 'Central',
        # Northeastern
        'นครราชสีมา': 'Northeast', 'บุรีรัมย์': 'Northeast', 'สุรินทร์': 'Northeast',
        'ศรีสะเกษ': 'Northeast', 'อุบลราชธานี': 'Northeast', 'ยโสธร': 'Northeast',
        'ชัยภูมิ': 'Northeast', 'อำนาจเจริญ': 'Northeast', 'บึงกาฬ': 'Northeast',
        'หนองบัวลำภู': 'Northeast', 'ขอนแก่น': 'Northeast', 'อุดรธานี': 'Northeast',
        'เลย': 'Northeast', 'หนองคาย': 'Northeast', 'มหาสารคาม': 'Northeast',
        'ร้อยเอ็ด': 'Northeast', 'กาฬสินธุ์': 'Northeast', 'สกลนคร': 'Northeast',
        'นครพนม': 'Northeast', 'มุกดาหาร': 'Northeast',
        # Western
        'ราชบุรี': 'West', 'กาญจนบุรี': 'West', 'สุพรรณบุรี': 'Central', 'เพชรบุรี': 'West',
        'ประจวบคีรีขันธ์': 'West',
        # Central
        'กรุงเทพมหานคร': 'Central', 'สมุทรปราการ': 'Central', 'นนทบุรี': 'Central',
        'ปทุมธานี': 'Central', 'พระนครศรีอยุธยา': 'Central', 'อ่างทอง': 'Central',
        'ลพบุรี': 'Central', 'สิงห์บุรี': 'Central', 'ชัยนาท': 'Central',
        'สระบุรี': 'Central', 'นครนายก': 'Central', 'นครสวรรค์': 'Central',
        'อุทัยธานี': 'Central', 'นครปฐม': 'Central', 'สมุทรสาคร': 'Central',
        'สมุทรสงคราม': 'Central',
        # Eastern
        'ชลบุรี': 'East', 'ระยอง': 'East', 'จันทบุรี': 'East', 'ตราด': 'East',
        'ฉะเชิงเทรา': 'East', 'ปราจีนบุรี': 'East', 'สระแก้ว': 'East',
        # Southern
        'นครศรีธรรมราช': 'South', 'กระบี่': 'South', 'พังงา': 'South', 'ภูเก็ต': 'South',
        'สุราษฎร์ธานี': 'South', 'ระนอง': 'South', 'ชุมพร': 'South', 'สงขลา': 'South',
        'สตูล': 'South', 'ตรัง': 'South', 'พัทลุง': 'South', 'ปัตตานี': 'South',
        'ยะลา': 'South', 'นราธิวาส': 'South'
    }
    return region_mapping

if __name__ == '__main__':
    df_constituency_info, df_province_info, stats_cons_json, stat_referendum_json, df_party_info = load_data()
    
    region_mapping = create_region_mapping()
    df_province_info['region'] = df_province_info['province'].map(region_mapping)

    # Build district_dim
    df_district_dim = pd.merge(df_constituency_info, df_province_info, on='prov_id')
    df_district_dim = df_district_dim[['cons_id', 'prov_id', 'province', 'cons_no', 'region']]
    df_district_dim = df_district_dim.rename(columns={
        'cons_id': 'district_id',
        'cons_no': 'district_number'
    })
    df_district_dim['year'] = 2569

    print("\ndistrict_dim DataFrame:")
    print(df_district_dim.head())

    # Build turnout DataFrame
    turnout_data = []
    for province in stats_cons_json['result_province']:
        for cons in province['constituencies']:
            turnout_data.append({
                'district_id': cons['cons_id'],
                'ballot_code': 'CONS',
                'voters_used': cons['turn_out'],
                'valid_votes': cons['valid_votes'],
                'invalid_votes': cons['invalid_votes'],
                'no_vote': cons['blank_votes']
            })
            turnout_data.append({
                'district_id': cons['cons_id'],
                'ballot_code': 'PARTY',
                'voters_used': cons['party_list_turn_out'],
                'valid_votes': cons['party_list_valid_votes'],
                'invalid_votes': cons['party_list_invalid_votes'],
                'no_vote': cons['party_list_blank_votes']
            })
    df_turnout = pd.DataFrame(turnout_data)
    
    # Merge with constituency info to get eligible_voters
    df_turnout = pd.merge(df_turnout, df_constituency_info[['cons_id', 'registered_vote']], left_on='district_id', right_on='cons_id', how='left')
    df_turnout = df_turnout.rename(columns={'registered_vote': 'eligible_voters'})
    df_turnout['year'] = 2569
    df_turnout = df_turnout.drop(columns=['cons_id'])


    print("\nturnout DataFrame:")
    print(df_turnout.head())

    # Build votes DataFrame
    votes_data = []
    for province in stats_cons_json['result_province']:
        for cons in province['constituencies']:
            # Candidate votes
            for candidate in cons['candidates']:
                votes_data.append({
                    'district_id': cons['cons_id'],
                    'ballot_code': 'CONS',
                    'actor_type': 'candidate',
                    'party_id': candidate['party_id'],
                    'votes': candidate['mp_app_vote'],
                    'rank': candidate['mp_app_rank']
                })
            # Party-list votes
            for party in cons['result_party']:
                votes_data.append({
                    'district_id': cons['cons_id'],
                    'ballot_code': 'PARTY',
                    'actor_type': 'party',
                    'party_id': party['party_id'],
                    'votes': party['party_list_vote'],
                    'rank': None  # Rank is not available for party-list votes in the source
                })
    df_votes = pd.DataFrame(votes_data)
    
    # Calculate rank for party-list votes
    df_votes['rank'] = df_votes[df_votes['actor_type'] == 'party'].groupby(['district_id', 'ballot_code'])['votes'].rank(method='min', ascending=False)
    
    # Merge with party info to get party_name
    # The party id in df_party_info is string, so we need to convert it
    df_party_info['id'] = pd.to_numeric(df_party_info['id'])
    df_votes = pd.merge(df_votes, df_party_info[['id', 'name']], left_on='party_id', right_on='id', how='left')
    df_votes = df_votes.rename(columns={'name': 'party_name'})
    df_votes['year'] = 2569
    df_votes = df_votes.drop(columns=['id'])

    print("\nvotes DataFrame:")
    print(df_votes.head())
    
    # Build referendum_results DataFrame
    referendum_data = []
    for province in stat_referendum_json['result_province']:
        for cons in province['constituencies']:
            # The key for the results is a UUID, so we get it dynamically
            result_key = list(cons['referendum_results'].keys())[0]
            referendum_data.append({
                'district_id': cons['cons_id'],
                'ballot_code': 'RFD',
                'yes_votes': cons['referendum_results'][result_key]['yes'],
                'no_votes': cons['referendum_results'][result_key]['no'],
                'voters_used': cons['referendum_turn_out']
            })
    df_referendum = pd.DataFrame(referendum_data)
    df_referendum['year'] = 2569
    
    print("\nreferendum_results DataFrame:")
    print(df_referendum.head())

def validate_schema(df_district_dim, df_turnout, df_votes, df_referendum):
    """Performs schema validation on the DataFrames."""
    
    print("\n--- Schema Validation ---")
    
    # A) Print column lists and dtypes
    print("\n--- A) Column Lists and Dtypes ---")
    print("\ndistrict_dim:")
    df_district_dim.info()
    print("\nturnout:")
    df_turnout.info()
    print("\nvotes:")
    df_votes.info()
    print("\nreferendum_results:")
    df_referendum.info()

    # B) Validate uniqueness and grain
    print("\n--- B) Uniqueness and Grain Validation ---")
    print("district_dim unique on (district_id, year):", df_district_dim.duplicated(subset=['district_id', 'year']).sum() == 0)
    
    # Need to create df_districts for this check
    df_districts = df_turnout[['district_id', 'year', 'ballot_code']].drop_duplicates()
    print("districts unique on (district_id, year, ballot_code):", df_districts.duplicated(subset=['district_id', 'year', 'ballot_code']).sum() == 0)
    
    print("turnout unique on (district_id, year, ballot_code):", df_turnout.duplicated(subset=['district_id', 'year', 'ballot_code']).sum() == 0)
    print("referendum_results unique on (district_id, year):", df_referendum[df_referendum['ballot_code'] == 'RFD'].duplicated(subset=['district_id', 'year']).sum() == 0)

    # C) Validate join coverage
    print("\n--- C) Join Coverage Validation ---")
    
    # district_dim joins districts
    merged_dim_districts = pd.merge(df_district_dim, df_districts, on=['district_id', 'year'], how='left')
    print("district_dim joins districts with no missing:", merged_dim_districts['ballot_code'].isnull().sum() == 0)

    # turnout joins districts
    merged_turnout_districts = pd.merge(df_turnout, df_districts, on=['district_id', 'year', 'ballot_code'], how='left', indicator=True)
    print("turnout joins districts with no missing:", len(merged_turnout_districts[merged_turnout_districts['_merge'] == 'left_only']) == 0)

    # votes joins districts
    merged_votes_districts = pd.merge(df_votes, df_districts, on=['district_id', 'year', 'ballot_code'], how='left', indicator=True)
    print("votes joins districts with no missing:", len(merged_votes_districts[merged_votes_districts['_merge'] == 'left_only']) == 0)

    # referendum_results joins district_dim
    merged_ref_dim = pd.merge(df_referendum, df_district_dim, on=['district_id', 'year'], how='left', indicator=True)
    print("referendum_results joins district_dim with no missing:", len(merged_ref_dim[merged_ref_dim['_merge'] == 'left_only']) == 0)

    # D) Validate rank integrity in votes
    print("\n--- D) Rank Integrity Validation ---")
    candidate_votes = df_votes[df_votes['actor_type'] == 'candidate']
    
    # min rank = 1
    min_rank_is_1 = candidate_votes.groupby(['district_id', 'year', 'ballot_code'])['rank'].min().eq(1).all()
    print("Min rank is 1 for all groups:", min_rank_is_1)

    # ranks are integers
    ranks_are_integers = pd.api.types.is_integer_dtype(candidate_votes['rank'])
    print("Ranks are integers:", ranks_are_integers)

    # if ties exist, report them
    tied_ranks = candidate_votes[candidate_votes.duplicated(subset=['district_id', 'year', 'ballot_code', 'rank'], keep=False)]
    if not tied_ranks.empty:
        print("Tied ranks found:")
        print(tied_ranks)
    else:
        print("No tied ranks found.")

    # ranks should be consecutive
    def check_consecutive(s):
        return sorted(s.tolist()) == list(range(1, len(s) + 1))

    consecutive_ranks = candidate_votes.groupby(['district_id', 'year', 'ballot_code'])['rank'].apply(check_consecutive)
    if not consecutive_ranks.all():
        print("Rank gaps found in some groups:")
        print(consecutive_ranks[~consecutive_ranks])
    else:
        print("Ranks are consecutive in all groups.")
        
    print("\n--- Validation Complete ---")


if __name__ == '__main__':
    # ... (previous code) ...
    df_constituency_info, df_province_info, stats_cons_json, stat_referendum_json, df_party_info = load_data()
    
    region_mapping = create_region_mapping()
    df_province_info['region'] = df_province_info['province'].map(region_mapping)

    # Build district_dim
    df_district_dim = pd.merge(df_constituency_info, df_province_info, on='prov_id')
    df_district_dim = df_district_dim[['cons_id', 'prov_id', 'province', 'cons_no', 'region']]
    df_district_dim = df_district_dim.rename(columns={
        'cons_id': 'district_id',
        'cons_no': 'district_number'
    })
    df_district_dim['year'] = 2569

    # Build turnout DataFrame
    turnout_data = []
    for province in stats_cons_json['result_province']:
        for cons in province['constituencies']:
            turnout_data.append({
                'district_id': cons['cons_id'],
                'ballot_code': 'CONS',
                'voters_used': cons['turn_out'],
                'valid_votes': cons['valid_votes'],
                'invalid_votes': cons['invalid_votes'],
                'no_vote': cons['blank_votes']
            })
            turnout_data.append({
                'district_id': cons['cons_id'],
                'ballot_code': 'PARTY',
                'voters_used': cons['party_list_turn_out'],
                'valid_votes': cons['party_list_valid_votes'],
                'invalid_votes': cons['party_list_invalid_votes'],
                'no_vote': cons['party_list_blank_votes']
            })
    df_turnout = pd.DataFrame(turnout_data)
    
    # Merge with constituency info to get eligible_voters
    df_turnout = pd.merge(df_turnout, df_constituency_info[['cons_id', 'registered_vote']], left_on='district_id', right_on='cons_id', how='left')
    df_turnout = df_turnout.rename(columns={'registered_vote': 'eligible_voters'})
    df_turnout['year'] = 2569
    df_turnout = df_turnout.drop(columns=['cons_id'])

    # Build votes DataFrame
    votes_data = []
    for province in stats_cons_json['result_province']:
        for cons in province['constituencies']:
            # Candidate votes
            for candidate in cons['candidates']:
                votes_data.append({
                    'district_id': cons['cons_id'],
                    'ballot_code': 'CONS',
                    'actor_type': 'candidate',
                    'party_id': candidate['party_id'],
                    'votes': candidate['mp_app_vote'],
                    'rank': candidate['mp_app_rank']
                })
            # Party-list votes
            for party in cons['result_party']:
                votes_data.append({
                    'district_id': cons['cons_id'],
                    'ballot_code': 'PARTY',
                    'actor_type': 'party',
                    'party_id': party['party_id'],
                    'votes': party['party_list_vote'],
                    'rank': 0 # Rank is not available for party-list votes in the source, will calculate later
                })
    df_votes = pd.DataFrame(votes_data)
    
    # Calculate rank for party-list votes
    df_votes.loc[df_votes['actor_type'] == 'party', 'rank'] = df_votes[df_votes['actor_type'] == 'party'].groupby(['district_id', 'ballot_code'])['votes'].rank(method='min', ascending=False)
    
    # Merge with party info to get party_name
    # The party id in df_party_info is string, so we need to convert it
    df_party_info['id'] = pd.to_numeric(df_party_info['id'])
    df_votes = pd.merge(df_votes, df_party_info[['id', 'name']], left_on='party_id', right_on='id', how='left')
    df_votes = df_votes.rename(columns={'name': 'party_name'})
    df_votes['year'] = 2569
    df_votes = df_votes.drop(columns=['id'])

    # Build referendum_results DataFrame
    referendum_data = []
    for province in stat_referendum_json['result_province']:
        for cons in province['constituencies']:
            # The key for the results is a UUID, so we get it dynamically
            if cons['referendum_results']:
                result_key = list(cons['referendum_results'].keys())[0]
                referendum_data.append({
                    'district_id': cons['cons_id'],
                    'ballot_code': 'RFD',
                    'yes_votes': cons['referendum_results'][result_key]['yes'],
                    'no_votes': cons['referendum_results'][result_key]['no'],
                    'voters_used': cons['referendum_turn_out']
                })
    df_referendum = pd.DataFrame(referendum_data)
    df_referendum['year'] = 2569

    validate_schema(df_district_dim, df_turnout, df_votes, df_referendum)

    print("\n--- Building Master Tables ---")

    # A) m_district_geo
    print("\nBuilding m_district_geo...")
    m_district_geo = df_district_dim.copy()
    m_district_geo['district_label'] = m_district_geo['province'].astype(str) + "-" + m_district_geo['district_number'].astype(str)
    m_district_geo = m_district_geo[['district_id', 'year', 'region', 'province', 'district_number', 'district_label']]
    m_district_geo.to_csv('m_district_geo.csv', index=False)
    print("m_district_geo created and saved.")

    # B) m_turnout_master
    print("\nBuilding m_turnout_master...")
    m_turnout_master = pd.merge(df_turnout, m_district_geo, on=['district_id', 'year'])
    m_turnout_master['turnout_rate'] = m_turnout_master['voters_used'] / m_turnout_master['eligible_voters']
    # Sanity check
    m_turnout_master.loc[m_turnout_master['eligible_voters'] == 0, 'turnout_rate'] = 0
    print("Turnout rates outside [0,1]:", m_turnout_master[(m_turnout_master['turnout_rate'] < 0) | (m_turnout_master['turnout_rate'] > 1)].shape[0])
    m_turnout_master = m_turnout_master[['district_id', 'year', 'ballot_code', 'region', 'province', 'district_number', 'district_label', 'eligible_voters', 'voters_used', 'valid_votes', 'invalid_votes', 'no_vote', 'turnout_rate']]
    m_turnout_master.to_csv('m_turnout_master.csv', index=False)
    print("m_turnout_master created and saved.")

    # C) m_votes_master
    print("\nBuilding m_votes_master...")
    m_votes_master = pd.merge(df_votes, m_district_geo, on=['district_id', 'year'])
    m_votes_master = pd.merge(m_votes_master, df_turnout[['district_id', 'year', 'ballot_code', 'voters_used']], on=['district_id', 'year', 'ballot_code'])
    m_votes_master['vote_share'] = m_votes_master['votes'] / m_votes_master['voters_used']
    # Sanity check
    m_votes_master.loc[m_votes_master['voters_used'] == 0, 'vote_share'] = 0
    print("Vote shares outside [0,1]:", m_votes_master[(m_votes_master['vote_share'] < 0) | (m_votes_master['vote_share'] > 1)].shape[0])
    m_votes_master = m_votes_master[['district_id', 'year', 'ballot_code', 'actor_type', 'party_id', 'party_name', 'votes', 'rank', 'region', 'province', 'district_number', 'district_label', 'voters_used', 'vote_share']]
    m_votes_master.to_csv('m_votes_master.csv', index=False)
    print("m_votes_master created and saved.")

    # D) m_referendum_master
    print("\nBuilding m_referendum_master...")
    m_referendum_master = pd.merge(df_referendum, m_district_geo, on=['district_id', 'year'])
    # Join with turnout to get eligible_voters
    m_referendum_master = pd.merge(m_referendum_master, df_turnout[['district_id', 'year', 'eligible_voters']], on=['district_id', 'year'], how='left')
    m_referendum_master = m_referendum_master.drop_duplicates(subset=['district_id', 'year'])

    print("Referendum year=2569 exists:", 2569 in m_referendum_master['year'].unique())
    print("Referendum ballot_code=RFD exists:", 'RFD' in m_referendum_master['ballot_code'].unique())
    
    m_referendum_master['yes_rate'] = m_referendum_master['yes_votes'] / m_referendum_master['voters_used']
    m_referendum_master['referendum_turnout_rate'] = m_referendum_master['voters_used'] / m_referendum_master['eligible_voters']
    # Sanity checks
    m_referendum_master.loc[m_referendum_master['voters_used'] == 0, 'yes_rate'] = 0
    m_referendum_master.loc[m_referendum_master['eligible_voters'] == 0, 'referendum_turnout_rate'] = 0
    print("Yes rates outside [0,1]:", m_referendum_master[(m_referendum_master['yes_rate'] < 0) | (m_referendum_master['yes_rate'] > 1)].shape[0])

    m_referendum_master.to_csv('m_referendum_master.csv', index=False)
    print("m_referendum_master created and saved.")

def generate_readiness_report(m_district_geo, m_turnout_master, m_votes_master, m_referendum_master, tied_ranks, consecutive_ranks):
    """Generates and prints the readiness report."""
    
    print("\n--- Readiness Report ---")
    
    # Row counts
    print("\n--- Row Counts ---")
    print(f"m_district_geo: {len(m_district_geo)} rows")
    print("\nm_turnout_master by ballot_code and year:")
    print(m_turnout_master.groupby(['year', 'ballot_code']).size())
    print("\nm_votes_master by ballot_code and year:")
    print(m_votes_master.groupby(['year', 'ballot_code']).size())
    print(f"\nm_referendum_master: {len(m_referendum_master)} rows")

    # Anomalies
    print("\n--- Anomalies Found ---")
    
    # Missing eligible voters
    missing_eligible = m_turnout_master['eligible_voters'].isnull().sum()
    if missing_eligible > 0:
        print(f"\n- Missing 'eligible_voters': {missing_eligible} records in m_turnout_master. This will result in null turnout_rate.")
        print("  - District BKK_0 has no registered voters in the source data.")

    # Tied ranks
    if not tied_ranks.empty:
        print("\n- Tied Ranks in 'votes' table (candidate actor_type):")
        print("  - Ties were found for candidate rankings in some districts.")
        print("  - This means multiple candidates had the same rank in the same district.")
        print(f"  - Number of tied vote records: {len(tied_ranks)}")
        print("  - Example of tied ranks:")
        print(tied_ranks.head())

    # Rank gaps
    if not consecutive_ranks.all():
        print("\n- Non-Consecutive Ranks in 'votes' table (candidate actor_type):")
        print("  - Gaps in candidate rankings were found in some districts.")
        print("  - This is a direct result of tied ranks when using 'min' ranking method (e.g., 1, 2, 2, 4).")
        print(f"  - Number of groups with rank gaps: {len(consecutive_ranks[~consecutive_ranks])}")
        print("  - Groups with gaps:")
        print(consecutive_ranks[~consecutive_ranks])
        
    print("\n--- Report Complete ---")


if __name__ == '__main__':
    # ... (previous code) ...
    # (The entire script up to the end of building master tables)
    # ...
    
    # Run validation and capture anomalies
    # (This is a simplified way to get the anomalies from the validation function)
    candidate_votes = df_votes[df_votes['actor_type'] == 'candidate']
    tied_ranks = candidate_votes[candidate_votes.duplicated(subset=['district_id', 'year', 'ballot_code', 'rank'], keep=False)]
    def check_consecutive(s):
        return sorted(s.tolist()) == list(range(1, len(s) + 1))
    consecutive_ranks = candidate_votes.groupby(['district_id', 'year', 'ballot_code'])['rank'].apply(check_consecutive)

    generate_readiness_report(m_district_geo, m_turnout_master, m_votes_master, m_referendum_master, tied_ranks, consecutive_ranks)

