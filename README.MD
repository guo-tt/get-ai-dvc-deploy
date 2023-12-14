# Development
0. docker network create conflent

1. make build (to build a docker image)

2. make zk (start local zookeeper)

3. make kafka (start the kafka instance)

```
# Create a topic
kafka-topics --create --topic get-forecaster --zookeeper zookeeper:2181 --partitions 5 --replication-factor 1
#kafka-topics --create --topic get_forecast --partitions 5 --replication-factor 1 --bootstrap-server localhost:9092

# Create a topic
kafka-topics --list --zookeeper zookeeper:2181
#kafka-topics --list --bootstrap-server localhost:9092 

```

4. create a `src/secret` folder and a file named sas_dev.json with the following info
```
{
    "sas_token": "......"
}
```

5. make run (start test/dev instance)
```
python train.py (train a model)
python predict.py (prediction)
python drift_detector.py (monitor drift between predict input data and training data)
python -m tools.check_kakka_sin (view kafka data)
```


