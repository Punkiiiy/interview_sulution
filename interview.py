import requests
import asyncio
import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_TOKEN = os.getenv("OPENAI_TOKEN")


async def ask_openai(session, task, comment):
    messages = [{
        "role": "system",
        "content": "Тебе приходит название задачи и комментарий пользователя по её выполнению. Проанализируй комментарий и скажи, положительный он или нет?"
    }, {
        "role": "user",
        "content": f"Название - '{task}'. Комментарий - '{comment}'"
    }]

    body = {
        "model": "gpt-4o-mini",
        "messages": messages
    }

    try:
        async with session.post(
                url="https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_TOKEN}"
                },
                json=body
        ) as response:
            data = await response.json()


            if "error" in data:
                print(f"Ошибка OpenAI API: {data['error']}")
                return f"Ошибка анализа: {data['error'].get('message', 'Unknown error')}"

            if "choices" not in data:
                print(f"Неожиданный ответ от API: {data}")
                return "Ошибка: неожиданный формат ответа"

            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Исключение при вызове OpenAI API: {e}")
        return f"Ошибка: {str(e)}"


def get_all_clients(search: str | None = None, limit: int = 5):
    query = {
        "limit": limit
    }
    if search:
        query["search"] = search

    response = requests.get(
        url=f"https://interview-mock-backend.onrender.com/api/v1/clients",
        params=query
    )
    return response.json()


def get_client_tasks(client_id: int, limit: int = 10):
    query = {
        "client_id": client_id,
        "limit": limit
    }
    response = requests.get(
        url=f"https://interview-mock-backend.onrender.com/api/v1/tasks",
        params=query
    )
    return response.json()


def get_task_comments(task_id: int):
    response = requests.get(
        url=f"https://interview-mock-backend.onrender.com/api/v1/tasks/{task_id}/comments"
    )
    return response.json()


async def analyze_comments(comments):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for task_title, comment_list in comments.items():
            for comment_text in comment_list:
                tasks.append(ask_openai(session, task_title, comment_text))

        results = await asyncio.gather(*tasks)
        print("\n=== Результаты анализа ===")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result}")


users = get_all_clients()
print("Users:", users)

tasks = get_client_tasks(users["data"][0]["id"])
print("Tasks:", tasks)

comments = {}
for task in tasks["data"]:
    comment = get_task_comments(task["id"])
    if comment.get("data"):
        comments[comment["meta"]["taskTitle"]] = [text["text"] for text in comment["data"]]

print(f"\nНайдено комментариев для анализа: {sum(len(v) for v in comments.values())}")

if comments:
    asyncio.run(analyze_comments(comments))
else:
    print("Комментарии для анализа не найдены")