PROJECT=getai
REPO=porter.azurecr.io/porter/$(PROJECT)
TAG=0.1.23

.PHONY: deploy

test:
	docker run -it --rm \
	--name $(PROJECT)-test \
	-p 9099:9099 \
	-v `pwd`/src:/apps \
	$(REPO):$(TAG) \
	bash 
	
#gunicorn -c server/gunicorn.py server.server:app

build: clean
	docker build -f build/ci/Dockerfile.release -t $(REPO):$(TAG) .

clean:
	find . \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} +

docker-push:
	docker buildx build . \
        --platform linux/arm64,linux/amd64 \
        --tag $(REPO):$(TAG) \
	--push

zk:
	docker run -d --rm \
	    --platform linux/arm64 \
	    --net=confluent \
	    --name=zookeeper \
	    -e ZOOKEEPER_CLIENT_PORT=2181 \
	    confluentinc/cp-zookeeper:7.1.2.arm64
	sleep 10

kafka:
	docker run -d --rm \
	    --net=confluent \
	    --name=kafka \
	    -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 \
	    -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092 \
	    -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
		confluentinc/cp-kafka:7.1.2@sha256:bd9fa7f54697d7e5d83b68de59384b8aa907d8bf3f6d6679e2d0a56ce17fea04

deploy:
	kubectl apply -f deploy/data-api-deploy.yaml

run:
	docker run \
	    --name get-ai \
	    --net=confluent \
	    -it \
	    --rm \
	    -v `pwd`/src:/apps \
	    -v `pwd`/data:/mnt/mlflow_data \
	    -p 5000:5000 \
	    $(REPO):$(TAG) \
	    bash
	    # mlflow server --host=0.0.0.0 --port 5000 --backend-store-uri sqlite:////home/spd/mlflow.db --default-artifact-root file:////home/spd/mlflow_artifacts
	    #jupyter notebook --allow-root --ip=0.0.0.0 --NotebookApp.token='' --NotebookApp.password=''