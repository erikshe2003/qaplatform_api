FROM python:3.6.8
ADD ./* /var/www/qaplatform_api/
WORKDIR /var/www/qaplatform_api/
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/
EXPOSE 5050
CMD ["gunicorn","-b 0.0.0.0:5050 automation:automation"]