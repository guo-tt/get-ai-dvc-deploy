import os
from datetime import datetime
from dateutil import tz
import time
import yaml
import json

import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
import mlflow.sklearn

from forecaster import AutomatedForecasting
from forecaster.utils.preprocessor import Preprocessor

from utils.octopus_loader import OctopusLoader
from utils.azure_blob import AzureBlob
from utils.logger import get_logger

dt_str = datetime.now().isoformat()
log_file = '/tmp/train-{}.log'.format(dt_str)
logger = get_logger('train', log_file=log_file)


def train(metric, mlflow_client, train_time=None, test_mode=False):
    loader = OctopusLoader(
            metric.get('namespace'),
            metric.get('measuring_point'),
            metric.get('metric'),
            metric.get('interval'),
            metric.get('url')
    )

    ### Load data
    if train_time is None:
        train_time = time.time()

    if test_mode is True:
        # use 2022-01-01 as the testing date
        dt = pd.to_datetime(int(train_time))
        end_ts = pd.to_datetime('2022-01-01 '+dt.strftime('%H:%M:%S')).timestamp()
    else:
        # round to the closest data point before current_time
        end_ts = (train_time // metric['interval']) * metric['interval']

    start_ts = end_ts - metric.get('train_history_in_days')*24*60*60

    logger.info('Train start ts: {} ({}) '.format(start_ts, pd.to_datetime(start_ts, unit='s')))
    logger.info('Train end ts: {} ({})'.format(end_ts, pd.to_datetime(end_ts, unit='s')))

    df = loader.get(
        start_ts,
        end_ts,
        time.time(),
        metric['interval'],
        test_mode=test_mode
    ).sort_values('ts').set_index('ts')
    logger.info("Load {} points from Chronos".format(len(df)))

    ### Train a model
    marker = time.time()
    pp = Preprocessor(remove_outlier=True)
    df_pp = pp.fit(df).transform(df)

    engine = AutomatedForecasting(models=['Linear',], test_size=0.04)
    engine.fit(df_pp).predict(df_pp)
    logger.info("Model trained in {:.1f} seconds".format(time.time()-marker))

    ### Save a model
    exp_name = metric.get('experiment_name')

    exp = mlflow_client.get_experiment_by_name(name=exp_name)
    if exp is None:
        logger.info('Create a new experiment "{}"'.format(exp_name))
        artifact_location = os.path.join(
            metric.get('artifact_location'),
            metric.get('experiment_name')
        )
        exp_id = mlflow_client.create_experiment(
            name=exp_name,
            artifact_location=artifact_location,
            tags={'get-forecast': exp_name}
        )
    else:
        logger.info('Find experiment "{}"'.format(exp_name))
        exp_id = exp.experiment_id
    logger.info('Set experiment_id to {}'.format(exp_id))


    with mlflow.start_run(experiment_id = exp_id):
        model = {
            'engine': engine,
            'pp': pp,
        }

        mlflow.log_param("name", engine.best_model.name)
        mlflow.log_param("alpha", engine.best_model.alpha)
        mlflow.log_param("cyclic_feature_encoding", engine.best_model.cyclic_feature_encoding)
        mlflow.log_metric("train_start_ts", start_ts)
        mlflow.log_metric("train_end_ts", end_ts)
        mlflow.sklearn.log_model(model, "model", registered_model_name=exp_name)
        logger.info("Model saved")
    return True

if __name__ == "__main__":
    metric_config_file = os.environ.get('METRIC_CONFIG', '/apps/metrics/metrics.yaml')
    with open(metric_config_file) as f:
        metrics = yaml.safe_load(f)
        logger.info(metrics)

    get_forecast_config = os.environ.get('GET_FORECAST_CONFIG', '/apps/config/settings.yaml')
    with open(get_forecast_config) as f:
        settings = yaml.safe_load(f)
        logger.info(settings)

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

    mlflow.set_tracking_uri(settings.get('mlflow_tracking_uri'))
    mlflow_client = MlflowClient()

    test_mode = settings.get('test_mode', False)
    train_time = os.environ.get('train_time', None)

    if train_time is None:
        dt = datetime.now()
    else:
        train_time = int(train_time)
        dt = datetime.utcfromtimestamp(train_time)

    dt_sg = dt.astimezone(tz.gettz('Asia/Singapore'))
    dt_str = dt_sg.isoformat()
    logger.info('train time: "{}"'.format(dt_str))

    try:
        for metric in metrics:
            _ = train(metric, mlflow_client, train_time=train_time, test_mode=test_mode)
    except Exception as e:
        logger.exception(e)


    for h in logger.handlers:
        h.close()

    # upload log to blob
    if sas_token:
        try:
            ab = AzureBlob(settings['blob_container_url'], settings['blob_container_name'], sas_token)
            blob_key = os.path.join(
                settings['blob_prefix'],
                'logs',
                'train',
                'year={}'.format(dt_sg.year),
                'month={}'.format(dt_sg.month),
                'day={}'.format(dt_sg.day),
                os.path.basename(log_file)
            )

            with open(log_file, 'r') as f:
                ab.upload_to_blob(blob_key, f.read())
        except Exception as e:
            print('Error while uploading log files')
            print(e)
