## OTM
This is a one time message delivery application.  
You can generate your own secret message by making a POST request to this url.  
In the request body submit a valid json containing the message.  
Eg:  
```
    curl -XPOST -d '{"message":"This is your secret message!"}' https:/<YOUR_URL>/
```
You will recive you uniq_link in the responce body.

Eg:
```json
    $ curl -s -XPOST -d '{"message":"This is your secret message!"}' https://<YOUR_URL> | jq
    {
      "status": "Success",
      "message": {
        "link": "https://<YOUR_URL>?link=3a2669a5df9add71aa79469e3194a68ebf4848c8a9bfafd1db0f3056f58b7c41",
        "key": "3a2669a5df9add71aa79469e3194a68ebf4848c8a9bfafd1db0f3056f58b7c41"
      }
    }
```

## Disclaimer:
This is a proof of concept app that was created to help define a requirement.  
It is NOT intendet for production use!  


## Installation
Clone this repo and install dependencies.  

```
git clone https://github.com/gbyx3/otm
cd otm
python3 -m venv enviroment-name
source ./enviroment-name/bin/activate
pip -r requirements.txt
python3 app.py
```

## Requirements
- ptyhon3
- redis


