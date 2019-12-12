FROM python:3.5
ENV PYTHONUNBUFFERED 1
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
WORKDIR /parse_sites_app/