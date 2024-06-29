import requests
from bs4 import BeautifulSoup
import argparse
import json
import time
import random
import logging
from termcolor import colored
from tqdm import tqdm

VERSION = "1.0.0-beta"

class TikGuard:
    def __init__(self, proxies=None):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/json'
        }
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.proxies = proxies if proxies else []

    def switch_proxy(self):
        if self.proxies:
            proxy = random.choice(self.proxies)
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
            logging.info(f"Switched to proxy: {proxy}")

    def get_report_url(self, video_url):
        for attempt in range(self.max_retries):
            try:
                self.switch_proxy()
                response = self.session.get(video_url, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                report_button = soup.find('button', {'class': 'report-button-class'})
                if report_button and 'data-report-url' in report_button.attrs:
                    return report_button['data-report-url']
                
                scripts = soup.find_all('script')
                for script in scripts:
                    if 'reportUrl' in script.text:
                        report_url_start = script.text.find('reportUrl') + len('reportUrl\":\"')
                        report_url_end = script.text.find('\"', report_url_start)
                        return script.text[report_url_start:report_url_end]
                        
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching video page: {e}, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        return None

    def submit_report(self, report_url, reason):
        payload = {
            'reason': reason,
            'additional_info': 'Spam or inappropriate content'
        }
        for attempt in range(self.max_retries):
            try:
                self.switch_proxy()
                response = self.session.post(report_url, json=payload, headers=self.headers)
                response.raise_for_status()
                return "Report submitted successfully!"
            except requests.exceptions.RequestException as e:
                logging.error(f"Error submitting report: {e}, retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        return "Failed to submit report."

    def login(self, username, password):
        login_url = 'https://www.tiktok.com/login'
        payload = {
            'username': username,
            'password': password
        }
        try:
            response = self.session.post(login_url, json=payload, headers=self.headers)
            response.raise_for_status()
            print("Logged in successfully!")
        except requests.exceptions.RequestException as e:
            print(f"Error logging in: {e}")

def print_logo():
    logo = """
████████╗██╗██╗  ██╗ ██████╗ ██╗   ██╗ ██████╗  █████╗ ██████╗ 
╚══██╔══╝██║██║  ██║██╔═══██╗██║   ██║██╔════╝ ██╔══██╗██╔══██╗
   ██║   ██║███████║██║   ██║██║   ██║██║  ███╗███████║██████╔╝
   ██║   ██║██╔══██║██║   ██║██║   ██║██║   ██║██╔══██║██╔═══╝ 
   ██║   ██║██║  ██║╚██████╔╝╚██████╔╝╚██████╔╝██║  ██║██║     
   ╚═╝   ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝     
    """
    print(colored(logo, 'cyan'))
    print(colored(f"Version: {VERSION}", 'green'))

def print_help():
    help_text = """
Usage: TikGuard [options]

Options:
  --username USERNAME     TikTok username for login
  --password PASSWORD     TikTok password for login
  --proxy PROXY           Proxy server (e.g., http://proxyserver:port)
  --proxies-file FILE     File containing a list of proxy servers
  video_url               URL of the TikTok video to report
  reason                  Reason for reporting the video

Examples:
  TikGuard https://www.tiktok.com/@user/video/1234567890 Spam
  TikGuard --username user --password pass https://www.tiktok.com/@user/video/1234567890 Inappropriate
"""
    print(help_text)

def main():
    parser = argparse.ArgumentParser(description="TikGuard - TikTok Reporting Tool")
    parser.add_argument('video_url', help='URL of the TikTok video to report')
    parser.add_argument('reason', help='Reason for reporting the video')
    parser.add_argument('--username', help='TikTok username for login', default=None)
    parser.add_argument('--password', help='TikTok password for login', default=None)
    parser.add_argument('--proxy', help='Proxy server (e.g., http://proxyserver:port)', default=None)
    parser.add_argument('--proxies-file', help='File containing a list of proxy servers', default=None)
    parser.add_argument('--help', action='store_true', help='Show this help message and exit')

    args = parser.parse_args()

    if args.help:
        print_help()
        return

    proxies = []
    if args.proxy:
        proxies.append(args.proxy)
    if args.proxies_file:
        with open(args.proxies_file, 'r') as file:
            proxies.extend([line.strip() for line in file])

    print_logo()
    
    reporter = TikGuard(proxies=proxies)

    if args.username and args.password:
        reporter.login(args.username, args.password)

    report_url = reporter.get_report_url(args.video_url)
    if report_url:
        with tqdm(total=100, desc="Submitting report", ncols=100) as pbar:
            result = reporter.submit_report(report_url, args.reason)
            for i in range(100):
                time.sleep(0.01)
                pbar.update(1)
            print(result)
    else:
        print("Failed to find report URL.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
