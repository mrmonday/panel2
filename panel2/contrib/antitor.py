import requests

from panel2 import app, cron
from panel2.service import IPAddress
from panel2.cron import HOURLY

@cron.task(HOURLY)
def antitor_suspend():
    data = requests.get('http://torstatus.blutmagie.de/ip_list_exit.php/Tor_ip_list_EXIT.csv')
    ips = data.text.split('\n')

    print 'suspending tor nodes'

    ctx = app.test_request_context()
    ctx.push()

    for ip in ips:
        ipa = IPAddress.query.filter_by(ip=ip).first()
        if not ipa or ipa.service.tor_whitelisted:
            continue
        if not ipa.service.is_entitled:
            ipa.service.destroy()
            continue
        ipa.service.suspend(disable_renew=True, template='email/service-suspended-tor.txt')

    ctx.pop()
