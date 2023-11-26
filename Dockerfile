FROM python:3.12-bookworm
LABEL authors="Expliyh"
ADD . /workdir
WORKDIR /workdir
RUN pip install -r requirements.txt
ENV DATABASE_HOST=mariadb
ENV DATABASE_PORT=3306
ENV DATABASE_NAME=your_database_name
ENV DATABASE_USERNAME=your_username
ENV DATABASE_PASSWORD=your_password
ENV PIXIV_API_URL=""
ENV TELEGRAM_BOT_TOKEN=your_telegram_token
ENV DEVELOPER_CHAT_ID=""
ENV TZ=Asia/Shanghai
RUN mkdir tmp
VOLUME /workdir/tmp
ENTRYPOINT ["python3", "/workdir/bot.py"]