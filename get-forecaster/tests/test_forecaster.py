import argparse
import pandas as pd

from forecaster import AutomatedForecasting
from utils.preprocessor import Preprocessor

df_raw_scm = pd.read_csv('../data/scm_july16_feb20.csv', parse_dates=True, index_col='timestamp')
df_scm = df_raw_scm.loc['2019-07':'2019-08'].copy()
pp = Preprocessor(remove_outlier=True)
df_scm_pp = pp.fit(df_scm).transform(df_scm)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Automated Forecasting')
    parser.add_argument('-l', '--list', nargs='+', help='Default Models', required=True)
    args = parser.parse_args()
    engine = AutomatedForecasting(models=args.list, test_size=0.04)
    print(engine.fit(df_scm_pp).predict(df_scm_pp))



