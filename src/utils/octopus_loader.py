import os
import time
import requests


import pandas as pd


from utils.logger import get_logger


logger = get_logger('octopus-loader')


class OctopusLoader():
    
    def __init__(self, namespace, measuring_point, metric, interval, url, stage='standardized'):
        self.namespace = namespace
        self.measuring_point = measuring_point
        self.metric = metric
        self.interval = interval
        self.url = url
        self.stage = stage


    def get(self, start_ts, end_ts, today_time, step, test_mode=False):
        if test_mode is False:
            logger.info('Load data from Octopus')
            return self._get_from_server(start_ts, end_ts, today_time, step)
        else:
            logger.info('Load data from test data')
            TEST_DATA_PATH = os.environ.get('TEST_DATA_PATH', '/apps/data/sample.csv')
            df = pd.read_csv(
                TEST_DATA_PATH,
                dtype={'value': float},
                parse_dates=['ts']
            )
            return df[
                (df['ts'] >= pd.to_datetime(start_ts, unit='s')) \
                & (df['ts'] <= pd.to_datetime(end_ts, unit='s'))
            ]


    def _get_from_server(self, start_ts, end_ts, today_time, step):
        query = (
            '{metric}'
            '{{measuring_point_namespace=\"{namespace}\",'
            'measuring_point=\"{measuring_point}\",'
            'stage=\"{stage}\",'
            'interval=\"{interval}\"}}'
        ).format(
            metric=self.metric,
            namespace=self.namespace,
            measuring_point=self.measuring_point,
            stage=self.stage,
            interval=self.interval
        )
        
        params = {
            "query": query,
            "start": start_ts,
            "end": end_ts,
            "time": today_time,
            "step": step
        }
        
        response = requests.get(
            self.url,
            params = params
        )
        
        reads = response.json()
        data = []
        for i in reads['data']['result']:
            data.extend(i['values'])

        df = pd.DataFrame(data, columns=['ts', 'value'])
        df['value'] = df['value'].astype(float)
        df['ts'] = df['ts'].apply(lambda x: pd.to_datetime(x, unit='s'))
        
        return df
