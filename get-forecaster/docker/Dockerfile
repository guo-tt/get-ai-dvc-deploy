from python:3.9

RUN pip install \
    adtk==0.6.2
    beautifulsoup4==4.11.1 \
    hyperopt==0.2.7 \
    imbalanced-learn==0.9.0 \
    keras==2.8.0 \
    lightgbm==3.3.2 \
    matplotlib==3.5.1 \
    mlflow==1.25.1 \
    numpy==1.21.6 \
    optuna==2.10.0 \
    pandas==1.4.2 \
    pyarrow==7.0.0 \
    python-dateutil==2.8.2 \
    PyYAML==21.10.1 \
    scikit-learn==1.0.2 \
    scipy==1.8.0 \
    scikit-optimize==0.9.0 \
    seaborn==0.11.2 \
    statsmodels==0.13.2 \
    SQLAlchemy==1.4.35 \
    tensorflow==2.8.0 \
    tensorboard==2.8.0 \
    tqdm==4.64.0 \
    tslearn==0.5.2 \
    xgboost==1.6.0 \
    yellowbrick==1.4 \

RUN pip install \
    convertdate==2.4.0 \
    cython==0.29.28 \
    holidays==0.13 \
    lunarcalendar==0.0.9 \
    pystan==2.19.1.1

RUN pip install prophet==1.0.1

RUN pip install jupyter==1.0.0
WORKDIR /srv
CMD ["jupyter", "notebook", "--allow-root", "--ip='*'", "--NotebookApp.token=''", "--NotebookApp.password=''"]
