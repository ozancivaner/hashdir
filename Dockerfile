FROM python:3.10

COPY . /hashdir
WORKDIR /hashdir

RUN pip install .[imohash]

CMD ["hashdir"]
