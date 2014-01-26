from panel2.vps.models import XenVPS
from panel2 import db, cron
from panel2.cron import HOURLY

@cron.task(HOURLY)
def throttle_bulk_users():
    vpslist = filter(lambda x: x.get_average_cpu() > 60, XenVPS.query.filter_by(is_entitled=True).filter_by(cpu_sla='standard'))

    for vps in vpslist:
        vps.cpu_sla = 'bulk'
        db.session.add(vps)
        db.session.commit()

        vps.confupdate()
        vps.schedupdate()

        print 'Throttling:', vps.id, vps.name, vps.nickname, vps.get_average_cpu()

@cron.task(HOURLY)
def unthrottle_good_users():
    vpslist = filter(lambda x: x.get_average_cpu() < 15, XenVPS.query.filter_by(is_entitled=True).filter_by(cpu_sla='bulk'))

    for vps in vpslist:
        vps.cpu_sla = 'standard'
        db.session.add(vps)
        db.session.commit()

        vps.confupdate()
        vps.schedupdate()

        print 'Unthrottling:', vps.id, vps.name, vps.nickname, vps.get_average_cpu()
