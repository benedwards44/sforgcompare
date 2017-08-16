# sforgcompare
Django + Heroku application which compares metadata between two Salesforce environments and presents the differences

## Addons

1. Heroku Postgres
2. Heroku Redis
3. Heroku Scheduler (for clearing database)

## Config Variables

1. DEFAULT_FROM_EMAIL (eg. ben@edwards.nz)
2. EMAIL_HOST (eg. smtp.gmail.com)
3. EMAIL_HOST_PASSWORD
4. EMAIL_HOST_USER (eg. ben@edwards.nz)
5. EMAIL_PORT (eg. 587)
6. SALESFORCE_API_VERSION (eg. 39)
7. SALESFORCE_CONSUMER_KEY (from Salesforce Connected App)
8. SALESFORCE_CONSUMER_SECRET (from Salesforce Connected App)
