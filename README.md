Salesforce Org Compare
============

Salesforce + Heroku application which compares metadata between two environments and presents the differences. The application is currently running at https://sforgcompare.herokuapp.com.

The tool uses the following technologies:
- Python
- Django
- Heroku
- Celery
- Redis
- Salesforce Tooling API
- Salesforce Metadata APi

## Setup

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/benedwards44/sforgcompare)


1. Create Heroku application
2. Install Heroku addons - Database, PostMark (outbound email tool), RedisToGo, Heroku Scheduler
2. Deploy code
3. Create a Connected App in your Salesforce organization.
4. Configure the following Heroku environment variables with the values of your Connected App: SALESFORCE_CONSUMER_KEY, SALESFORCE_CONSUMER_SECRET.
