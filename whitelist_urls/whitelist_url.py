import subprocess
import requests
import pwinput
import urllib3
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_api_key(firewall_host, username, password):
    url = f"{firewall_host}/api/?type=keygen&user={username}&password={password}"
    resp = requests.get(url, verify=False)
    if resp.status_code == 200 and "<key>" in resp.text:
        return resp.text.split("<key>")[1].split("</key>")[0]
    return None

def get_vsys_list(firewall_host, api_key):
    xpath = "/config/devices/entry/vsys"
    params = {'type': 'config', 'action': 'get', 'xpath': xpath, 'key': api_key}
    resp = requests.get(f"{firewall_host}/api/", params=params, verify=False)
    if resp.status_code != 200:
        print("[ERROR] Failed to retrieve VSYS list.")
        return []
    try:
        root = ET.fromstring(resp.text)
        vsys_parent = root.find('.//vsys')
        if vsys_parent is None:
            return []
        return [e.attrib['name'] for e in vsys_parent.findall('entry')]
    except Exception as e:
        print(f"[ERROR] Parsing VSYS list failed: {e}")
        return []

def extract_blocked_urls(firewall_host, api_key, snippet):
    print(f"[INFO] Searching for blocked URLs matching: {snippet}")
    params = {
        'type': 'log',
        'log-type': 'url',
        'query': f'(url contains "{snippet}") and ((action eq block-continue) or (action eq block-url))',
        'nlogs': '50',
        'key': api_key
    }
    resp = requests.get(f"{firewall_host}/api/", params=params, verify=False)
    if resp.status_code != 200:
        print("[ERROR] Log query failed.")
        return []
    try:
        root = ET.fromstring(resp.text)
        job = root.findtext('.//job')
    except Exception as e:
        print(f"[ERROR] XML parsing error: {e}")
        return []
    if not job:
        print("[ERROR] No job ID received.")
        return []
    for _ in range(10):
        time.sleep(2)
        rp = {'type':'log','action':'get','job-id':job,'key':api_key}
        r = requests.get(f"{firewall_host}/api/", params=rp, verify=False)
        if r.status_code != 200:
            continue
        try:
            rroot = ET.fromstring(r.text)
            domains = set()
            for entry in rroot.findall(".//entry"):
                misc = entry.findtext("misc") or ""
                urlc = misc.strip()
                if not urlc:
                    continue
                if not urlc.startswith("http"):
                    urlc = "https://" + urlc
                host = urlparse(urlc).netloc or urlparse(urlc).path.split("/")[0]
                if host:
                    domains.add(host.lower())
            return sorted(domains)
        except Exception as e:
            print(f"[ERROR] Parsing error: {e}")
            continue
    print("[INFO] No matching logs found.")
    return []

def list_categories(firewall_host, api_key, vsys):
    if vsys == "shared":
        xpath = "/config/shared/profiles/custom-url-category"
    else:
        xpath = f"/config/devices/entry/vsys/entry[@name='{vsys}']/profiles/custom-url-category"
    params = {'type':'config','action':'get','xpath':xpath,'key':api_key}
    resp = requests.get(f"{firewall_host}/api/", params=params, verify=False)
    if resp.status_code != 200:
        print("[ERROR] Failed to load categories.")
        return []
    root = ET.fromstring(resp.text)
    return [e.attrib['name'] for e in root.findall(".//entry")]

def main():
    print("==== Palo Alto URL Whitelisting Tool ====")
    change_id = input("Change/Ticket number: ").strip()
    host_in = input("Firewall hostname or IP (e.g., 10.10.10.10): ").strip()
    fw = host_in if host_in.startswith("http") else f"https://{host_in}"
    user = input("Username: ").strip()
    pwd = pwinput.pwinput("Password: ", mask="*").strip()
    term = input("Search term (e.g., apple or apple.com): ").strip()

    print("\n[INFO] Logging in...")
    key = get_api_key(fw, user, pwd)
    if not key:
        print("[ERROR] Login failed.")
        return

    vsys_list = get_vsys_list(fw, key)
    vsys_list.append("shared")
    if vsys_list:
        print("\nAvailable VSYS:")
        for idx, v in enumerate(vsys_list, 1):
            print(f"[{idx}] {v}")
        sel = input("→ Select VSYS (number): ").strip()
        try:
            vsys = vsys_list[int(sel) - 1]
        except:
            print("[ERROR] Invalid selection, defaulting to 'vsys1'.")
            vsys = "vsys1"
    else:
        print("[INFO] No VSYS found, defaulting to 'vsys1'.")
        vsys = "vsys1"

    domains = extract_blocked_urls(fw, key, term)
    if not domains:
        print("[INFO] No blocked domains found.")
        return
    print("\nBlocked Domains:")
    for i, d in enumerate(domains, 1):
        print(f"[{i}] {d}")
    sel = input("→ Select (e.g. 1,2 or * for all): ").strip()
    if sel == "*":
        chosen = domains
    else:
        try:
            idxs = [int(x)-1 for x in sel.split(",")]
            chosen = [domains[i] for i in idxs if 0 <= i < len(domains)]
        except:
            print("[ERROR] Invalid input.")
            return

    cats = list_categories(fw, key, vsys)
    if not cats:
        print("[ERROR] No categories found.")
        return
    print("\nAvailable Categories:")
    for i, c in enumerate(cats, 1):
        print(f"[{i}] {c}")
    sel = input("→ Select category (number): ").strip()
    try:
        category = cats[int(sel) - 1]
    except:
        print("[ERROR] Invalid category.")
        return

    url_args = ",".join(chosen)
    cmd = [
        "ansible-playbook", "whitelist_url.yml",
        "--extra-vars",
        f"change_id={change_id} ip_address={fw.replace('https://','')} username={user} password={pwd}"
        f" target_url_list='{url_args}' selected_category={category} vsys={vsys}"
    ]

    #print("\n[DEBUG] Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("[ERROR] Ansible playbook failed with exit code", e.returncode)

if __name__ == "__main__":
    main()
