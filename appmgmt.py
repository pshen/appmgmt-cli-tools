#!/usr/local/bin/python

########################
# APP mgmt cli script
# inspired by https://github.com/mikeyk/ec2-cli-tools
# Author: Chenjun Shen
########################

import os
import sys
import getopt

from sys import stderr

from fabric.api import run,get,env,task,parallel

env.key_filename="/root/.ssh/id_rsa"

app_user_mapping = {'PAS':'pas', 'PECENG':'peceng'}

def get_user(app):
	return app_user_mapping[app.split("-")[0]]

def set_user(app):
	env.user=get_user(app)

def get_jdk_bin(app):
	return "/opt/as/java-%s/bin" % (app)

#@task
#@parallel(pool_size=4)
#@with_settings(warn_only=True)
def jmap(app, dump="off", file="/dev/null"):
	set_user(app)
	jdk_bin=get_jdk_bin(app)
	#with hide('running'):
	if dump=="off":
		run('%s/jmap `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, jdk_bin, app))
	else:
		dumpfname="/var/tmp/%s.%s.hprof" % (app, env.host)
		run('%s/jmap -dump:format=b,file=%s `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, dumpfname, jdk_bin, app)) 
		run('gzip -f %s' % (dumpfname))
		get('%s.gz' % (dumpfname), local_path='%s.gz' % (dumpfname))
		run('rm -f %s.gz' % (dumpfname))

#@task
#@parallel(pool_size=4)
def jstack(app):
	set_user(app)
	jdk_bin=get_jdk_bin(app)
	run('%s/jstack `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, jdk_bin, app))

def usage():
	print >>stderr, """Usage: fabfile.py [-H HOST] [-A APP] [-T TASK] 
Prints server host name.

  -h, --help		display this help and exit
  -H, --host HOST	planet hostname
  -A, --app  APP	planet appname
  -T, --task TASK       task -> jmap/jstack"""

def main(argv):
	try:
		opts, args = getopt.getopt(argv, "hH:A:T:",
                                         ["help", "HOST=", "APP=", "TASK="])
	except getopt.GetoptError, err:
        	print >>sys.stderr, err
        	usage()
        	sys.exit(2)

	host=[]
	app=""
	task=""

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

	if not host or not app or not task:
		usage()
                sys.exit()

	env.all_hosts=host.split(",")

	print env.all_hosts

	env.user=get_user(app)
	
	if task=="jmap":
		jmap(app)
	elif task=="jstack":
		jstack(app)
	else:
		usage()
		sys.exit()
	
if __name__ == "__main__":
	main(sys.argv[1:])
