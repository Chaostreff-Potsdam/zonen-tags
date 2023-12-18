# A simple Website to generate and upload images to the Chaos#Zonen-Tags

## Getting Started

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirement.txt
flask --app tag_configurator.app run --port 8000 --host 0.0.0.0
~~~

## Config

You can configure the IP of the AP you want to use in `config.toml`.

~~~toml
AP_IP = "1.2.3.4"
~~~

Alternatively you can set the environment variable `FLASK_AP_IP`.

~~~bash
FLASK_AP_IP=1.2.3.4 flask --app tag_configurator.app run --port 8000 --host 0.0.0.0  
~~~
