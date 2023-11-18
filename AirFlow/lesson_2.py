import requests
import pandas as pd
from datetime import timedelta
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

TOP_1M_DOMAINS = 'https://storage.yandexcloud.net/kc-startda/top-1m.csv'
TOP_1M_DOMAINS_FILE = 'top-1m.csv'


def get_data():
    # Здесь пока оставили запись в файл, как передавать переменую между тасками будет в третьем уроке___
    top_doms = pd.read_csv(TOP_1M_DOMAINS)
    top_data = top_doms.to_csv(index=False)
    with open(TOP_1M_DOMAINS_FILE, 'w') as f:
        f.write(top_data)


def get_stat_zone():
    top_doms = pd.read_csv(TOP_1M_DOMAINS_FILE, names=['rank', 'domain'])
    top_doms['domain_zone'] = top_doms['domain'].str.rsplit('.', 1).str[-1]
    top_data_10 = top_doms.groupby('domain_zone').agg({'rank': 'count'}).sort_values('rank', ascending=False).reset_index()
    top_data_10 = top_data_10.head(10)
    with open('top_data_10.csv', 'w') as f:
        f.write(top_data_10.to_csv(index=False, header=False))


def get_stat_long():
    top_data_lenght = pd.read_csv(TOP_1M_DOMAINS_FILE, names=['rank', 'domain'])
    top_data_lenght['domain_lenght'] = top_data_lenght['domain'].apply(lambda x: len(str(x)))
    top_lenght_domain = top_data_lenght.sort_values(by=['domain_lenght', 'domain'], ascending=[False, True]).head(1).domain
    with open('top_lenght_domain.csv', 'w') as f:
        f.write(top_lenght_domain.to_csv(index=False, header=False))


def get_airflow_rank(): # The airflow domain's rank
    top_doms_df = pd.read_csv(TOP_1M_DOMAINS_FILE, names=['rank', 'domain'])
    try:
        airflow_rank = int(top_doms_df.loc[top_doms_df['domain'] == 'airflow.com', 'rank'])
    except:
        air_sim = (top_doms_df.loc[top_doms_df['domain'].str.startswith('airflow')][['domain', 'rank']]
                   .reset_index(drop=True))
        air_rank = f'There is no "airflow.com" but similar domains are the following:{dict(air_sim.values)}'    
    with open('airflow_rank.txt', 'w') as f:
        f.write(str(airflow_rank))



def print_data(ds):
    with open('top_data_10.csv', 'r') as f:
        all_zone = f.read()
    with open('top_lenght_domain.csv', 'r') as f:
        all_long = f.read()
    with open('airflow_rank.csv', 'r') as f:
        all_airflow = f.read()
    date = ds

    print(f'Top-10 domain zones for date {date}')
    print(all_zone)

    print(f'Longest domain name for date {date}')
    print(all_long)

    print(f'Rank of airflow.com for date {date}')
    print(all_airflow)


default_args = {
    'owner': 't.shevchenko',
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 14),
}
schedule_interval = '30 13 * * *'

dag = DAG('tshevchenko41', default_args=default_args, schedule_interval=schedule_interval)

t1 = PythonOperator(task_id='get_data',
                    python_callable=get_data,
                    dag=dag)

t2 = PythonOperator(task_id='get_stat_zone',
                    python_callable=get_stat_zone,
                    dag=dag)

t3 = PythonOperator(task_id='get_stat_long',
                         python_callable=get_stat_long,
                         dag=dag)

t4 = PythonOperator(task_id='get_airflow_rank',
                        python_callable=get_airflow_rank,
                        dag=dag)

t5 = PythonOperator(task_id='print_data',
                    python_callable=print_data,
                    dag=dag)

t1 >> [t2, t3, t4] >> t5

# t1.set_downstream(t2)
# t1.set_downstream(t2_com)
# t2.set_downstream(t3)
# t2_com.set_downstream(t3)
