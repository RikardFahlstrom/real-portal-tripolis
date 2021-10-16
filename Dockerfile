FROM python:3.8-slim-buster
RUN apt-get update && apt-get -y dist-upgrade && apt install -y netcat
WORKDIR /scraper_code
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY . .
CMD ["python3", "program.py"]
