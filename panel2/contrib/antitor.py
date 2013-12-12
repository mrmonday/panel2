import requests

from panel2 import app, cron
from panel2.service import IPAddress
from panel2.cron import HOURLY

@cron.task(HOURLY)
def antitor_suspend():
    data = requests.get('http://torstatus.blutmagie.de/ip_list_exit.php/Tor_ip_list_EXIT.csv')
    ips = data.text.split('\n')

    ctx = app.test_request_context()
    ctx.push()

    for ip in ips:
        ipa = IPAddress.query.filter_by(ip=ip).first()
        if not ipa or not ipa.service.is_entitled or ipa.service.tor_whitelisted:
            continue
        ipa.service.suspend(disable_renew=True)

    ctx.pop()
