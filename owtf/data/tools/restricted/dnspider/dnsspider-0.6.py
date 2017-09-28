#!/usr/bin/env python

# BUG dnsspider-0.5.py -t 0 -d 194.98.65.69 -H ../Wordlists/HostNames-200 -a

# -*- coding: latin-1 -*- ######################################################
#                                                                              #
# dnsspider-0.6.py - multithreaded subdomain bruteforcer                       #
#                                                                              #
# Patched/modified/enhanced version                                            #
# Based on v0.4 by NullSecurity                                                #
#                                                                              #
# DATE                                                                         #
# 05/31/2013                                                                   #
#                                                                              #
# DESCRIPTION                                                                  #
# A very fast multithreaded bruteforcer of subdomains                          #
#                                                                              #
# CHANGELOG:                                                                   #
#                                                                              #
# v0.6                                                                         #
# - fix a bug regarding attack_pool.release()                                  #
# - loop until no timeout / bad response                                       #
# - display some stats about the scan                                          #
# - scans for AAAA and SRV records                                             #
#                                                                              #
################################################################################


import sys
import time
import string
import itertools
import socket
import threading
import re


BANNER = '+--------------+\n' \
         '| dnsspider.py |\n' \
         '+--------------+'
USAGE = '\n\n' \
        '  dnsspider.py -h'
VERSION = 'dnsspider.py v0.6'

defaults = {}
hostnames = []
prefix = ''
postfix = ''
found = []
chars = string.ascii_lowercase
digits = string.digits

# stats
nb_tests = 0
nb_founds = 0
nb_errors = 0


def blue(msg):
    print '[+] \033[0;94m' + msg + '\033[0;m'
    return


def red(msg):
    print '[-] ERROR: \033[0;91m' + msg + '\033[0;m'
    return


from optparse import OptionParser
try:
    import dns.message
    import dns.query
except ImportError:
    red("you need 'dnspython' package")
    sys.exit()


def usage():
    print('\n' + USAGE)
    sys.exit()
    return


def check_usage():
    if len(sys.argv) == 1:
        print('[-] WARNING: use -h for help and usage')
        sys.exit()
    return


def get_default_nameserver():
    blue('getting default nameserver')
    lines = list(open('/etc/resolv.conf', 'r'))
    for line in lines:
        line = string.strip(line)
        if not line or line[0] == ';' or line[0] == '#':
            continue
        fields = string.split(line)
        if len(fields) < 2:
            continue
        if fields[0] == 'nameserver':
            defaults['nameserver'] = fields[1]
            return defaults


def get_default_source_ip():
    blue('getting default ip address')
    try:
        # get current used iface enstablishing temp socket
        ipsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ipsocket.connect(("gmail.com", 80))
        defaults['ipaddr'] = ipsocket.getsockname()[0]
        blue('found currently used interface ip ' + "'" +
                defaults['ipaddr'] + "'")
        ipsocket.close()
    except:
        red('can\'t get your ip-address, use "-i" option and define yourself')
    return defaults


def parse_cmdline():
    p = OptionParser(usage=USAGE, version=VERSION)
    p.add_option('-a', dest='domain',
            help='subdomain to bruteforce')
    p.add_option('-H', dest='wl_hosts',
            help='hosts wordlist, one hostname per line')
    p.add_option('-S', dest='wl_services',
            help='services wordlist, one service per line')
    p.add_option('-d', dest='dnshost',
            help='choose another nameserver (default your system\'s)')
    p.add_option('-i', dest='ipaddr',
            help='source ip address to use (default your systems\'s)')
    p.add_option('-p', dest='port', default=0,
            help='source port to use (default %default --> first free random'
                    'port) ' '\n\nnote: if fixed port, use max 1 thread!')
    p.add_option('-o', dest='timeout', default=3,
            help='timeout (default %defaults)')
    p.add_option('-v', action='store_true', dest='verbose', 
            help='verbose mode - prints every attempt (default quiet)')
    p.add_option('-x', dest='threads', default=32,
            help='number of threads to use (default %default) - choose more :)')
    p.add_option('-r', dest='logfile', default='stdout',
            help='write found subdomains to file (default %default)')
    (opts, args) = p.parse_args()
    return opts


def check_cmdline(opts):
    if not opts.domain:
        red('see usage, mount /dev/brain')
        sys.exit()
    return


def set_opts(defaults, opts):
    if not opts.dnshost:
        opts.dnshost = defaults['nameserver']
    if not opts.ipaddr:
        opts.ipaddr = defaults['ipaddr']
    return opts


def read_wordlist(wordlist):
    words = []
    if wordlist:
        words = list(open(wordlist, 'r'))
    return words


