![](static/tripolis.png)

---

# Real portal Tripolis

![](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=Selenium&logoColor=white)
![](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

Real portal Brf Tripolis is a scraping service that collects sales information about apartments for Brf Tripolis.
It collects information about **all apartments sold** and **all listed apartments** and shares this information via email, where the raw data
is attached as Excel files and a Bokeh plot summarizing average prices per year.

## Usage

Make sure that the `config.ini` file is placed in top level directory and has the following structure
```yaml
[abj_portal]
login_url = https://abjbo.realportal.nu/
# the scrape_url is missing the last pageno=NUMBER this is passed in the script
scrape_url = https://abjbo.realportal.nu/common/portal.php?menuid=103&pageid=108&from=1970-04-05&tom=2023-01-09&bolagsid=175&template=bootstrap&pageno=
username = 12345
password = ABCDEF

# Only used if run local
[selenium]
local_executable_path = absolute-path-to-local-chromedriver

[mail]
from_address=i_send_things@mail.com
from_address_pw=secret-pw
to_address=i_receive_things@mail.com

[booli]
api_caller=Api Caller Name
api_key=SecretApiKey
```

Run with docker-compose
```bash
docker-compose -f docker-compose.yml up --abort-on-container-exit
```
