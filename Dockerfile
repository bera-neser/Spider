FROM alpine

RUN apk update && \
    apk add python3 && \
    python3 -m ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

WORKDIR /app

COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT ["python", "spider.py"]
