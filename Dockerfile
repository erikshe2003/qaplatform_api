FROM python:3.6.8
ADD ./* /var/www/qaplatform_api/
WORKDIR /var/www/qaplatform_api/
RUN python3 -m venv env
RUN /bin/bash -c "source env/bin/activate"
RUN pwd
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/
EXPOSE 5050
#ENV GUNICORN_CMD_ARGS="--workers=4 --bind=0.0.0.0:5050 –preload"
#CMD ["gunicorn","automation:automation"]