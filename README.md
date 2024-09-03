# OTM - One Time Message

## Description

This is a simple one time message delivery application. You can generate a secret message and share it with recipients. The message will expire after a set time.

### Features

* Generate a secret message
* Use your own salt to generate the secret message
* Retrieve a secret message
* Message expire after first read
* Message expire after a set time

## Getting Started

### Requirements

Following are the requirements for this application:

* Python3 and pip
* Redis server

### Installation

Clone this repo and install dependencies.

```sh
# Clone otms repo
git clone https://github.com/axians/otm
cd otm

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source ./venv/bin/activate

# Install dependencies
pip install --require-virtualenv --requirement requirements.txt

# Checkout the latest release
git checkout 1.0.0

# Run the application
python3 app.py
```

## Usage

The application can either be used interactivly or via API. To use the API make a POST request to the application with a valid json containing the message.

JSON format:

```json
{
  "message": "This is the message", // Required
  "salt": "YourCustomSalt", // Optional, if not provided a static salt will be used
  "ttl": 3600 // Optional, default 3600
}
```

Example:

```text
curl -s -XPOST -d '{"message":"This is your secret message!", "salt":"YourCustomSalt", "ttl":"3600"}' https://your.url.tld/
```

Output:

```json
{
  "status": "Success",
  "message": {
    "link": "https://your.url.tld?link=12345678901234567890",
    "key": "12345678901234567890",
    "salt":"<hash('YourCustomSalt')>"
  }
}
```
