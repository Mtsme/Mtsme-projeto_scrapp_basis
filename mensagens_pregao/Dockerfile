FROM python:3.11.7-slim
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt && rm -rf /requirements.txt
RUN apt-get -yqq update && \
    apt-get install -y gnupg2 curl xvfb x11vnc fluxbox && \
    curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*
RUN sbase get chromedriver && sbase get uc_driver
ENV DISPLAY=:0
