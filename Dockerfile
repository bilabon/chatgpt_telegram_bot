FROM python:3.11
WORKDIR /bot
COPY requirements.txt /bot/
RUN apt-get install ffmpeg
RUN pip install -r requirements.txt
COPY . /bot
CMD python main.py