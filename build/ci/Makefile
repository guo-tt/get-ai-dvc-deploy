.PHONY: build push k8config deploy

build: docker-release-image-build
push: docker-login docker-push

k8config: k8s-kube-config
deploy: k8s-configmap k8s-setup-secrets k8s-secret k8s-pvc k8s-deploy k8s-cronjobs k8s-ingress


# targets
docker-release-image-build:
	docker build \
	    -t $(DOCKER_TAG) \
		--build-arg http_proxy="$(http_proxy)" \
		--build-arg https_proxy="$(https_proxy)" \
		--build-arg no_proxy="$(no_proxy)" \
		-f ./build/ci/Dockerfile.release \
	    .

docker-login:
	docker login $(DOCKER_REGISTRY) -u $(DOCKER_LOGIN_USR) -p $(DOCKER_LOGIN_PSW)

docker-push:
	docker push $(DOCKER_TAG)


### Kubernetes ###
kubectl_cmd = /usr/local/bin/kubectl-1.13.5 --namespace=$(KUBE_NAMESPACE) --request-timeout='2m'
k8s_yaml_path := build/k8s

fetch-py-modules:
	git clone https://code.in.spdigital.sg/SP-Data-Cloud/get-forecaster

fetchkey:
	mkdir -p ./secret/
	vault kv get -format json -field 'data' -tls-skip-verify ${VAULT_SAS_PATH}/${VAULT_SAS_FILE} > ./secret/sas_$(KUBE_ENV).json
	vault kv get -format json -field 'data' -tls-skip-verify ${VAULT_AIE_PATH}/mlflow_azureblob.json > ./secret/mlflow_azureblob.json
	vault kv get -format json -field 'data' -tls-skip-verify ${VAULT_AIE_PATH}/mlflow_backend_uri.json > ./secret/mlflow_backend_uri.json
	ls -l ./secret/
	jq -s '.[0] * .[1]' ./secret/mlflow_azureblob.json ./secret/mlflow_backend_uri.json > ./secret/mlflow.json
	jq -r 'to_entries|map("\(.key)=\(.value|tostring)")|.[]' ./secret/mlflow.json > ./secret/mlflow_env.json
	cat ./secret/mlflow_env.json
	vault write $(KAFKA_CA) common_name=$(KAFKA_CONSUMER_NAME) --format=json > ./secret/tmp
	jq -r ".data.certificate" < ./secret/tmp > ./secret/cert.pem
	jq -r ".data.issuing_ca" < ./secret/tmp > ./secret/ca.pem
	jq -r ".data.private_key" < ./secret/tmp > ./secret/key.pem
	curl -s -k -o ./secret/rootca.pem 'https://vault.in.spdigital.sg/v1/pki-ca-root/ca/pem'
	cat ./secret/rootca.pem >> ./secret/ca.pem
	head -5 ./secret/cert.pem
	head -5 ./secret/rootca.pem

k8s-setup-secrets:
	mkdir -p ./config/
	vault kv get -format json -field 'data' -tls-skip-verify ${VAULT_AIE_PATH}/config.json > ./config/config_$(KUBE_ENV).json

k8s-kube-config:
	mkdir -p ${HOME}/.kube
	vault kv get -field=config -format json -tls-skip-verify $(VAULT_K8CONFIG_PATH) > $(HOME)/.kube/config

k8s-secret:
	#    $(kubectl_cmd) create secret generic test-secret --from-file=./config/TEST.json --dry-run -o yaml | $(kubectl_cmd) apply -f -
	$(kubectl_cmd) create secret generic $(KUBE_SECRET) \
	    --from-file=./secret/sas_$(KUBE_ENV).json \
	    --from-file=./secret/key.pem \
	    --from-file=./secret/cert.pem \
	    --from-file=./secret/ca.pem \
	    --dry-run -o yaml | $(kubectl_cmd) apply -f -
	$(kubectl_cmd) create secret generic mlflow \
	    --from-env-file=./secret/mlflow_env.json \
	    --dry-run -o yaml | $(kubectl_cmd) apply -f -
	#

k8s-pvc:
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-mlflow-pvc.yml

k8s-configmap:
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-configmap.yml
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-metrics.yml

k8s-deploy:
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-deploy.yml

k8s-cronjobs:
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-train-cronjob.yml
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-prediction-cronjob.yml

k8s-ingress:
	$(kubectl_cmd) apply -f $(k8s_yaml_path)/$(KUBE_ENV)/get-ai-ingress.yml

debug:
	$(kubectl_cmd) get pods
