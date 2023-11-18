import requests
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
import numpy as np
from datetime import timedelta
from datetime import datetime
from io import StringIO
import telegram

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.models import Variable

TOP_GAMES = '/var/lib/airflow/airflow.git/dags/a.batalov/vgsales.csv'
TOP_GAMES_FILE = 'vgsales.csv'

default_args = {
    'owner': 't.shevchenko',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2023, 9, 19),
    'schedule_interval': '0 20 * * *'
}


@dag(default_args=default_args, catchup=False)
def top_games_airflow():
    @task(retries=3)
    def get_data():
        top_g = pd.read_csv(TOP_GAMES)
        top_g = top_g.query("Year == 2003")
        return top_g

    @task(retries=4, retry_delay=timedelta(10))
    def get_games_world(top_g):
        # Пункт 1. Самая продаваемая игра в 2003 году
        top_g_top_game = top_g.groupby('Name').agg({'Global_Sales': 'sum'}).sort_values('Global_Sales',
                                                                                        ascending=False).reset_index().head(
            1)  # .values[0]
        return top_g_top_game

    @task(retries=4, retry_delay=timedelta(10))
    def get_genre(top_g):
        # Пункт 2. Игры какого жанра были самыми продаваемыми в Европе? Перечислить все, если их несколько
        top_g_top_genre_EU = top_g.groupby('Genre').agg({'EU_Sales': 'sum'}).sort_values('EU_Sales',
                                                                                         ascending=False).query(
            "EU_Sales != 0").reset_index().head(1)  # .values[0]
        return top_g_top_genre_EU

    @task(retries=4, retry_delay=timedelta(10))
    def get_platform(top_g):
        # Пункт 3. На какой платформе было больше всего игр, которые продались более чем миллионным тиражом в Северной Америке? Перечислить все, если их несколько.
        top_g_top_platform_US = top_g.groupby('Platform').agg({'NA_Sales': 'sum'}).sort_values('NA_Sales',
                                                                                               ascending=False).query(
            "NA_Sales > 1").reset_index()
        return top_g_top_platform_US

    @task(retries=4, retry_delay=timedelta(10))
    def get_publisher(top_g):
        # Пункт 4. У какого издателя самые высокие средние продажи в Японии? Перечислить все, если их несколько.
        top_g_top_Publisher_JP = top_g.groupby('Publisher').agg({'JP_Sales': 'sum'}).sort_values('JP_Sales',
                                                                                                 ascending=False).query(
            "JP_Sales != 0").reset_index().head(1)
        return top_g_top_Publisher_JP

    @task(retries=4, retry_delay=timedelta(10))
    def get_eu_vs_jp(top_g):
        # Пункт 5. Сколько игр продались лучше в Европе, чем в Японии?
        top_g_top_EU_vs_JP = top_g.groupby('Name').agg({'EU_Sales': 'sum', 'JP_Sales': 'sum'}).sort_values('EU_Sales',
                                                                                                           ascending=False).query(
            "EU_Sales != 0 and JP_Sales != 0").reset_index()
        top_g_top_EU_vs_JP['EU_larg_JP'] = top_g_top_EU_vs_JP['EU_Sales'] - top_g_top_EU_vs_JP['JP_Sales']
        top_g_top_EU_vs_JP = top_g_top_EU_vs_JP.query("EU_larg_JP > 0")
        EU_vs_JP_count = top_g_top_EU_vs_JP['Name'].count()
        return EU_vs_JP_count

    @task()
    def print_data(top_g_top_game, top_g_top_genre_EU, top_g_top_platform_US, top_g_top_Publisher_JP, EU_vs_JP_count):
        top_game_name, top_game_quantity = top_g_top_game['Name'], top_g_top_game['Global_Sales']
        top_genre_name, top_genre_quantity = top_g_top_genre_EU['Genre'], top_g_top_genre_EU['EU_Sales']
        top_platform_name, top_platform_quantity = top_g_top_platform_US['Platform'], top_g_top_platform_US['NA_Sales']
        top_Publisher_name, top_Publisher_quantity = top_g_top_Publisher_JP['Publisher'], top_g_top_Publisher_JP[
            'JP_Sales']
        EU_vs_JP_c = EU_vs_JP_count

        print(f'''Top game in 2003
                  Game name: {top_game_name}
                  Game quantity: {top_game_quantity}''')

        print(f'''Top genre in 2003 in EU
                  Genre name: {top_genre_name}
                  Genre quantity: {top_genre_quantity}''')

        print(f'''Top platform in 2003 in NA
                  Genre name: {top_platform_name}
                  Genre quantity: {top_platform_quantity}''')

        print(f'''Top Publisher in 2003 in Japan
                  Publisher name: {top_Publisher_name}
                  Publisher quantity: {top_Publisher_quantity}''')

        print(f'''Games with sales in EU better than Japan in 2003
                  Quantity: {EU_vs_JP_c}''')

    top_g = get_data()
    top_g_top_game = get_games_world(top_g)
    top_g_top_genre_EU = get_genre(top_g)
    top_g_top_platform_US = get_platform(top_g)
    top_g_top_Publisher_JP = get_publisher(top_g)
    EU_vs_JP_count = get_eu_vs_jp(top_g)

    print_data(top_g_top_game, top_g_top_genre_EU, top_g_top_platform_US, top_g_top_Publisher_JP, EU_vs_JP_count)


top_games_airflow = top_games_airflow()
