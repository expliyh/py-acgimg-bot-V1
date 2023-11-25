FROM python:3.12-bookworm
LABEL authors="Expliyh"
ADD . /workdir
WORKDIR /workdir
RUN pip install -r requirements.txt
ENTRYPOINT ["python3", "/workdir/bot.py"]