import configparser
import ccxt
from os import path
import logging as log
from supertrend import Supertrend
import time

class Bot():

    def __init__(self):
        config_parser = configparser.ConfigParser()
        settings_path = path.abspath("settings.conf")
        config_parser.read(settings_path)

        workers = []

        for config_section in config_parser.sections():

            if not (config_section in ccxt.exchanges):
                continue
            
            #1st worker param
            config = config_parser[config_section]

            exchange_cls = getattr(ccxt, config_section)
            #2nd worker param
            exchange = exchange_cls({
                'apiKey': config['apikey'],
                'secret': config['apisecret']
            })
          
            #3rd worker param (each item)
            markets = []
            for market in exchange.loadMarkets():
                traded_currencies = config['tradedcurrencies'].split(',')
                currency = market.split('/')[0]
                if(market.endswith('/'+ config['currency']) and currency in traded_currencies):
                    markets.append(market)

            #4th worker param (each item)
            tickers = []
            if (exchange.has['fetchTickers']):
                tickers = exchange.fetch_tickers(markets)
            else:
                for market in markets:
                    ticker = exchange.fetch_ticker(market)
                    tickers.append(ticker)

            #5th worker param (each item)
            balance = exchange.fetch_balance()
            free_balance = balance[config['currency']]['free']
            size = (free_balance *  max(1, float(config['valueatrisk']))) / len(markets)

            for market in markets:
                ticker = tickers[market]['info']['lastPrice']
                workers.append(Supertrend(config_section, config, exchange, market, size))

        
        self.workers = workers

    def run(self):
        for worker in self.workers:
            worker.start()
            time.sleep(5)

Bot().run()