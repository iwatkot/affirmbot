FROM python:3.11

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH .:${PYTHONPATH}
CMD ["python", "./src/bot.py"]