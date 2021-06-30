FROM python:3.7-slim-buster

RUN apt-get update && apt-get install -y duplicity && pip3 install dup-composer

CMD ["dupcomp"]
