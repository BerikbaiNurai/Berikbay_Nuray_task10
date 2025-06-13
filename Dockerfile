FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# (Не обязательно, если command указан в docker-compose.yml)
# CMD — на случай, если запускаем контейнер без compose
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
