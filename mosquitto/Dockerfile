FROM python:3

WORKDIR /usr/src/app

COPY . .

RUN apt-get -y update
RUN pip3 install -r requirements.txt

# -u for unbuffered output
ENTRYPOINT ["python3", "-u"]
