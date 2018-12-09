import pager
import cbf
from interface import config as conn_iface
from mount import connection as mount_connection

def do_surgeon_boot(path):
    """
Usage:
surgeon_boot <path to surgeon.cbf>

Uploads a Surgeon.cbf file to a device in USB Boot mode. 
File can be any name, but must conform to CBF standards.
    """
    pager_client = pager.client(conn_iface(mount_connection()))
    pager_client.upload(path)
    print 'Booting surgeon.'


cbf.create(mem='superhigh', opath='surgeon_wrap.cbf', ipath='surgeon_zImage')
do_surgeon_boot('surgeon_wrap.cbf')
