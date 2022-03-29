import bottle
import redis
import settings
import logging
import json
import time
import hashlib
import uuid
import string
app = application = bottle.default_app()


def rate(fn):
    def _wrap(*args, **kwargs):
        ip = bottle.request.environ.get(settings.http_ip_field)
        try:
            r = connect(settings.ratelimit_db)
        except:
            generic_message = 'There was a problem communicating with the database.'
            bottle.response.status = 500
            if bottle.request.method == 'GET':
                return bottle.template('error.html', generic_message=generic_message, message=False)
            else:
                return {'status':'Failure', 'error':[generic_message]}
        try:
            attempts = r.get(ip)
            if not attempts:
                attempts = bytes([0])
        except Exception as e:
            generic_message = 'There was a problem '
            bottle.response.status = 500
            if bottle.request.method == 'GET':
                return bottle.template('error.html', generic_message=generic_message, message=False)
            else:
                return {'status':'Failure', 'error':[generic_message]}
        attempts = bytes_to_int(attempts)
        attempts += 1
        r.setex(ip, 5, int_to_bytes(attempts))
        if attempts > 10 :
            generic_message = 'You have been temporarily banned due to excessive requests'
            message = 'If you feel like this is/was a misstake please contact the system owner.'
            r.setex(ip, 86400, int_to_bytes(attempts))
            bottle.response.status = 429
            if bottle.request.method == 'GET':
                return bottle.template('error.html', generic_message=generic_message, message=message)
            else:
                return {'status':'Failure', 'error':[generic_message]}
        return fn(*args, **kwargs)
    return _wrap


def bytes_to_int(b):
    return (int.from_bytes(b, "big"))


def int_to_bytes(i):
    return (bytes([i]))


def connect(db=settings.db):
    return redis.StrictRedis(settings.redis_host, port=settings.redis_port, db=db, password=settings.redis_pass)


def update_redis(key, message, ttl=3600):
  r = connect()
  h = r.setex(key, ttl, message)
  return h


def generate_key():
    return hashlib.sha256(f'{str(uuid.uuid4())} - {str(time.time())}'.encode()).hexdigest()


def validate_message(message):
    if any(c in settings.bad_chars for c in message):
        return False
    return True


def validate_link(link):
    if link in ['hello']:
        return True
    if len(link) != 64:
        return False
    if any(i not in string.ascii_letters and i not in string.digits for i in link):
        return False
    return True


@bottle.route("/:why")
@rate
def catchall(why):
    generic_message = 'Ops'
    message = f'''
If you got here you have successfully by bassed the WAF (If implemented).
Please contact the system owner and inform them that "{why}" casued this to happend

If you feel like no external WAF is implemented please stop FUZZing the application.
'''
    bottle.response.status = 400
    return bottle.template('error.html', generic_message=generic_message, message=message)


@bottle.post('/')
@rate
def add_message():
    try:
        byte = bottle.request.body
        data = json.loads(byte.read().decode('UTF-8'))
        message = data['message']
    except:
        bottle.response.status = 400
        return {'status':'Failure', 'error':['Wrong input parameters']}
    if not validate_message(message):
        bottle.response.status = 400
        return {'status':'Failure', 'error':['Bad charachters in payload']}
    try:
        r = connect()
    except:
        bottle.response.status = 500
        return {'status':'Failure', 'error':['There was a problem communicating with the database']}
    key = generate_key()
    if update_redis(key, message):
        bottle.response.status = 200
        return {'status':'Success', 'message':{'link':f'{settings.uri}/?link={key}', 'key':key}}
    else:
        bottle.response.status = 500
        return {'status':'Failure', 'error':['Failed to store message in database']}


@bottle.get('/')
@rate
def display_message():
    generic_message = 'Welcome'
    message = f'''
This is a one time message delivery application.
You can generate your own secret message by making a POST request to this url.
In the request body submit a valid json containing the message.
Eg:
    curl -XPOST -d '{{"message":"This is your secret message!"}}' {settings.uri}

You will recive you unique link in the response body.

Eg:
    curl -s -XPOST -d '{{"message":"This is your secret message!"}}' {settings.uri} | jq
    {{
      "status": "Success",
      "message": {{
        "link": "{settings.uri}?link=3a2669a5df9add71aa79469e3194a68ebf4848c8a9bfafd1db0f3056f58b7c41",
        "key": "3a2669a5df9add71aa79469e3194a68ebf4848c8a9bfafd1db0f3056f58b7c41"
      }} 
    }}

Disclaimer:
This is a proof of concept app that was created to help define a requirement.
It is NOT intendet for production use!

Causion:
There is a rate-limiter in place.
    '''
    link = bottle.request.query.link
    if not link:
        bottle.response.status = 200
        return bottle.template('index.html', generic_message=generic_message, message=message)
    if not validate_link(link):
        generic_message = 'The link you have provided is not valid.'
        bottle.response.status = 400
        return bottle.template('error.html', generic_message=generic_message, message=False)
    try:
        r = connect()
    except:
        generic_message = 'There was a problem communicating with the database.'
        bottle.response.status = 500
        return bottle.template('error.html', generic_message=generic_message, message=False)
    message = r.get(link)
    ttl = r.ttl(link)
    if not message:
        generic_message = 'No message found on that link'
        bottle.response.status = 200
        return bottle.template('index.html', generic_message=generic_message, message=message)
    if link in ['hello']:
        bottle.response.status = 200
        return bottle.template('message.html', generic_message=generic_message, message=message)
    try:
        r.delete(link)
    except:
        generic_message = 'Failed to delete message'
        message = f'''
Since the message was not deleted we will not send it.
If the error persist please contact the system owner.

Time left before your message expires: {ttl}
        '''
        bottle.response.status = 500
        return bottle.template('error.html', generic_message=generic_message, message=message)
    generic_message = 'This message has been deleted and will not be visible again'
    bottle.response.status = 200
    return bottle.template('message.html', generic_message=generic_message, message=message)


if __name__ == '__main__':
    bottle.run(host='0.0.0.0', port=8080, debug=False, reloader=True)
