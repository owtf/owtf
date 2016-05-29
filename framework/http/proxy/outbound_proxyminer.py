#!/usr/bin/env python
'''
Proxy Miner developed by Marios Kourtesis <name.surname@gmail.com>

The code is Structured in 3 parts
A)Miner Engine
B)Helper Functions
C)Proxy Mining Functions

'''

import urllib2
from bs4 import BeautifulSoup
import re
import itertools
import os
from tornado.httpclient import HTTPRequest, HTTPClient
from tornado.httputil import HTTPHeaders
from tornado.httpclient import HTTPError


#---------------------------------MINER-ENGINE---------------------------------
class Proxy_Miner:

    User_agent = "Mozilla/5.0 (X11; Linux i686; rv:22.0) Gecko/20100101 Firefox/22.0"

    def start_miner(self):
        Proxies = []
        #Websites List contains as first element a "pointer" to the mining
        #function and as second element the site name.
        Websites = [
                    [self.proxylisty, "www.proxylisty.com"],
                    [self.samair, "http://samair.ru"],
                    [self.sites_google_site_proxyfree4u, "https://sites.google.com/site/proxyfree4u"],
                    [self.idcloak, "http://www.idcloak.com"],
                   ]
        #Fetching Data by calling the mining functions
        print "[#] Proxy Miner has started"
        for i in range(0, len(Websites)):
            print "[#] Fetching data from : " + Websites[i][1]
            try:
                Proxies += Websites[i][0]()
            except Exception as error:
                print "Please Report this information to OWTF community!!!\n" + \
                      "Mining Proxies Data from : " + Websites[i][1] + " Failed!\n" + \
                      "*****************************************************\n" + \
                      "                     Exception                     \n" + \
                      str(error) + "\nFetching data from " + Websites[i][1] + " Skipped\n" + \
                      "*****************************************************\n"

        print "[#] Fetching Done"

        if os.path.isfile(os.path.expanduser("~/.owtf/proxy_miner/proxies.txt")):
            print "[#] Previous proxies Found.\n[#] Merging..."
            previous_proxies = self.load_proxy_list("proxies.txt")
            Proxies += previous_proxies
        Proxies = self.remove_double_entries(Proxies)

        print "Total Proxies : " + str(len(Proxies))

        return Proxies

#----------------------------------HELPER-FUNCTIONS----------------------------
    #check's if the proxy data(ip:port) are valid
    def check_proxy(self, proxy):
        ValidIpAddressRegex = "(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]|[1-9])\.((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){2}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[1-9])"
        try:
            port = int(proxy[1])
        except:
            return False
        if port < 0 or port > 65536:
            return False
        if re.match(ValidIpAddressRegex, proxy[0]) == None:
            return False
        return True

    def load_proxy_list(self, filename):
        path = os.path.join(os.path.expanduser("~/.owtf/proxy_miner/"), filename)
        file_handle = open(path, "r")
        proxies = []
        file_buf = file_handle.read()
        lines = file_buf.split("\n")
        for line in lines:
            if str(line).strip() != "":
                proxies.append(line.split(":"))
        return proxies

    def export_proxies_to_file(self, filename, proxies):
        path = os.path.expanduser("~/.owtf/proxy_miner/")
        print path
        if not os.path.exists(path):
            #print "Creating path"
            os.makedirs(path)
        fh = open(os.path.join(path, filename), 'w+')
        for i in range(0, len(proxies)):
            fh.write(proxies[i][0] + ":" + proxies[i][1] + "\n")
            # fh.write(str(proxies[i]) + "\n")
        fh.close()

    def getpage(self, url):
        response = urllib2.urlopen(url)
        return response.read()

    #some pages check the user-agent string
    def getpage_with_user_agent(self, url):
        headers = {'User-Agent': Proxy_Miner.User_agent}
        req = urllib2.Request(url, None, headers)
        return urllib2.urlopen(req).read()

    #  removes double entries and sort's the proxy list
    def remove_double_entries(self, proxies):
        proxies.sort(key=lambda x: (
                                    int(x[0].split(".")[0]),
                                    int(x[0].split(".")[1]),
                                    int(x[0].split(".")[2]),
                                    int(x[0].split(".")[3]),
                                    int(x[1])
                                    )
                     )
        return list(proxies for proxies, _ in itertools.groupby(proxies))

