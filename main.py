# -*- coding:utf-8 -*-
import os
import pickle
import json
import argparse
import numpy as np
import requests
from utils.eeg.analysis import main_anlaysis as eeg_analysis
from utils.ecg.util_func import CleanUpECG, ECGFeatureExtractor


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='이양복', type=str)
    parser.add_argument('--age', default=71, type=int)
    parser.add_argument('--measurement_date', default='2024-07-31 14:36', type=str)
    parser.add_argument('--birth', default='1953-07-20', type=str)
    parser.add_argument('--sex', default='male', choices=['male', 'female'], type=str)
    parser.add_argument('--file_name', default='2024-07-31-1436.csv', type=str)
    return parser.parse_args()


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        dtypes = (np.datetime64, np.complexfloating)
        if isinstance(obj, dtypes):
            return str(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            if any([np.issubdtype(obj.dtype, i) for i in dtypes]):
                return obj.astype(str).tolist()
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


def eeg_content_bulk(payload, name):
    return {
        'topography_delta': payload['topography'][name]['delta'],
        'topography_theta': payload['topography'][name]['theta'],
        'topography_alpha': payload['topography'][name]['alpha'],
        'topography_beta': payload['topography'][name]['beta'],
        'topography_gamma': payload['topography'][name]['gamma'],
        'connectivity_delta': payload['connectivity'][name]['delta'],
        'connectivity_theta': payload['connectivity'][name]['theta'],
        'connectivity_alpha': payload['connectivity'][name]['alpha'],
        'connectivity_beta': payload['connectivity'][name]['beta'],
        'connectivity_gamma': payload['connectivity'][name]['gamma'],
    }


if __name__ == '__main__':
    args = get_args()
    file = args.file_name
    data_path = r'D:\Project\BioSignal_Analysis_cli\database\ch'
    save_path = r'D:\Project\BioSignal_Analysis_cli\database\ch\clean'

    try:
        ecg = CleanUpECG(data_path=os.path.join(data_path, file))
        cleaned_data = ecg.save_filtered_data(save_path=save_path)
        ext = ECGFeatureExtractor(data_path=os.path.join(save_path, file), save_path=save_path,
                                  sfreq=125, age=args.age, sex=args.sex)
        hrv_results = ext.extract()
        hrv_payload = json.dumps(hrv_results, cls=NpEncoder)
    
        del cleaned_data, ext, hrv_results
    
        eeg_results = eeg_analysis(os.path.join(data_path, file))
    
        eeg_payload = json.dumps({
            'psd': eeg_results['psd_result'],
            'sleep_staging': eeg_results['sleep_stage'],
            'frontal_limbic': eeg_results['frontal_limbic'],
            'baseline': eeg_content_bulk(eeg_results, 'baseline'),
            'stimulation1': eeg_content_bulk(eeg_results, 'stimulation1'),
            'recovery1': eeg_content_bulk(eeg_results, 'recovery1'),
            'stimulation2': eeg_content_bulk(eeg_results, 'stimulation2'),
            'recovery2': eeg_content_bulk(eeg_results, 'recovery2'),
        }, cls=NpEncoder)

        headers = {'Content-type': 'application/json', 'Accept': '*/*'}
        ip = '34.64.50.127:8000'
        s_index = ['male', 'female']
        oo = requests.post('http://{}/api/v1/exp/'.format(ip),
                           data=json.dumps({'name': args.name,
                                            'measurement_date': args.measurement_date,
                                            'age': args.age,
                                            'birth': args.birth,
                                            'sex': s_index.index(args.sex),
                                            'hrv': hrv_payload,
                                            'eeg': eeg_payload}),
                           headers=headers)
        print(oo)
    except Exception:
        print('분석 불가!! 관리자에게 문의하시오')
