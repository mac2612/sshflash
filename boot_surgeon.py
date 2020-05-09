import pager
import cbf
import sys
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


if len(sys.argv) != 2:
  print("surgeon.py: Boot a surgeon kernel on a leapfrog device in surgeon mode")
  print("Syntax: surgeon.py <surgeon_file>")
  sys.exit(1)

do_surgeon_boot(sys.argv[1])
