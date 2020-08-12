FROM python:3.6.8
ADD ./* /var/www/qaplatform_api
WORKDIR /var/www/qaplatform_api
RUN pip install -r requirements.txt -i http://pypi.douban.com/simple/
EXPOSE 5050
CMD ["gunicorn","-w 4 -b 0.0.0.0:5050 app:app"]