def attack(opts, hostname, attack_pool, query_type):
    global nb_tests
    global nb_founds
    global nb_errors

    # sys.stdout.write('--- \033[0;91m Active DNS threads: %d \033[0;m\n' % (threading.active_count() - 1))
    # sys.stdout.flush()
    if opts.verbose:
        sys.stdout.write('--- \033[0;93m [%d/%d] \033[0;91m[%d]\033[0;m %s %s\n' % (nb_founds, nb_tests, nb_errors, hostname, query_type))
        sys.stdout.flush()

    ok = False
    while not ok:
       nb_tests = nb_tests + 1

       try:
           x = dns.message.make_query(hostname, query_type)
           a = dns.query.udp(x, opts.dnshost, float(opts.timeout), 53, None, opts.ipaddr, int(opts.port), True, False)
       except dns.exception.Timeout:
           #red('Time out')
   	   nb_errors = nb_errors + 1
           continue
       except dns.exception.FormError:
           # red('Bad response')
   	   nb_errors = nb_errors + 1
           continue
       except socket.error:
           # red('No connection? Fixed src port + several threads?')
   	   nb_errors = nb_errors + 1
	   continue

       ok = True
       if a.answer:
           answ = ''
           # iterate dns rrset answer (can be multiple sets) field to extract
           # detailed info (dns and ip) 
           for i in a.answer:
               answ += str(i[0])
               answ += ' '
           answer = (hostname, query_type, answ)
           found.append(answer)
	   nb_founds = nb_founds + 1
    attack_pool.release()
    return


def start_thread(opts, hostname, attack_pool, threads, query):
    t = threading.Thread(target=attack, args=(opts, hostname, attack_pool, query))
    attack_pool.acquire()
    try:
        t.start()
    except Exception, e:
        red('Can\'t start a new thread. Please lower the max number of threads using \'-x\'')
	sys.exit()
    threads.append(t)
    return threads


def start_attack(opts, hostnames, services):
    sys.stdout.write('[+] \033[0;94mattacking \'%s\' via \033[0;m' % opts.domain)
    threads = list()
    attack_pool = threading.BoundedSemaphore(value=int(opts.threads))
    sys.stdout.write('\033[0;94mdictionary\033[0;m\n')

    for hostname in hostnames:
	# A and AAAA
        hostname = hostname.rstrip() + '.' + opts.domain
        threads = start_thread(opts, hostname, attack_pool, threads, 'A')
        threads = start_thread(opts, hostname, attack_pool, threads, 'AAAA')

    for service in services:
	# SRV (UDP and TCP)
        service_udp = service.rstrip() + '._udp.' + opts.domain
        threads = start_thread(opts, service_udp, attack_pool, threads, 'SRV')
        service_tcp = service.rstrip() + '._tcp.' + opts.domain
        threads = start_thread(opts, service_tcp, attack_pool, threads, 'SRV')

    for t in threads:
        t.join()
    return


def log_results(opts, nb_hosts, nb_services, found, time):
    out = sys.stdout
    if opts.logfile != 'stdout':
        print('[+] \033[0;94mlogging results to \'%s\'\033[0;m' % opts.logfile)
        try:
            out = open(opts.logfile, 'w')
        except IOError:
            red('I/O error when writing to \'%s\'. Dumping to stdout' % opts.logfile)
            out = sys.stdout

    # Stats
    out.write('---\n')
    out.write('STATS\n')
    out.write('Duration: %d seconds\n' % time)
    out.write('Duration: %d seconds\n' % time)
    out.write('Number of hostnames in wordlist: %d\n' % nb_hosts)
    out.write('Number of services in wordlist: %d\n' % nb_services)
    out.write('Number of tests: %d\n' % nb_tests)
    out.write('Number of retries: %d (%.2f%%)\n' % (nb_errors, (nb_errors) / (nb_tests / 100.)))
    out.write('Number of hits: %d\n' % nb_founds)

    # Found hosts
    if found:
        out.write('---\n')
        out.write('ANSWERED DNS REQUESTS\n')
        out.write('---\n')
        for x in found:
            out.write('domain: '+x[0]+' | '+x[1]+' | '+x[2]+'\n')
    else:
        out.write('---\n')
        out.write('NO HOSTS FOUND\n')
        out.write('---\n')

    blue('game over')
    return


def main():
    start_time = time.time()
    check_usage()
    opts = parse_cmdline()
    check_cmdline(opts)
    if not opts.dnshost:
        defaults = get_default_nameserver()
    if not opts.ipaddr:
        defaults = get_default_source_ip()
    opts = set_opts(defaults, opts)
    hostnames = read_wordlist(opts.wl_hosts)
    services = read_wordlist(opts.wl_services)
    start_attack(opts, hostnames, services)
    log_results(opts, len(hostnames), len(services), found, time.time() - start_time)
    return


if __name__ == '__main__':
    print(BANNER)
    main()

# EOF
