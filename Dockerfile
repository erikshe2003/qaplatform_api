FROM python:3.6.8
COPY ./ /var/www/qaplatform_api/
WORKDIR /var/www/qaplatform_api/
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/
EXPOSE 5050
#ENV GUNICORN_CMD_ARGS="--workers=4 --bind=0.0.0.0:5050 –preload"
CMD ["gunicorn", "--chdir", "/var/www/qaplatform_api/", "automation:automation", "-c", "/var/www/qaplatform_api/config/gunicorn.conf"]
# nohup gunicorn -w 2 -b 0.0.0.0:5050 automation:automation > nohup.log 2>&1 &
#CMD nohup gunicorn -w 2 -b 0.0.0.0:5050 automation:automation > nohup.log 2>&1 &