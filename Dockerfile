FROM python:3.6.8
COPY ./ /var/www/qaplatform_api/
WORKDIR /var/www/qaplatform_api/
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/
EXPOSE 5050
CMD ["gunicorn", "--chdir", "/var/www/qaplatform_api/", "automation:automation", "-c", "/var/www/qaplatform_api/config/gunicorn.conf"]