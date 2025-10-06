import openai
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from sqlalchemy import create_engine, Column, String, Integer, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Инициализация OpenAI API
openai.api_key = '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'

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

# Настройка ИИ-агента с многоуровневым контекстом
llm = OpenAI(temperature=0.7)
agent = initialize_agent(
    tools=[], 
    llm=llm, 
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True
)

# Уровень 1: Чтение контекста
def fetch_context(user_id):
    context = get_user_context(user_id)
    return context

# Уровень 2: Ответ на запрос
def process_request(user_id, user_input):
    context = fetch_context(user_id)
    
    # Формируем запрос с учётом контекста
    prompt = f"User context: {context}\nUser input: {user_input}\nAssistant response:"

    # Получаем ответ с учётом предыдущих взаимодействий
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7
    )

    answer = response.choices[0].text.strip()
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

