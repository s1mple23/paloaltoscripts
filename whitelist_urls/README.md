# Palo Alto URL Whitelisting Automation

A pair of scripts to automate the process of discovering blocked URLs in Palo Alto Networks firewalls and whitelisting them—using a Python wrapper and an Ansible playbook.

## Repository Contents

- `whitelist_url.py`  
  Python script that:
  1. Prompts for Change/Ticket number, firewall Host/IP, credentials, search term, VSYS, and URL category.
  2. Queries the PAN‑OS XML API for blocked URL logs.
  3. Invokes the Ansible playbook with the selected parameters.

- `whitelist_url.yml`  
  Ansible playbook that:
  1. Gathers the existing Custom URL Category.
  2. Merges in new URL entries (both root and wildcard).
  3. Commits only if there are changes.
  4. Writes a per‑Change/Ticket log file.

## Prerequisites

1. **Python 3.8+**  
2. **PIP packages** (install via `pip install -r requirements.txt`):
- requests
- pwinput
- urllib3
- ansible
- pan-python


3. **Ansible** (2.9+) with the **Palo Alto Networks PAN‑OS collection**:
   ```bash
   sudo apt install ansible
   pip install ansible
   ansible-galaxy collection install paloaltonetworks.panos

