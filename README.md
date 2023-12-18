# A simple Website to generate and upload images to the Chaos#Zonen-Tags

This is a simple website to generate and upload images to [Open EPaper Link Access Point](https://openepaperlink.de).

## Getting Started

### Prerequisites

* [Python 3.11+](https://www.python.org)
* [Git LFS](https://git-lfs.com) installed (for the images)

### Installing

~~~bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
~~~

### Running

~~~bash
flask --app tag_configurator.app run --port 8000 --host 0.0.0.0
~~~

## Configuration

Before running the server for the first time, you have to configure the IP address of the Open EPaper Link access point.
There are two ways to do this.

### 1. Using the config file

* Copy the `config.toml.example` file to `config.toml`
* Open the `config.toml` file in a text editor
* Set the `AP_IP` variable to the IP address of the access point

~~~toml
AP_IP = "1.2.3.4"
~~~

### 2. Using an environment variable

Alternatively you can set the environment variable `FLASK_AP_IP` either using `export FLASK_AP_IP=1.2.3.4` or when
starting the server:

~~~bash
FLASK_AP_IP=1.2.3.4 flask --app tag_configurator.app run --port 8000 --host 0.0.0.0  
~~~
