!/usr/bin/env python
'''
Script to be added as a cpanel standard hook for nginx php-fpm compatiblity
this script has hooks for:
- creating nginx vhost and php-fpm pool after creating an account in whm
- deleting nginx vhost and php-fpm pool after terminating an account in whm
'''
import os
import sys
import shutil
import fileinput
import re
import subprocess
import json
import argparse  # May need python-argparse package

__author__ = "Ahmed Kamel"
__copyright__ = "Copyright (C) 2015, Ahmed Kamel"
__credits__ = ["Ahmed Kamel"]
__license__ = "Apache"
__version__ = "0.1"
__maintainer__ = "Ahmed Kamel"
__email__ = "k.tricky@gmail.com"
__status__ = "Development"

ngx_vhost_tmpl = '/usr/local/nginx/vhost_tmpl.conf'
ngx_vhost_dir = '/usr/local/nginx/vhosts'
fpm_pool_tmpl = '/usr/local/php-fpm/etc/pool_tmpl.conf'
fpm_pool_dir = '/usr/local/php-fpm/etc/conf.d'
ngx_reload = ['/sbin/service', 'nginx', 'configtest', '&&', '/sbin/service',
              'nginx', 'reload']
fpm_reload = ['/sbin/service', 'php-fpm', 'restart']


def replace(file_name, regex_str, repl):
    """find and replace a regex string on a provided file"""
    for line in fileinput.input(file_name, inplace=1):
        line = re.sub(regex_str, repl, line.rstrip())
        print line


def describe():
    '''describe function to provide info about the hook action code options for
    usr/local/cpanel/bin/manage_hooks utility for more information refer to
    this url https://goo.gl/H9iRBL and https://goo.gl/CZvz8i'''
    print json.dumps([{
        'category': 'Whostmgr',
        'event': 'Accounts::Create',
        'stage': 'post',
        'hook': '/root/bin/cphook.py --createaccount',
        'exectype': 'script'
    },
                      {
                          'category': 'Whostmgr',
                          'event': 'Accounts::Remove',
                          'stage': 'post',
                          'hook': '/root/bin/cphook.py --removeaccount',
                          'exectype': 'script'
                      }, ])


def create_account():
    '''adds nginx and php-fpm config files for created account domain'''
    hook_data = json.loads(sys.stdin.read())['data']
    # data hash/dict returned by cpanel/whm operation
    user = hook_data['user']
    domain = hook_data['domain']
    homedir = hook_data['homedir']
    rootdir = os.path.join(homedir, 'public_html')
    vhost_path = ngx_vhost_dir + '/%s.conf' % domain
    fpm_pool_path = fpm_pool_dir + '/%s.conf' % domain
    shutil.copy(ngx_vhost_tmpl, vhost_path)
    replace(vhost_path, 'DOMAIN', domain)
    replace(vhost_path, 'ROOTDIR', rootdir)
    shutil.copy(fpm_pool_tmpl, fpm_pool_path)
    replace(fpm_pool_path, 'DOMAIN', domain)
    replace(fpm_pool_path, 'ROOTDIR', rootdir)
    replace(fpm_pool_path, 'USER', user)
    subprocess.call(fpm_reload)
    subprocess.call(ngx_reload)
    sys.stdout.write('1')


def remove_account():
    '''removes nginx and php-fpm config files of removed cpanel account'''
    # metadata returned from calling removeaccount func https://goo.gl/zgYgwZ
    hook_data = json.loads(sys.stdin.read())['data']
    user = hook_data['user']
    dom_list = [x.split()[0].strip(':') + '.conf'
                for x in [x for x in open('/tmp/test.txt') if 'wedksac' in x]]
    for f in dom_list:
        os.remove(ngx_vhost_dir + '/%s' % f)
        os.remove(fpm_pool_dir + '/%s' % f)
    subprocess.call(fpm_reload)
    subprocess.call(ngx_reload)
    sys.stdout.write('1')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--describe",
                        action='store_true',
                        help="calls describe function for event")
    parser.add_argument("--createaccount",
                        action='store_true',
                        help="calls createaccount post hook")
    parser.add_argument("--removeaccount",
                        action='store_true',
                        help="calls removeaccount post hook")
    args = parser.parse_args()
    if args.describe:
        describe()
    elif args.createaccount:
        create_account()
    elif args.removeaccount:
        remove_account()


main()
