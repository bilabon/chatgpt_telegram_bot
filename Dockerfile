FROM python:3.11-slim-buster
WORKDIR /bot
COPY requirements.txt /bot/
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install -r requirements.txt
COPY . /bot
CMD python main.py