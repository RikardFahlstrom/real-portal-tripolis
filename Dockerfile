FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get -y dist-upgrade
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
RUN apt install -y netcat # Required by wait-for script
COPY . .
CMD ["python3", "program.py"]