# **Time Series Forecasting**

---

This project aims to:

* Develop a time series forecasting package which streamlines the lifecycle of time series forecasting tasks

* Integrate time series forecasting capability into GET plafform

---

## User Guide
Python version: 3.7.6

To install all packages used:
```
pip3 install -r requirements.txt
```

### Importing the modules
```
from utils.preprocessor import Preprocessor
from forecaster import AutomatedForecasting
```

### Preprocessor
* Converts univariate time series dataframe into a time series dataframe of the specified frequency
* Input: pandas.DataFrame indexed by DateTime (row: datetime, col: observations)
* `fit(X)`: Finds the median profile and outlier profile of X
* `transform(X)`: Processes the dataframe and removes outliers using fitted median profile and outlier profile
* Output: pandas.DataFrame indexed by DateTime (row: datetime, col: observations)
```
pp = Preprocessor(resample_freq='30min', remove_outlier=True)
df_pp = pp.fit(df).transform(df)
```
Parameters:
* `resample_freq`: Resample freqency of time series. `str, default='30min'`
* `remove_outlier`: If True, outliers will be removed. `bool, default=True`



### AutomatedForecasting
* Conducts Automated Forecasting which finds the best combination of model and hyperparameters.
* Input: pandas.DataFrame from Preprocessor
* `fit(X)`: Conducts model and hyperparameter search
```
engine = AutomatedForecasting(freq='30min', horizon='1d', models=['Linear'], iteration=50, method='bayesian', early_stopping_steps=10)
engine.fit(df_pp)
```
Parameters:
* `freq`: Frequency of time series. `str, default='30min'`
* `horizon`: Forecast horizon. `str, default='1d'`
* `models`: Models included in the search space. `list`
* `iteration`: Number of iterations for the search. `int, default=50`
* `method`: Hyperparameter search method. `{'bayesian', 'randomized_search'}, default='bayesian'`
* `early_stopping_steps`: Number of trials with no improvement in best loss before bayesian optimization stops. `int, default=10`

Attributes:
* `best_model`: Model with the best perfomance and fitted with the input time series



### Workflow
#### 1. Fit preprocessor with training data and Transform training data
The preprocessor is initiated and fitted with past 6 months data as training data. The data is then transformed. In this step, the data is resampled to the specified resampling frequency and outliers are removed. 
```
pp = Preprocessor(resample_freq='30min', remove_outlier=True)
df_train_pp = pp.fit(df_train).transform(df_train)
```

#### 2. Train model with preprocessed training data
Using the automated forecaster, hyperparameter tuning is conducted and the best model is fitted with the training data.
```
from forecaster import AutomatedForecasting
engine = AutomatedForecasting(freq='30min', horizon='1d', models=['Linear'], iteration=50, method='bayesian', early_stopping_steps=10)
engine.fit(df_train_pp)
```

#### 3. Preprocess new data
New data consisting of 7 days of data is transformed using the fitted preprocessor from step 1.
```
df_new_pp = pp.transform(df_new)
```

#### 4. Produce forecast using preprocessed new data
The fitted `engine` takes the processed new data as input and returns the forecast values for the forecast horizon `horizon` and frequency `freq` specified in step 2.
```
df_fcst = engine.predict(df_new_pp)
```

#### 5. Obtain top 5 features
The best model is retrieved from the automated forecaster as an attribute via `engine.best_model`. The top 5 features can be obtained from the best model as an array of feature names.
```
best_model = engine.best_model
best_model.best_features
```

## Feature Description
The following description assumes 7 days in the look back cycle.
* `lag n`: lag features over past 7 days based on time series frequency 
* `median_look_back`: median in past 7 days 
* `std_look_back`: standard deviation in past 7 days 
* `ratio_i_j`: ratio in past 7 days, where 1d <= i <= 6d, 2d <= j <= 7d, i < j
* `lag_n_ratio_i`: lag n and lag n+1 ratio, shifted by i days
* `median_lag_n_ratio`: median of lag n and lag n+1 ratio in past 7 days
* `std_lag_n_ratio`: standard deviation of lag n and lag n+1 ratio in past 7 days
* `lag_n_ratio_of_ratio_i_j`: lag n ratio of ratio in past 7 days, where 1d <= i <= 6d, 2d <= j <= 7d, i < j
* `weekend_false`: weekday feature
* `weekend_true`: weekend feature

Only applicable for onehot cyclic feature encoding:
* `hour_i`: hour feature, where 1 <= i <= 24
* `day_i_of week`: day of week feature, where 1 <= i <= 7

Only applicable for sincos cyclic feature encoding:
* `sin_hour`: sine of hour features
* `cos_hour`: cosine of hour features
* `sin_day_of_week`: sine of day of week features
* `cos_day_of_week`: cosine of day of week features
