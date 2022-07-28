import os
# supress tensorflow warning
os. environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from dateutil import tz
import time
import pickle
import yaml
import json
import requests
import zipfile
import io

from datetime import datetime
import pandas as pd
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType


from forecaster import AutomatedForecasting
from forecaster.utils.preprocessor import Preprocessor

from utils.octopus_loader import OctopusLoader
from utils.azure_blob import AzureBlob
from utils import kafka_sink
from utils.logger import get_logger

dt_str = datetime.now().isoformat()
log_file = '/tmp/predict-{}.log'.format(dt_str)
logger = get_logger('predict', log_file=log_file)

def predict(metric, mlflow_client, predict_time=None, test_mode=False):

    logger.info('predict for {}'.format(
        metric.get('metric'))
    )

    ### Load data
    loader = OctopusLoader(
            metric.get('namespace'),
            metric.get('measuring_point'),
            metric.get('metric'),
            metric.get('interval'),
            metric.get('url')
    )

    ### Load data
    if predict_time is None:
        predict_time = time.time()

    if test_mode is True:
        # use 2022-01-01 as the testing date
        dt = pd.to_datetime(int(predict_time))
        end_ts = pd.to_datetime('2022-01-01 '+dt.strftime('%H:%M:%S')).timestamp()
    else:
        # round to the closest data point before current_time
        end_ts = (predict_time // metric['interval']) * metric['interval']

    start_ts = end_ts - metric.get('predict_history_in_days')*24*60*60

    logger.info('train start ts: {} ({}) '.format(start_ts, pd.to_datetime(start_ts, unit='s')))
    logger.info('train end ts: {} ({})'.format(end_ts, pd.to_datetime(end_ts, unit='s')))

    df = loader.get(
        start_ts,
        end_ts,
        time.time(),
        metric['interval'],
        test_mode=test_mode
    ).sort_values('ts').set_index('ts')
    logger.info("load {} points from Chronos".format(len(df)))

    ### Load a model and predict
    logger.info('search model from experiment {}'.format(metric.get('experiment_name')))
    exp = mlflow_client.get_experiment_by_name(name=metric.get('experiment_name'))
    if exp:
        exp_id = exp.experiment_id
        logger.info('found experiment with id {}'.format(exp_id))

        runs = mlflow_client.search_runs(
            experiment_ids=exp_id,
            filter_string="",
            run_view_type=ViewType.ACTIVE_ONLY,
            max_results=1,
            order_by=["metrics.accuracy DESC"]
        )

        model = None
        counter = 1
        # get latest Run
        for run in runs:
            try:
                model = mlflow.sklearn.load_model(
                    os.path.join(run.info.artifact_uri, 'model')
                )
                logger.info('load model from {} run {}'.format(counter, run.info.run_id))
                if 'pp' in model and 'engine' in model:
                    logger.info('use model from {} run {}'.format(counter, run.info.run_id))
                    break
            except Exception as e:
                logger.exception(e)

        if model:
            df_pp = model['pp'].transform(df)
            df_predict = model['engine'].predict(df_pp)
            logger.info('prediction completed')
            return df_predict
        else:
            return None


def write_to_blob(container_url, container_name, sas_token, blob_key, data):
    try:
        ab = AzureBlob(container_url, container_name, sas_token)
        ab.upload_to_blob(blob_key, data)
    except Exception as e:
        print('Error while uploading log files')
        print(e)


if __name__ == "__main__":

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
    dt_str = dt_sg.isoformat()
    logger.info('predict time: "{}"'.format(dt_str))

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

    for metric in metrics:
        df_predict = predict(
            metric,
            mlflow_client,
            predict_time=predict_time,
            test_mode=test_mode
        )
        logger.info(df_predict)

        if df_predict is not None:
            if settings.get('write_to_kafka') is True:
                summary = kafka_sink.publish_messages(
                    df_predict,
                    settings.get('kafka_sink_topic'),
                    metric.get('metric'),
                    metric['tags']
                )
                logger.info('write {} messages to kafka'.format(len(df_predict)))

            if sas_token:
                blob_key = os.path.join(
                    settings['blob_prefix'],
                    'predict',
                    'year={}'.format(dt_sg.year),
                    'month={}'.format(dt_sg.month),
                    'day={}'.format(dt_sg.day),
                    'metric={}'.format(metric['metric']),
                    '{}.parquet'.format(
                        int(time.time())
                    ),
                )

                df_predict['predict_time'] = dt_str
                table = pa.Table.from_pandas(df_predict)
                buf = pa.BufferOutputStream()
                _ = pq.write_table(table, buf)

                _ = write_to_blob(
                    settings['blob_container_url'],
                    settings['blob_container_name'],
                    sas_token,
                    blob_key,
                    buf.getvalue().to_pybytes()
                )


    for h in logger.handlers:
        h.close()

    # upload log to blob
    if sas_token:
        try:
            blob_key = os.path.join(
                settings['blob_prefix'],
                'logs',
                'predict',
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
