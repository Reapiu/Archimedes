# Archimedes 2.0, written by Reapiu (AKA John Floyd) in April 28 & 29, 2024.

import requests
import argparse
import tls_client
import httpx
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

capkey = None
invite = None
proxies = None

def solve_2captcha(capkey, site_key, page_url):
	capkey = config['captcha_key']
	time_start = time.time()
	url = "https://2captcha.com/in.php?key={}&method=hcaptcha&sitekey={}&pageurl={}".format(capkey,site_key,page_url)
	response = httpx.get(url)
	if response.text[0:2] == 'OK':
		captcha_id = response.text[3:]
		url = "http://2captcha.com/res.php?key={}&action=get&id={}".format(capkey,captcha_id)
		response = httpx.get(url)
		while 'CAPCHA_NOT_READY' in response.text:
			time.sleep(5)
			response = httpx.get(url)
			print(response.text)
		print(response.text)
		return response.text.replace('OK|','') , str(time.time() - time_start)
	else:
		print('Captcha solving error ({})!'.format(response.text))
		return False

def solve_capmonster(capkey, site_key, page_url):
	url = "https://api.capmonster.cloud/createTask"
	data = {
		"clientKey": capkey,
		"task":
		{
			"type": "HCaptchaTaskProxyless",
			"websiteURL": page_url,
			"websiteKey": site_key
		}
	}
	response = httpx.post(url,json=data)
	if response.json()['errorId'] == 0:
		task_id = response.json()['taskId']
		url = "https://api.capmonster.cloud/getTaskResult"
		data = {
			"clientKey": capkey,
			"taskId": task_id
		}
		response = httpx.post(url,json=data)
		while response.json()['status'] == 'processing':
			time.sleep(3)
			response = httpx.post(url,json=data)
		return response.json()['solution']['gRecaptchaResponse']
	else:
		print('Captcha solving error ({})!'.format(response.json()['errorDescription']))
		return False

def check_proxy(proxy):
	try:
		response = requests.get("http://discord.com/", proxies={"http": proxy}, timeout=5)
		if response.status_code == 200:
			return proxy
	except Exception as e:
		return None

def main():
	argument_parser = argparse.ArgumentParser(description="The most handy Discord account generator!")

	argument_parser.add_argument("--capkey", type=str, help="The key to the CAPTCHA solving service.")
	argument_parser.add_argument("--invite", type=str, help="The invite link of the server to join after creating the account.")
	argument_parser.add_argument("--proxies", type=str, help="The path to the file containing all of the proxies.")

	arguments = argument_parser.parse_args()

	capkey = str(arguments.capkey)
	invite = str(arguments.invite)
	proxies = str(arguments.proxies)

	with open(arguments.proxies, 'r') as file:
		proxies = file.readlines()
		proxies = [proxy.strip() for proxy in proxies]

	print("Checking proxies...")

	working_proxies = []
	with ThreadPoolExecutor(max_workers=50) as executor:
		with tqdm(total=len(proxies)) as pbar:
			results = executor.map(check_proxy, proxies)
			for result in results:
				pbar.update(1)
				if result:
					working_proxies.append(result)

	print(f"Found {len(working_proxies)} working proxies.")

	proxies = working_proxies

	session = tls_client.Session(client_identifier="safari_ios_16_0")

	while True:
		try:
			fingerprint = None

			proxy = random.choice(proxies)

			ip, port = proxy.split(":")
			proxy = f"http://{ip}:{port}"

			session.proxies = {"http": proxy, "https": proxy}

			headers = {'Accept': '*/*', 'Accept-Language': 'es-ES,es;q=0.9', 'Connection': 'keep-alive', 'Referer': 'https://discord.com/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'Sec-GPC': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36', 'X-Track': 'eyJvcyI6IklPUyIsImJyb3dzZXIiOiJTYWZlIiwic3lzdGVtX2xvY2FsZSI6ImVuLUdCIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKElQaG9uZTsgQ1BVIEludGVybmFsIFByb2R1Y3RzIFN0b3JlLCBhcHBsaWNhdGlvbi8yMDUuMS4xNSAoS0hUTUwpIFZlcnNpb24vMTUuMCBNb2JpbGUvMTVFMjQ4IFNhZmFyaS82MDQuMSIsImJyb3dzZXJfdmVyc2lvbiI6IjE1LjAiLCJvc192IjoiIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfZG9tYWluX2Nvb2tpZSI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjk5OTksImNsaWVudF9ldmVudF9zb3VyY2UiOiJzdGFibGUiLCJjbGllbnRfZXZlbnRfc291cmNlIjoic3RhYmxlIn0'}

			response = session.get('https://discord.com/api/v9/experiments', headers=headers)
			if response.status_code == 200:
				data = response.json()
				fingerprint = data["fingerprint"]
				print(f"Obtained fingerprint {fingerprint}!")
			else:
				print("Failed to obtain fingerprint...")

			cap = solve_capmonster(capkey, site_key='4c672d35-0701-42b2-88c3-78380b0db560', page_url='https://discord.com/')

			payload = {'consent': True, 'global_name': "Ronnie McFloyd", 'unique_username_registration': True, 'fingerprint': fingerprint, 'captcha_key': cap, 'invite': invite}

			headers = {'authority': 'discord.com', 'accept': '*/*', 'accept-language': 'es-ES,es;q=0.9', 'referer': 'https://discord.com/', 'origin': 'https://discord.com', 'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Brave";v="114"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin', 'sec-gpc': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36', 'x-track': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImZyLUZSIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzExNC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTE0LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjk5OTksImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9', 'x-fingerprint': fingerprint}

			response = session.post('https://discord.com/api/v9/auth/register', headers=headers, json=payload)

			if "token" not in response.text:
				if "retry_after" in response.text:
					print("Could not generate token due to ratelimit.")
			token = response.json().get('token')
			if token == None:
				print("Token failed to generate, token not found!")
			else:
				with open("tokens.txt", "w", encoding='utf-8') as f:
					f.write(token + "\n")
				print(f"Successfully generated token {token}!")
		except Exception as e:
			print(f"Encountered exception ({str(e)})!")

if __name__ == "__main__":
	main()