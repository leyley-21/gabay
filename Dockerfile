FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
COPY manage.py serve.py wsgi.py ./
RUN useradd --create-home gabay && mkdir -p /var/lib/als_gabay && chown -R gabay:gabay /var/lib/als_gabay
USER gabay
ENV HOST=0.0.0.0 PORT=8080 GABAY_DATABASE_PATH=/var/lib/als_gabay/als_gabay.db
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8080')+'/health')"
CMD ["sh", "-c", "python manage.py initialize-database && python serve.py"]
