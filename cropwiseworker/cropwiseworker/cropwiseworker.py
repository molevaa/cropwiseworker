#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import pandas as pd

def data_downloader(endpoint, token, params=None, data_format=None, version=None):
    print(endpoint.upper(),'DOWNLOADING IS STARTED')
    all_data = []
    base_version='v3'
    if version is not None:
        base_version=version
    base_url = 'https://operations.cropwise.com/api/'+str(base_version)+'/'
    headers = {
        "Content-Type": "application/json",
        "X-User-Api-Token": token
    }

    base_params = {'sort_by': 'id_asc'}
    if params is not None:
        base_params.update(params)

    get = requests.get(f'{base_url}{endpoint}', headers=headers, params=base_params)
    try:
        record_id = json.loads(get.text)['data'][0]['id']
        iter_num = 0
        
        while True:
            try:
                iter_params = {'from_id': record_id}
                iter_params.update(base_params)

                get = requests.get(f'{base_url}{endpoint}', headers=headers, params=iter_params)
                data = json.loads(get.text)['data']

                all_data.extend(data)
                record_id = data[-1]['id'] + 1
                iter_num += 1
                print('Iteration num:', iter_num, 'Last added record id:', record_id - 1)
            except (IndexError, KeyError):
                print('The work is done...')
                break
                
        if data_format == 'json':
            return all_data
        else:
            return pd.DataFrame(all_data)
    except IndexError:
        print('DATA IS MISSING')
    

def agrimatrix_dataset(enterprise, token, season):
    fields=cw.data_downloader('fields',token)
    
    def calculate_centroid_as_string(geojson_str):
        try:
            geom = shape(json.loads(geojson_str))
            centroid = geom.centroid
            return f"{centroid.y}, {centroid.x}"
        except Exception as e:
            return None
    
    fields['centroid'] = fields['shape_simplified_geojson'].apply(calculate_centroid_as_string)
    fields_reworked=fields[['id', 'centroid','calculated_area', 'legal_area', 'tillable_area']].rename(columns={'id':'field_id'})

    crops=cw.data_downloader('crops',token)
    crops=crops[['id', 'name']].rename(columns={'id':'crop_id'})

    params={'year':season-1}
    history_items_previous=cw.data_downloader('history_items',token,params=params)
    history_items_previous=history_items_previous[['field_id','crop_id','variety']]
    history_items_previous=history_items_previous.merge(crops,how='left',on='crop_id').drop(columns='crop_id').rename(columns={'name':'ancestor','variety':'ancestor_variety'})
    history_items_previous=history_items_previous[['field_id','ancestor','ancestor_variety']]

    params={'year':season}
    history_items_current=cw.data_downloader('history_items',token,params=params)
    history_items_current=history_items_current[['field_id','crop_id','variety','sowing_date','harvesting_date','harvested_weight']]
    history_items_current=history_items_current.merge(crops,how='left',on='crop_id').drop(columns='crop_id').rename(columns={'name':'crop','variety':'crop_variety'})
    history_items_current=history_items_current[['field_id','crop','crop_variety','sowing_date','harvesting_date','harvested_weight']]

    crop_rotation=fields_reworked.merge(history_items_previous,how='left',on='field_id').merge(history_items_current,how='left',on='field_id')

    soil_tests=cw.data_downloader('soil_tests',token)

    soil_tests_reworked=soil_tests.join(pd.json_normalize(soil_tests['elements'])).drop(columns=['elements']).sort_values(by=['field_id', 'made_at'], ascending=[True, False]).drop_duplicates(subset='field_id')
    ph_columns = [col for col in soil_tests_reworked.columns if 'pH' in col]
    soil_tests_reworked['pH_combined'] = soil_tests_reworked[ph_columns].bfill(axis=1).iloc[:, 0]
    soil_tests_reworked=soil_tests_reworked[['field_id','pH_combined','organic_matter','P','K','S','made_at']]

    yield_and_soil_params=crop_rotation.merge(soil_tests_reworked,how='left',on='field_id')

    chemicals=cw.data_downloader('chemicals',token)
    chemicals=chemicals[['id','chemical_type','name']].rename(columns={'id':'applicable_id','name':'applicable_name','chemical_type':'applicable_feature'})

    seeds=cw.data_downloader('seeds',token)
    seeds=seeds[['id','name']].rename(columns={'id':'applicable_id','name':'applicable_name'})

    fertilizers=cw.data_downloader('fertilizers',token)
    fertilizers=fertilizers[['id','fertilizer_type','name']].rename(columns={'id':'applicable_id','name':'applicable_name','fertilizer_type':'applicable_feature'})

    applicable=pd.concat([chemicals,seeds,fertilizers])

    work_types=cw.data_downloader('work_types',token)
    work_types=work_types[['id','name']].rename(columns={'id':'work_type_id','name':'work_type_name'})

    application_mix_items=cw.data_downloader('application_mix_items',token,params=params)

    application_mix_items_reworked=application_mix_items[['id','agro_operation_id','applicable_type','applicable_id','fact_amount','fact_rate','planned_amount','planned_rate']]

    mix_items_applicable=application_mix_items_reworked.merge(applicable,how='left',on='applicable_id').drop_duplicates(subset=['id'])

    params={'season':season}
    agro_operations=cw.data_downloader('agro_operations',token,params=params)

    agro_operations_work_types=agro_operations.merge(work_types,how='left',on='work_type_id')
    agro_operations_reworked=agro_operations_work_types[['id','season','field_id','operation_type', 'operation_subtype','work_type_name','status','actual_start_datetime','completed_date','fact_water_rate','humidity','protein_content','planned_water_rate']].dropna(subset=['completed_date']).rename(columns={'id':'agro_operation_id'})

    ao_with_ami=agro_operations_reworked.merge(mix_items_applicable,how='left',on='agro_operation_id').drop(columns=['id'])

    first_half=ao_with_ami[['field_id','agro_operation_id', 'season', 'operation_type',
           'operation_subtype', 'work_type_name','applicable_type','applicable_feature', 'applicable_name',
           'actual_start_datetime', 'completed_date', 'fact_amount', 'fact_rate', 'planned_amount',
           'planned_rate','fact_water_rate','humidity', 'protein_content', 'planned_water_rate']]

    def transform_dataframe(df):
        df['operation_count'] = df.groupby('field_id').cumcount() + 1
        new_column_names = []
        for i in range(1, df['operation_count'].max() + 1):
            for col in df.columns.drop(['field_id', 'operation_count']):
                new_column_names.append(f"{col}_{i}")
        pivot_data_grouped = pd.DataFrame(index=df['field_id'].unique(), columns=new_column_names)
        for index, row in df.iterrows():
            count = row['operation_count']
            for col in df.columns.drop(['field_id', 'operation_count']):
                pivot_data_grouped.at[row['field_id'], f"{col}_{count}"] = row[col]
        pivot_data_grouped.reset_index(inplace=True)
        pivot_data_grouped.rename(columns={"index": "field_id"}, inplace=True)
        return pivot_data_grouped

    transform_half=transform_dataframe(first_half)

    pre_final_part1=yield_and_soil_params.merge(transform_half,how='left',on='field_id')

    for_deleting=[]
    for x in pre_final_part1.columns.to_list():
        if x.startswith('season') or x.startswith('agro_operation_id'):
            for_deleting.append(x)

    pre_final_part2=pre_final_part1.drop(columns=for_deleting)
    columns=pre_final_part2.columns.to_list()
    pre_final_part2['season']=season
    pre_final_part2['eterprise']=enterprise
    final=pre_final_part2[['season','eterprise']+columns]
    return final


