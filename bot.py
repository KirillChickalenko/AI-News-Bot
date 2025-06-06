import telebot
import json
import time
import re

bot = telebot.TeleBot("HTTP API ДЛЯ БОТА")
CHANNEL_ID = "ID КАНАЛУ"
AI_OUTPUT_FILE = "ai_output.json"

def clean_processed_text(text):
    text = re.sub(r"\[Заголовок\]:\s*", "", text)
    text = re.sub(r"\[Зміст\]:\s*", "", text)
    return text.strip()

def load_articles():
    try:
        with open(AI_OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def send_message(article):
    processed_clean = clean_processed_text(article.get('processed', ''))
    message = (
        f"{processed_clean}\n\n"
        f"🔗 <a href='{article.get('url', '')}'>Читати джерело</a>\n"
        f"📢 Джерело: {article.get('source', 'Невідомо')}"
    )
    try:
        bot.send_message(CHANNEL_ID, message, parse_mode="HTML", disable_web_page_preview=False)
        print(f"Відправлено: {article.get('original', 'Новина без заголовка')}")
        return True
    except Exception as e:
        print(f"Помилка при відправці повідомлення: {e}")
        return False

def main_loop():
    sent_ids = set()

    while True:
        articles = load_articles()


        new_articles = []
        for art in articles:
            unique_id = (art.get('original', '') + art.get('url', '')).strip()
            if unique_id not in sent_ids:
                new_articles.append((unique_id, art))

        if new_articles:
            for unique_id, article in new_articles:
                if send_message(article):
                    sent_ids.add(unique_id)
                time.sleep(1)
        else:
            print("Немає нових новин для відправки.")

        time.sleep(3)
if __name__ == "__main__":
    main_loop()
