import os
import requests
import json
import datetime as dt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_SERVER = 'smtp.gmail.com'
MY_EMAIL = os.environ.get('MY_EMAIL')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"
ALPHA_API_KEY = os.environ.get('ALPHA_API_KEY')
ALPHA_API_CALL = 'https://www.alphavantage.co/query'

NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
NEWS_API_CALL = 'https://newsapi.org/v2/everything'

YESTERDAY = (dt.datetime.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")

## STEP 1: Use https://www.alphavantage.co
# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday then print("Get News").
alpha_params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": ALPHA_API_KEY,
    "datatype": 'json'
}

news_params = {
    "q": COMPANY_NAME,
    "from": YESTERDAY,
    "sortBy": 'popularity',
    "apiKey": NEWS_API_KEY
}

def get_api_data(api_key:str, params:dict) -> json:
    response = requests.get(api_key, params=params)
    response.raise_for_status()
    data = response.json()
    return data

def get_close_delta(day_one, day_before) -> int:
    formatted_day_one = day_one.strftime("%Y-%m-%d")
    formatted_day_before = day_before.strftime("%Y-%m-%d")
    
    day_one_close = float(alpha_data["Time Series (Daily)"][formatted_day_one]["4. close"])
    day_before_close = float(alpha_data["Time Series (Daily)"][formatted_day_before]["4. close"])
    
    delta = round(100*(day_one_close - day_before_close)/day_before_close,2)
    return delta

alpha_data = get_api_data(api_key=ALPHA_API_CALL, params=alpha_params)

weekday = dt.datetime.today().weekday()
if weekday == 0:
    friday = dt.datetime.today() - dt.timedelta(days=3)
    day_before = friday - dt.timedelta(days=1)
    
    delta = get_close_delta(day_one=friday, day_before=day_before)
else:
    yesterday = dt.datetime.today() - dt.timedelta(days=1)
    day_before = yesterday - dt.timedelta(days=1)

    delta = get_close_delta(day_one=yesterday, day_before=day_before)

## STEP 2: Use https://newsapi.org
# Instead of printing ("Get News"), actually get the first 3 news pieces for the COMPANY_NAME. 
if abs(delta) > 1: # Change to 5
    if delta > 0:
        message_beginning = f'{STOCK}: 🔼{delta}%\n'
    else:
        message_beginning = f'{STOCK}: 🔻{delta}%\n'

    data = get_api_data(api_key=NEWS_API_CALL, params=news_params)

    data_length = len(data['articles'])
    if data_length > 3:
        data_scope = data['articles'][0:3]
    else:
        data_scope = data['articles'][0:data_length]
        
    ## STEP 3: Use SMTPlib
    # Send a seperate message with the percentage change and each article's title and description to your e-mail. 

    message = f'{message_beginning}'
    for article in data_scope:
        headline = 'Headline: ' + article['title'] + '\n'
        brief = 'Brief: ' + article['description'] + '\n'
        link_to_news = 'URL: ' + article['url'] + '\n\n'
        message += headline + brief + link_to_news
    
    subject = f"CHECK OUT THIS STOCK: {message_beginning}!!!"
    body = message
    
    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = MY_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER)
        server.starttls()
        server.login(MY_EMAIL, EMAIL_PASSWORD)
        
        server.sendmail(MY_EMAIL, MY_EMAIL, msg.as_string())
        print("E-mail sent successfuly")
    except Exception as e:
        print(f"Error sending e-mail: {e}")
