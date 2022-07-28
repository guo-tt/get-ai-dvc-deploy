import time
import pandas as pd


from confluent_kafka import Consumer, KafkaError


from utils import kafka_sink


MIN_COMMIT_COUNT = 1

def consume_loop(consumer, topics):
    try:
        consumer.subscribe(topics)

        msg_count = 0
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                     (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                print(msg.value())
                msg_count += 1
                # if msg_count % MIN_COMMIT_COUNT == 0:
                #    consumer.commit(asynchronous=False)
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()


df = pd.DataFrame({
    'ts': [1, 2, 3],
    'value': [10, 20, 230]
})

kafka_topic = 'get-forecaster'
metric_name = 'test_metric'
tags = {'namespace': 'test', 'measurement_point':'test'}

kafka_sink.publish_messages(df, kafka_topic, metric_name, tags)

conf = {'bootstrap.servers': 'kafka:9092',
        'group.id': "foo",
        'enable.auto.commit': False,
        'auto.offset.reset': 'earliest'}

consumer = Consumer(conf)

consume_loop(consumer, [kafka_topic])
