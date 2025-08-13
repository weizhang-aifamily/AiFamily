pm2 start "gunicorn -w 4 -b 0.0.0.0:5000 /var/www/ejiacan/app:app" --name ejiacan-app

mysql -u ejiacan -p
use ejiacan;
show tables;
