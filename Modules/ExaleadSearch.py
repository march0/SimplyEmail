# !/usr/bin/env python

# Class will have the following properties:
# 1) name / description
# 2) main name called "ClassName"
# 3) execute function (calls everthing it neeeds)
# 4) places the findings into a queue
import configparser
import requests
import time
import re
import urlparse
import os
from Helpers import helpers
from Helpers import Parser
from bs4 import BeautifulSoup
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

class ClassName:

    def __init__(self, Domain, verbose=False):
        self.name = "Exalead Search for Emails"
        self.description = "Uses Exalead to search for emails and parses them out of the Html"
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.Domain = Domain
            self.Quanity = int(config['ExaleadSearch']['StartQuantity'])
            self.UserAgent = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
            self.Limit = int(config['ExaleadSearch']['QueryLimit'])
            self.Counter = int(config['ExaleadSearch']['QueryStart'])
            self.verbose = verbose
            self.urlList = []
            self.Text = ""
        except:
            print helpers.color("[*] Major Settings for Exalead are missing, EXITING!\n", warning=True)


    def execute(self):
        self.search()
        FinalOutput, HtmlResults = self.get_emails()
        return FinalOutput, HtmlResults


    def search(self):
        while self.Counter <= self.Limit:
            time.sleep(1)
            if self.verbose:
                p = '[*] Exalead Search on page: ' + str(self.Counter)
                print helpers.color(p, firewall=True)
            try:
                url = 'http://www.exalead.com/search/web/results/?q="%40' + self.Domain + '"&elements_per_page=' + \
                      str(self.Quanity) + '&start_index=' + str(self.Counter)
            except Exception as e:
                error = "[!] Major issue with Exalead Search: " + str(e)
                print helpers.color(error, warning=True)
            try:
                r = requests.get(url, headers=self.UserAgent)
            except Exception as e:
                error = "[!] Fail during Request to Exalead (Check Connection):" + str(e)
                print helpers.color(error, warning=True)
            try:
                RawHtml = r.content
                self.Text += RawHtml # sometimes url is broken but exalead search results contain e-mail
                soup = BeautifulSoup(RawHtml)
                self.urlList = [h2.a["href"] for h2 in soup.findAll('h4', class_='media-heading')]
            except Exception as e:
                error = "[!] Fail during parsing result: " + str(e)
                print helpers.color(error, warning=True)
            self.Counter += 30

        # Now take all gathered URL's and gather the Raw content needed
        for Url in self.urlList:
            try:
                data = requests.get(Url, timeout=2)
                self.Text += data.content
            except Exception as e:
                error = "[!] Connection Timed out on Exalead Search:" + str(e)
                print helpers.color(error, warning=True)

        if self.verbose:
            p = '[*] Searching Exalead Complete'
            print helpers.color(p, status=True)

    def get_emails(self):
        Parse = Parser.Parser(self.Text)
        Parse.genericClean()
        Parse.urlClean()
        FinalOutput = Parse.GrepFindEmails()
        HtmlResults = Parse.BuildResults(FinalOutput, self.name)
        return FinalOutput, HtmlResults
