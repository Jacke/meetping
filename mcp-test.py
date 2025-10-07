import openai
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain.chains import ConversationChain
try:
    from langchain_openai import OpenAI as LCOpenAI
except ImportError:
    try:
        from langchain_community.llms import OpenAI as LCOpenAI
    except ImportError:
        from langchain.llms import OpenAI as LCOpenAI
from langchain.prompts import PromptTemplate
from sqlalchemy import create_engine, Column, String, Integer, Sequence
from sqlalchemy.orm import declarative_base, sessionmaker

# Загрузка переменных окружения из .env в корне проекта
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "Не задан OPENAI_API_KEY. Создайте файл .env с OPENAI_API_KEY=..."
    )
openai.api_key = api_key

# Настройка базы данных
Base = declarative_base()

class UserContext(Base):
    __tablename__ = 'user_context'
    id = Column(Integer, Sequence('user_context_id_seq'), primary_key=True)
    user_id = Column(Integer)
    context = Column(String(500))

# Инициализация SQLAlchemy
engine = create_engine('sqlite:///context.db', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Функция для добавления контекста пользователя в базу данных
def save_user_context(user_id, context):
    existing_context = session.query(UserContext).filter(UserContext.user_id == user_id).first()
    if existing_context:
        existing_context.context = context
    else:
        new_context = UserContext(user_id=user_id, context=context)
        session.add(new_context)
    session.commit()

# Функция для получения контекста пользователя из базы данных
def get_user_context(user_id):
    user_context = session.query(UserContext).filter(UserContext.user_id == user_id).first()
    return user_context.context if user_context else ""

# Настройка ИИ-агента с многоуровневым контекстом (агент не используется, оставляем только LLM)
try:
    llm = LCOpenAI(temperature=0.7, model="gpt-3.5-turbo-instruct")
except TypeError:
    # Для старых версий LangChain параметр может называться model_name
    llm = LCOpenAI(temperature=0.7, model_name="gpt-3.5-turbo-instruct")

# Уровень 1: Чтение контекста
def fetch_context(user_id):
    context = get_user_context(user_id)
    return context

# Уровень 2: Ответ на запрос
def process_request(user_id, user_input):
    context = fetch_context(user_id)
    
    # Формируем запрос с учётом контекста
    prompt = f"User context: {context}\nUser input: {user_input}\nAssistant response:"

    # Получаем ответ с учётом предыдущих взаимодействий (через LangChain LLM)
    answer = llm.invoke(prompt).strip()
    # Сохраняем обновлённый контекст
    updated_context = f"{context} {user_input} {answer}"
    save_user_context(user_id, updated_context)
    return answer

# Уровень 3: Действие на основе запросов и рекомендаций
def execute_action(user_id, action):
    if action == 'show weather':
        return "Here’s the current weather in your area: sunny and 72°F."
    elif action == 'suggest movie':
        return "I recommend watching 'Inception' based on your interests."
    else:
        return "I couldn't understand the action, please try again."

# Основной цикл взаимодействия с ИИ-агентом
def main():
    user_id = 1  # Уникальный ID пользователя
    print("Добро пожаловать в интеллектуальный агент!")
    
    while True:
        user_input = input("Вы: ")
        if user_input.lower() == "выход":
            print("До свидания!")
            break

        # Обрабатываем запрос
        response = process_request(user_id, user_input)
        print(f"ИИ: {response}")

        # Предложение действия
        action = input("Хотите, чтобы я выполнил действие? (Да/Нет): ")
        if action.lower() == "да":
            user_action = input("Какое действие вы хотите, чтобы я выполнил? ")
            action_response = execute_action(user_id, user_action)
            print(f"ИИ выполняет: {action_response}")

if __name__ == "__main__":
    main()

