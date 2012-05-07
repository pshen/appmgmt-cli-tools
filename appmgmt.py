#!/usr/local/bin/python
#
#####################################################
# APP mgmt cli script
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

def get_pid(app):
    print "GETTING PID OF APP=%s" % (app)
    return run('%s/jps -v | awk \'/%s/{print $1}\'' % (jdk_bin, app))

def jinfo(pid, optn=""):
    run('%s/jinfo %s %s' % (jdk_bin, optn, pid))

def jmap(pid, dump=False, optn=""):
    #with hide('running'):
    if not dump:
        run('%s/jmap %s %s' % (jdk_bin, optn, pid))
    else:
        dumpfname="/var/tmp/%s.%s.hprof" % (pid, env.host)
        run('%s/jmap -dump:format=b,file=%s %s' % (jdk_bin, dumpfname, pid)) 
        run('gzip -f %s' % (dumpfname))
        get('%s.gz' % (dumpfname), local_path='%s.gz' % (dumpfname))
        run('rm -f %s.gz' % (dumpfname))

def jstack(pid, optn=""):
        run('%s/jstack %s %s' % (jdk_bin, optn, pid))

def lsof(pid):
    run('/usr/sbin/lsof -p %s' % (pid))

def netstat(pid):
    run('/bin/netstat -anp | grep %s' % (pid))

def view(app, optn=""):
    file_path="/opt/as/APP/%s/%s" % (app, optn)
    run('test -f %s && /bin/cat %s' % (file_path, file_path))

def usage():
    print >>stderr, """Usage: appmgmt.py [-H HOST] [-A APP] [-T TASK] [-P PATH]

  -h, --help         display this help and exit
  -H, --host HOST    hostname -> fraapppas01.int.fra.net-m.internal
  -A, --app  APP     appname -> PAS-APP01
  -T, --task TASK    task -> jinfo/jmap/jmap_with_dump/jstack/lsof/netstat/view
  -O, --optn OPTION  optn -> option sent to the native cmd"""

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "hH:A:T:O:", ["help", "host=", "app=", "task=", "optn="])
    except getopt.GetoptError, err:
        print >>sys.stderr, err
        usage()
        sys.exit(2)

    # init
    optn=""

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
        elif opt in ("-P", "--optn"):
            optn = arg

    if not host or not app or not task:
        usage()
        sys.exit(1)

    env.host_string=host
    env.host=host
    env.user=get_user(app)
    global jdk_bin
    jdk_bin=get_jdk_bin(app)

    # getting pid
    pid = get_pid(app)
    if pid=="":
        print "NO RUNNING INSTANCE"
        sys.exit(2)

    if task=="jinfo":
        jinfo(pid, optn)
    elif task=="jmap":
        jmap(pid, False, optn)
    elif task=="jmap_with_dump":
        jmap(pid, True, optn) 
    elif task=="jstack":
        jstack(pid, optn)
    elif task=="lsof":
        lsof(pid)
    elif task=="netstat":
        netstat(pid)
    elif task=="view":
        view(app, optn)
    else:
        usage()
        sys.exit(1)
    
if __name__ == "__main__":
    main(sys.argv[1:])
