import os
import sys
import yaml
import json
import pandas as pd

from confluent_kafka import Consumer, KafkaError

from pb.spug_kafka_format import Timestamp, Sample, Samples

get_forecast_config = os.environ.get('GET_FORECAST_CONFIG', '/apps/config/settings.yaml')
with open(get_forecast_config) as f:
    settings = yaml.safe_load(f)

kafka_conf = settings.get('kafka')
# kafka_conf.pop('debug')
kafka_conf['group.id'] = 'verify-sink'

c = Consumer(kafka_conf)
c.subscribe([settings.get('kafka_sink_topic')])

data = []

try:
    while True:
        msg = c.poll(1)
        if msg is None:
            continue
        elif not msg.error():
            try:
                v = msg.value()
                if v:
                    s_list = Samples()
                    s_list.parse_from_bytes(v)
                    for i in s_list.Samples:
                        print("{} ({}): {}".format(
                            i.Timestamp.seconds,
                            pd.to_datetime(i.Timestamp.seconds, unit='s'),
                            i.Value
                        ))
                        print({j.key: j.value for j in i.Tags})
            except Exception as e:
                print(e)
        elif msg.error().code() == KafkaError._PARTITION_EOF:
            print('End of partition reached {0}/{1}'
                  .format(msg.topic(), msg.partition()))
        else:
            print('Error occured: {0}'.format(msg.error().str()))

except KeyboardInterrupt:
    pass

finally:
    c.close()
