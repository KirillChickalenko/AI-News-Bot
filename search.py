# -*- coding: utf-8 -*-
import requests
import time
import hashlib
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

API_KEY = "API КЛЮЧ ДЛЯ NEWS API"
DOMAINS = (
    "pravda.com.ua,unian.net,zn.ua,tsn.ua,rian.com.ua,"
    "rbc.ua,061.ua,suspilne.media,24tv.ua,"
    "babel.ua,hromadske.ua,glavcom.ua,focus.ua"
)
CHECK_INTERVAL = 1200
NEWS_FILE = "news.txt"
AI_INPUT_FILE = "ai_input.json"

def get_news_id(article):
    unique_str = article['title'] + article['publishedAt']
    return hashlib.md5(unique_str.encode('utf-8')).hexdigest()

def load_seen_news():
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def save_seen_news(seen_news):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        for news_id in seen_news:
            f.write(f"{news_id}\n")

def load_ai_input():
    try:
        with open(AI_INPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_ai_input(articles):
    with open(AI_INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

def extract_full_text(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        domain = requests.utils.urlparse(url).netloc

        selectors = [
            "div.post_text", "div.article-text", "div.blog-post-body",
            "div.article-body", "article", "div[itemprop='articleBody']",
            "div.entry-content", "div.text", "div.news-text"
        ]

        for sel in selectors:
            container = soup.select_one(sel)
            if container:
                text = container.get_text(separator='\n', strip=True)
                if len(text) > 100:
                    return text

        return "Текст не знайдено або надто короткий."

    except Exception as e:
        print(f"[!] Не вдалося отримати текст з {url}: {e}")
        return "Не вдалося отримати повний текст."

def check_news():
    print("Перевірка новин розпочата...")
    seen_news = load_seen_news()
    new_articles = []
    existing_ai_articles = load_ai_input()
    existing_urls = {a['url'] for a in existing_ai_articles}

    date_from = (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%dT%H:%M:%S')

    query = ("Запоріжжя OR Запорожье OR Zaporizhzhia OR Зеленський OR Зеленский OR Україна OR Украина")

    params = {
        "q": query,
        "domains": DOMAINS,
        "from": date_from,
        "sortBy": "publishedAt",
        "language": "uk",
        "pageSize": 100,
        "apiKey": API_KEY,
    }

    try:
        response = requests.get("https://newsapi.org/v2/everything", params=params)
        response.raise_for_status()
        data = response.json()

        if data['status'] == 'ok' and data['totalResults'] > 0:
            keywords = [
                'запоріжжя', 'запорожье', 'zaporizhzhia',
                'запорізька область', 'запорожская область',
                'запорізький', 'запорожский', 'зеленський', 'зеленский',
                'володимир зеленський', 'владимир зеленский',
                'президент україни', 'президент украины',
                'україна', 'украина', 'фронт',
                'запорізький фронт', 'запорожский фронт',
                'напрямок', 'направление',
                'запорізький напрямок', 'запорожское направление',
                'обстріл', 'обстрел', 'атака', 'штурм',
                'бойові дії', 'боевые действия', 'лінія фронту', 'линия фронта'
            ]

            for article in data['articles']:
                news_id = get_news_id(article)
                if news_id in seen_news:
                    continue

                title = article['title'].lower()
                description = (article.get('description') or '').lower()
                content = (article.get('content') or '').lower()

                if any(k in title or k in description or k in content for k in keywords):
                    if article['url'] in existing_urls:
                        continue

                    print(f"\nНова новина: {article['title']}")
                    print(f"Джерело: {article.get('source', {}).get('name', '')} | {article['url']}")

                    full_text = extract_full_text(article['url'])

                    new_article = {
                        'title': article['title'],
                        'url': article['url'],
                        'content': full_text,
                        'source': article.get('source', {}).get('name', '')
                    }

                    new_articles.append(new_article)
                    seen_news.add(news_id)
                    existing_urls.add(article['url'])

            if new_articles:
                save_seen_news(seen_news)
                all_ai_articles = existing_ai_articles + new_articles
                save_ai_input(all_ai_articles)
        else:
            print("Новин не знайдено.")

    except requests.RequestException as e:
        print(f"Помилка запиту: {e}")

    print("Перевірка завершена.\n")
    return new_articles

if __name__ == "__main__":
    while True:
        check_news()
        time.sleep(CHECK_INTERVAL)