#----------------------------PROXY-MINING-FUNCTIONS-------------------------
#Mining Function returns list of proxies.

    # http://samair.ru/proxy/proxy-84.htm
    def samair(self):
        proxies = []
        for counter in range(1, 31): # fetch 30 pages
            if counter < 10:
                pn = "0" + str(counter)
            else:
                pn = str(counter)
            # extracting proxies
            page = BeautifulSoup(self.getpage("http://samair.ru/proxy/proxy-" + pn + ".htm"))
            link = "http://samair.ru" + page.find("a", text="these proxies in IP:Port format only").get("href")
            # print(link)
            proxy_page = BeautifulSoup(self.getpage(link))
            ip_addrs = proxy_page.find("div", id="content").text
            # print ip_addrs
            d_list = ip_addrs.split("\n")
            for row in d_list:
                proxy = str(row).split(":")
                if len(proxy) == 2:  # number of elements
                    # row.append("http")
                    if(self.check_proxy(proxy)):
                        proxies.append(proxy)
            counter = counter + 1
        return proxies

    # http://www.proxylisty.com/
    def proxylisty(self):
        proxies = []
        for i in range(1, 14):  # Fetch 13 pages
            page = BeautifulSoup(self.getpage_with_user_agent("http://www.proxylisty.com/ip-proxylist-" + str(i)))
            # print i

            d_list = page.find_all("tr")
            d_list = d_list[2:-2]
            for raw_data in d_list:
                text = raw_data.get_text()
                tmp = text.split("\n")
                p = []
                # for i in range(1, 4): #append proxy type
                for i in range(1, 3):
                    p.append(str(tmp[i]))
                    if self.check_proxy(p):
                        proxies.append(p)
        return proxies

    # http://www.idcloak.com/proxylist/free-proxy-ip-list.html#sort
    def idcloak(self):
        proxies = []
        url = "http://www.idcloak.com/proxylist/free-proxy-ip-list.html"
        #getting live updated proxies
        page = BeautifulSoup(self.getpage(url))
        # print page.find("div",id="torefresh")
        page = page.find("div", id="torefresh")
        data_list = page.find_all("tr")
        data_list = data_list[1:]
        for raw_data in data_list:
            # print raw_data

            # parsing the data
            soup = BeautifulSoup(str(raw_data))
            # </td><td>3128</td><td>222.83.14.142</td></tr>
            raw_proxy = soup.findAll("td")
            proxy = [str(raw_proxy[-1])[4:-5], str(raw_proxy[-2])[4:-5]]
            if self.check_proxy(proxy):
                proxies.append(proxy)
        page_num = 1
        http_client = HTTPClient()
        while True:  # loop until last page
            post_data = "port%5B%5D=all&protocol-http=true" + \
            "&protocol-https=true&anonymity-low=true&anonymity-medium=true" + \
            "&anonymity-high=true&connection-low=true&connection-medium=true" + \
            "&connection-high=true&speed-low=true&speed-medium=true" + \
            "&speed-high=true&order=desc&by=updated&page=" + str(page_num)

            request = HTTPRequest(
                                  url=url,
                                  connect_timeout=30,
                                  request_timeout=30,
                                  follow_redirects=False,
                                  use_gzip=True,
                                  user_agent=Proxy_Miner.User_agent,
                                  method="POST",
                                  body=post_data
                                  )

            try:
                response = http_client.fetch(request)
            except Exception as e:
                print e
                pass
            #print response
            #parsing the data
            page = BeautifulSoup(response.body)
            page = page.find("table", id="sort")
            data_list = page.find_all("tr")
            data_list = data_list[1:]
            for raw_data in data_list:
                # print raw_data
                soup = BeautifulSoup(str(raw_data))
                raw_proxy = soup.findAll("td")
                proxy = [str(raw_proxy[-1])[4:-5], str(raw_proxy[-2])[4:-5]]
                if self.check_proxy(proxy):
                    proxies.append(proxy)
            # if the following pattern don't exists you are in the last page
            if response.body.find(" name=\"page\" value=\"" + str(page_num + 1)) == -1:
                break
            page_num += 1
        return proxies

    # https://sites.google.com/site/proxyfree4u/
    def sites_google_site_proxyfree4u(self):
        proxies = []
        url = "https://sites.google.com/site/proxyfree4u/proxy-list?offset="
        # fetch the latest 10 pages
        for i in range(0, 100, 10):
            # print url + str(i)
            soup = BeautifulSoup(self.getpage(url + str(i)))
            http_client = HTTPClient()
            for link in soup.find_all('a'):
                fetch_url = link.get('href')
                #get the correct URL
                if fetch_url == None:
                    continue
                if fetch_url.find("&single=true&gid=0&output=txt") != -1:
                    request = HTTPRequest(
                                          url=fetch_url,
                                          connect_timeout=30,
                                          request_timeout=30,
                                          follow_redirects=False,
                                          use_gzip=True,
                                          user_agent=Proxy_Miner.User_agent
                                          )
                    #  sometime during tests the response was 599.
                    #  re-sending the packet 4 times
                    for times in range(0, 4):
                        try:
                            response = http_client.fetch(request)
                        except HTTPError as e:
                            if e.code in [408, 599]:
                                continue
                        #getting the cookies. In order to get the proxy list 2 cookies are needed
                        first_redirect = e.response.headers['Location']
                        cookie = e.response.headers['Set-Cookie']
                        cookie_headers = HTTPHeaders()
                        cookie_headers.add("Cookie", cookie.split(";")[0])
                        req2 = HTTPRequest(
                                           url=first_redirect,
                                           connect_timeout=30.0,
                                           request_timeout=30.0,
                                           follow_redirects=False,
                                           use_gzip=True,
                                           headers=cookie_headers,
                                           user_agent=Proxy_Miner.User_agent
                                           )
                        try:
                            http_client.fetch(req2)
                        except HTTPError as e2:
                            second_redirect = e2.response.headers['Location']
                            # get the second cookie
                            cookie2 = e2.response.headers['Set-Cookie']
                            cookie_headers.add("Cookie", cookie2.split(";")[0])
                            req3 = HTTPRequest(
                                               url=second_redirect,
                                               connect_timeout=30.0,
                                               request_timeout=30.0,
                                               follow_redirects=True,
                                               use_gzip=True,
                                               headers=cookie_headers,
                                               user_agent=Proxy_Miner.User_agent
                                               )
                            resp3 = http_client.fetch(req3)
                            # print resp3.body
                            lines = resp3.body.split("\n")
                            counter = 0
                            for j in range(1, len(lines)):
                                proxy = lines[j].split(":")
                                if self.check_proxy(proxy):
                                    proxies.append(proxy)
                                # if the list contains non valid proxies
                                else:
                                    counter += 1
                                    if counter == 15:
                                        break
                        break

        return proxies
#---------------------------------------------------------------
