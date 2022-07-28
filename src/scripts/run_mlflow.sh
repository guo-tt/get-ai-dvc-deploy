mlflow server \
  --host=0.0.0.0 --port 5000 \
  --backend-store-uri="${MLFLOW_TRACKING_URI}" \
  --default-artifact-root='file:////mnt/mlflow-data/artifacts'

