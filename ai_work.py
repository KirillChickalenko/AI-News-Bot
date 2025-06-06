import os
import json
import time
import hashlib
from together import Together
import difflib

os.environ["TOGETHER_API_KEY"] = "API КЛЮЧ ДЛЯ TOGETHER.AI"
client = Together()

def file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def clean_ai_input():
    if not os.path.exists('ai_input.json'):
        print("Файл ai_input.json не знайдено.")
        return

    with open('ai_input.json', 'r', encoding='utf-8') as f:
        try:
            articles = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Помилка декодування JSON: {e}")
            return

    filtered = []
    for article in articles:
        content = article.get('content', '').strip()
        if content not in ["Текст не знайдено.", "Не вдалося отримати повний текст."] and len(content) >= 100:
            filtered.append(article)
        else:
            print(f"Видаляю статтю через відсутність або короткий текст: {article.get('title')}")

    with open('ai_input.json', 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

def is_similar(text1, text2, threshold=0.85):
    ratio = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    return ratio >= threshold

def process_news():
    clean_ai_input()

    if not os.path.exists('ai_input.json'):
        print("Файл ai_input.json не знайдено після очищення.")
        return []

    with open('ai_input.json', 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            print("Файл ai_input.json пустий після очищення.")
            return []
        try:
            articles = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Помилка декодування JSON: {e}")
            return []

    results = []
    processed_texts = []

    for article in articles:
        prompt = f"""
        Скороти й покращ текст новини, зберігаючи ключову інформацію. І все українською мовою. 
        Заголовок: {article['title']}
        Текст: {article['content']}

        Поверни лише покращений текст у форматі:
        [Заголовок]: короткий заголовок українською мовою у стилі телеграм поста
        [Зміст]: лаконічний виклад українською мовою у стилі телеграм поста
        """

        try:
            response = client.chat.completions.create(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )

            processed_text = response.choices[0].message.content.strip()

            if any(is_similar(processed_text, existing) for existing in processed_texts):
                print(f"ДУБЛЬОВАНА НОВИНА: {article['title']}")
                continue

            processed_texts.append(processed_text)

            results.append({
                'original': article['title'],
                'processed': processed_text,
                'url': article['url'],
                'source': article['source']
            })

            print(f"Оброблено: {article['title']}")

        except Exception as e:
            print(f"Помилка при обробці новини: {str(e)}")
            continue

    with open('ai_output.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return results

if __name__ == "__main__":
    last_hash = None

    while True:
        current_hash = file_hash('ai_input.json')
        if current_hash and current_hash != last_hash:
            print("Запускаю обробку...")
            process_news()
            last_hash = current_hash
        time.sleep(3)
