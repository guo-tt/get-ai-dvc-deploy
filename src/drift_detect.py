import json, os
import pandas as pd

from evidently.model_profile import Profile
from evidently.model_profile.sections import DataDriftProfileSection
from evidently.pipeline.column_mapping import ColumnMapping

import yaml 
from datetime import datetime
import time
from dateutil import tz

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType

from utils.octopus_loader import OctopusLoader
from utils.logger import get_logger
from utils.azure_blob import AzureBlob

dt_str = datetime.now().isoformat()
log_file = '/tmp/data-drift-{}.log'.format(dt_str)
logger = get_logger('drift', log_file=log_file)


def write_to_blob(container_url, container_name, sas_token, blob_key, data):
    try:
        ab = AzureBlob(container_url, container_name, sas_token)
        ab.upload_to_blob(blob_key, data)
    except Exception as e:
        print('Error while uploading log files')
        print(e)

#evaluate data drift with Evidently Profile
def eval_drift(reference, production, column_mapping):
    data_drift_profile = Profile(sections=[DataDriftProfileSection()])
    data_drift_profile.calculate(reference, production, column_mapping=column_mapping)
    report = data_drift_profile.json()
    json_report = json.loads(report)

    drifts = []

    for feature in column_mapping.numerical_features + column_mapping.categorical_features:
        drifts.append((feature, json_report['data_drift']['data']['metrics'][feature]['drift_score']))

    return drifts


def get_predict_df(predict_time, loader, metric, test_mode):

    if predict_time is None:
        predict_time = time.time()

    ### Load predict data
    if test_mode is True:
        # use 2022-01-01 as the testing date
        dt = pd.to_datetime(int(predict_time))
        predict_end_ts = pd.to_datetime('2022-01-01 ' + dt.strftime('%H:%M:%S')).timestamp()
    else:
        # round to the closest data point before current_time
        predict_end_ts = (predict_time // metric['interval']) * metric['interval']

    predict_start_ts = predict_end_ts - metric.get('predict_history_in_days')*24*60*60

    logger.info('predict start ts: {} ({}) '.format(predict_start_ts, pd.to_datetime(predict_start_ts, unit='s')))
    logger.info('predict end ts: {} ({})'.format(predict_end_ts, pd.to_datetime(predict_end_ts, unit='s')))

    predict_df = loader.get(predict_start_ts, predict_end_ts, time.time(), metric['interval'], test_mode=test_mode).sort_values('ts').set_index('ts')

    return predict_df 


def get_reference_df(metric, loader, test_mode=False):
    
    mlflow.set_tracking_uri(settings.get('mlflow_tracking_uri'))
    mlflow_client = MlflowClient()

    exp = mlflow_client.get_experiment_by_name(name=metric.get('experiment_name'))
    
    exp_id = exp.experiment_id

    runs = mlflow_client.search_runs(
        experiment_ids=exp_id,
        filter_string="",
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=1,
        order_by=["metrics.accuracy DESC"]
    )

    reference = []

    # get latest Run
    for run in runs:
        train_end_ts = int(mlflow_client.get_metric_history(run.info.run_id, 'train_end_ts')[0].value)
        train_start_ts = int(mlflow_client.get_metric_history(run.info.run_id, 'train_start_ts')[0].value)

        logger.info('train start ts: {} ({}) '.format(train_start_ts, pd.to_datetime(train_start_ts, unit='s')))
        logger.info('train end ts: {} ({})'.format(train_end_ts, pd.to_datetime(train_end_ts, unit='s')))

        r = loader.get(
            train_start_ts,
            train_end_ts,
            time.time(),
            metric['interval'],
            test_mode=test_mode
        ).sort_values('ts').set_index('ts')

        reference.append(r)

    return reference

if __name__ == "__main__":

    detector_config_file = os.environ.get('DETECTOR_CONFIG', '/apps/config/drift_detect.yaml')
    with open(detector_config_file) as f:
        detector = yaml.safe_load(f)

    metric_config_file = os.environ.get('METRIC_CONFIG', '/apps/metrics/metrics.yaml')
    with open(metric_config_file) as f:
        metrics = yaml.safe_load(f)

    get_forecast_config = os.environ.get('GET_FORECAST_CONFIG', '/apps/config/settings.yaml')
    with open(get_forecast_config) as f:
        settings = yaml.safe_load(f)

    predict_time = os.environ.get('predict_time', None)

    if predict_time is None:
        dt = datetime.now()
    else:
        predict_time = int(predict_time)
        dt = datetime.utcfromtimestamp(predict_time)

    dt_sg = dt.astimezone(tz.gettz('Asia/Singapore'))

    drift = []

    for metric in metrics:
        d = {}

        loader = OctopusLoader(
                    metric.get('namespace'),
                    metric.get('measuring_point'),
                    metric.get('metric'),
                    metric.get('interval'),
                    metric.get('url')
            )
        test_mode = settings.get('test_mode', False)

        predict_df = get_predict_df(predict_time, loader, metric, test_mode)
        reference_dfs = get_reference_df(metric, loader, test_mode)

        #set column mapping for Evidently Profile
        data_columns = ColumnMapping()
        data_columns.numerical_features = detector['numerical_features']
        data_columns.categorical_features = []

        drift_values = []
        for reference_df in reference_dfs:
            drift_value = eval_drift(reference_df, predict_df, column_mapping=data_columns)
            drift_values.append(drift_value)

        d['metric'] = metric 
        d['drift'] = drift_values
    
    drift.append(d)
    logger.info('drift is {}'.format(drift))

    # Read SAS token
    myenv = os.getenv("KUBE_ENV", "dev")
    sas_path = "./secret/sas_" + myenv + ".json"
    sas_token = None

    if os.path.isfile(sas_path):
        try:
            with open(sas_path) as f:
                sas = json.load(f)
                for v in sas.values():
                    sas_token = v
        except Exception as e:
            logger.exception(e)

    # upload log to blob
    if sas_token:
        try:
            blob_key = os.path.join(
                settings['blob_prefix'],
                'logs',
                'drift',
                'year={}'.format(dt_sg.year),
                'month={}'.format(dt_sg.month),
                'day={}'.format(dt_sg.day),
                os.path.basename(log_file)
            )

            with open(log_file, 'r') as f:
                write_to_blob(
                    settings['blob_container_url'],
                    settings['blob_container_name'],
                    sas_token,
                    blob_key,
                    f.read()
                )
            
        except Exception as e:
            print('Error while uploading log files')
            print(e)