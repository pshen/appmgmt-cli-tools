#!/usr/local/bin/python
#
#####################################################
# APP mgmt cli script
# https://github.com/pshen/appmgmt-cli-tools
#
# inspired by
# a) https://github.com/mikeyk/ec2-cli-tools
# b) https://gist.github.com/2307647 
#
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

def jinfo(app, para):
    run('%s/jinfo %s `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, para, jdk_bin, app))

def jmap(app, dump=False, para):
    #with hide('running'):
    if not dump:
        run('%s/jmap %s `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, para, jdk_bin, app))
    else:
        dumpfname="/var/tmp/%s.%s.hprof" % (app, env.host)
        run('%s/jmap -dump:format=b,file=%s `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, dumpfname, jdk_bin, app)) 
        run('gzip -f %s' % (dumpfname))
        get('%s.gz' % (dumpfname), local_path='%s.gz' % (dumpfname))
        run('rm -f %s.gz' % (dumpfname))

def jstack(app, force=False, para):
    if force:
        run('%s/jstack %s -F `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, para, jdk_bin, app))
    else:
        run('%s/jstack %s `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, para, jdk_bin, app))

def lsof(app):
    run('/usr/sbin/lsof -p `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, app))

def netstat(app):
    run('/bin/netstat -anp | grep `%s/jps -v | awk \'/%s/{print $1}\'`' % (jdk_bin, app))

def view(app, para):
    file_path="/opt/as/APP/%s/%s" % (app, para)
    run('test -f %s && /bin/cat %s' % (file_path, file_path))

def usage():
    print >>stderr, """Usage: appmgmt.py [-H HOST] [-A APP] [-T TASK] [-P PATH]

  -h, --help         display this help and exit
  -H, --host HOST    hostname -> fraapppas01.int.fra.net-m.internal
  -A, --app  APP     appname -> PAS-APP01
  -T, --task TASK    task -> jinfo/jmap/jmap_with_dump/jstack/jstack_with_force/lsof/netstat/view
  -P, --para PARA    para -> parameter send to the native cmd"""

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hH:A:T:P:", ["help", "HOST=", "APP=", "TASK=", "PARA="])
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
        elif opt in ("-P", "--para"):
            para = arg

    if not host or not app or not task:
        usage()
        sys.exit(1)

    env.host_string=host
    env.host=host
    env.user=get_user(app)
    global jdk_bin
    jdk_bin=get_jdk_bin(app)
    
    if task=="jinfo":
        jinfo(app, para)
    elif task=="jmap":
        jmap(app, False, para)
    elif task=="jmap_with_dump":
        jmap(app, True, para) 
    elif task=="jstack":
        jstack(app, False, para)
    elif task=="jstack_with_force":
        jstack(app, True, para)        
    elif task=="lsof":
        lsof(app)
    elif task=="netstat":
        netstat(app)
    elif task=="view":
        view(app, para)
    else:
        usage()
        sys.exit(1)
    
if __name__ == "__main__":
    main(sys.argv[1:])
