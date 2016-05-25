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

1. Click the Deploy to Heroku button.
2. Create a Connected App in your Salesforce organization. Provide OAuth access and set the Redirect URI to your app URL appended with /oauth_response. For example: https://sforgcompare.herokuapp.com/oauth_response
3. Configure the following Heroku environment variables with the values of your Connected App: SALESFORCE_CONSUMER_KEY, SALESFORCE_CONSUMER_SECRET.