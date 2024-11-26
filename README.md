# Proxmox-Confluence Poster (pve_confluence_poster)
Service that creates VM table from Proxmox API, posts it at Confluence page and regularly updates it.

### Configuration

Script gets its parameters from config.yml:
```
proxmox:
  url: 'proxmox_url_value'                   # Proxmox URL, e.g. 'https://pve-01.acme.com:8005'
  token_id: 'proxmox_token_id_value'         # Proxmox token ID, e.g. 'service_user@pve!pve_confluence_poster'. Generate it in user settings section and make sure it has full access to VM info.
  token_secret: 'proxmox_token_secret_value' # Proxmox token secret, e.g. '8e42ee73-579e-e440-8782-8c10c097f403'. You will get it along with previous value.

confluence:
  url: 'confluence_url_value'                # Confluence URL, e.g. 'https://confluence.acme.com'
  token: 'confluence_token_value'            # Confluence token, e.g. 'NT9SXNu1k3fhIfqhq6HOtpxu+MfwszNzM3OpA'. Generate it in user settings section.
  page_id: 'confluence_page_id_value'        # Confluence page id, e.g. '348884789'. You can find it in the end of your page's URL.
  ```

If you need to change update interval, just update:
```
time.sleep(60) # 60 seconds by default
```
at the end of main .py file.

  ### Building and running
  0. Make sure you filled configuration file.
  1. Clone this repository:
  ```
  git clone https://github.com/borisovpavel29/proxmox-confluence-poster.git
  ```
  2. Build and start service with Docker:
  ```
  docker build ./proxmox-confluence-poster -t proxmox-confluence-poster:latest

  docker run -d proxmox-confluence-poster:latest
  ```
Docker Compose:
  ```
  cd proxmox-confluence-poster
  docker compose build
  docker compose up -d
  ```
or any other way you want.