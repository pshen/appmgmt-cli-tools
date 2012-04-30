#!/usr/local/bin/python
#
#####################################################
# APP mgmt cli script
# https://github.com/pshen/appmgmt-cli-tools
#
# inspired by https://github.com/mikeyk/ec2-cli-tools
# Author: Chenjun Shen
#
#####################################################

import os
import sys
import getopt

from sys import stderr
from fabric.api import run,get,env

# SET SSH PRIVATE KEY LOCATION
env.key_filename="/home/appmgmt/.ssh/id_rsa"

# APP<->USER MAPPING
APP_USER_MAPPING = {'PAS':'pas', 'PECENG':'pec'}

def get_user(app):
	return APP_USER_MAPPING[app.split("-")[0]]

def get_jdk_bin(app):
	return "/opt/as/java-%s/bin" % (app)

def jinfo(app):
	run('%s/jinfo `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, jdk_bin, app))

def jmap(app, dump="off", file="/dev/null"):
	#with hide('running'):
	if dump=="off":
		run('%s/jmap `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, jdk_bin, app))
	else:
		dumpfname="/var/tmp/%s.%s.hprof" % (app, env.host)
		run('%s/jmap -dump:format=b,file=%s `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, dumpfname, jdk_bin, app)) 
		run('gzip -f %s' % (dumpfname))
		get('%s.gz' % (dumpfname), local_path='%s.gz' % (dumpfname))
		run('rm -f %s.gz' % (dumpfname))

def jstack(app, force=False):
	if force:
		run('%s/jstack -F `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, jdk_bin, app))
	else:
		run('%s/jstack `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, jdk_bin, app))

def lsof(app):
	run('/usr/sbin/lsof -p `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, app))

def netstat(app):
	run('/bin/netstat -anp | grep `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, app))

def view(app, path):
	file_path="/opt/as/APP/%s/%s" % (app, path)
	run('test -f %s && /bin/cat %s' % (file_path, file_path))

def usage():
	print >>stderr, """Usage: appmgmt.py [-H HOST] [-A APP] [-T TASK] [-P PATH]

  -h, --help		display this help and exit
  -H, --host HOST	hostname -> fraapppas01.int.fra.net-m.internal
  -A, --app  APP	appname -> PAS-APP01
  -T, --task TASK       task -> jinfo/jmap/jstack/lsof/netstat/view
  -P, --path PATH	path -> conf/server.xml"""

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hH:A:T:P:",
                                         ["help", "HOST=", "APP=", "TASK=", "PATH="])
	except getopt.GetoptError, err:
        	print >>sys.stderr, err
        	usage()
        	sys.exit(2)

	for opt, arg in opts:
        	if opt in ("-h", "--help"):
            		usage()
            		sys.exit()
        	elif opt in("-H", "--host"):
            		host = arg
        	elif opt in("-A", "--app"):
            		app = arg
        	elif opt in("-T", "--task"):
            		task = arg
		elif opt in ("-P", "--PATH"):
			path = arg

	if not host or not app or not task:
		usage()
                sys.exit(1)

	env.host_string=host
	env.user=get_user(app)
	global jdk_bin
	jdk_bin=get_jdk_bin(app)
	
	if task=="jinfo":
		jinfo(app)
	elif task=="jmap":
		jmap(app)
	elif task=="jstack":
		jstack(app)
	elif task=="jstack_with_force":
		jstack(app, force=True)		
	elif task=="lsof":
		lsof(app)
	elif task=="netstat":
		netstat(app)
	elif task=="view":
		view(app, path)
	else:
		usage()
		sys.exit(1)
	
if __name__ == "__main__":
	main(sys.argv[1:])
