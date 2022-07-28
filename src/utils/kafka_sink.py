import os
import sys
import yaml
import json

from confluent_kafka import Producer, KafkaError

from pb.spug_kafka_format import Timestamp, Sample, Samples


get_forecast_config = os.environ.get('GET_FORECAST_CONFIG', '/apps/config/settings.yaml')
with open(get_forecast_config) as f:
    settings = yaml.safe_load(f)


def acked(err, msg):
    if err is not None:
        print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
    else:
        pass


def publish_messages(df, kafka_topic, metric_name, tags, callback=acked):
    p = Producer(settings.get('kafka'))

    try:
        data = pack_message(df, metric_name, tags)
        p.produce(
            kafka_topic,
            data
        )
    finally:
        p.flush()


def pack_message(df, metric_name, tags):
    '''
    df: 
                    y
        ds
        1654528132  12345

    '''

    # df1 = df.reset_index().rename(columns={'index': 'ts'})

    s_list = Samples()
    for ts, y in df.iterrows():
        s = Sample()
        s.Name = metric_name
        s.Timestamp.seconds = int(ts.timestamp())
        s.Value = float(y)

        for k, v in tags.items():
            tag = Sample.TagsEntry()
            tag.key = k
            tag.value = v
            s.Tags.append(tag)

        s_list.Samples.append(s)
        
    return s_list.encode_to_bytes()
