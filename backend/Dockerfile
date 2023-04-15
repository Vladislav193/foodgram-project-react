FROM python:3.7-slim
WORKDIR /app
<<<<<<< HEAD
COPY requirements.txt ./
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]
=======
COPY backend/requirements.txt ./
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ] 
>>>>>>> 63237f0dcb846cedcb36f9f4dd8ce49573833824
