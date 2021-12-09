import requests
import logging
from huey.contrib.djhuey import task
from app.disposable_email import models as email_models


logger = logging.getLogger('conote')


@task()
def send_notification(token, title, message):
    target = "https://sc.ftqq.com/{}.send".format(token)
    response = requests.post(target, data=dict(
        text=title,
        desp=message
    ))
    response.encoding = 'utf-8'
    return response.text
