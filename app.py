import re
import bottle
import requests
import redis
import settings
import logging.config
import json
import time
import hashlib
import uuid
import string
import textwrap
import sys
from cryptography.fernet import Fernet
import base64
import ipaddress

logging.config.dictConfig(settings.log_config)
logger = logging.getLogger(__name__)
app = application = bottle.default_app()


@bottle.hook("after_request")
def enable_cors():
    """
    Add CORS headers
    """
    bottle.response.headers["Access-Control-Allow-Origin"] = "https://eu.wikipedia.org"
    bottle.response.headers["Access-Control-Allow-Methods"] = "GET"
    bottle.response.headers[
        "Access-Control-Allow-Headers"
    ] = "Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token"


def check_user_agent(fn):
    """
    Decorator function that checks if the user agent is allowed.
    """

    def _wrap(*args, **kwargs):
        if bottle.request.get_header("User-Agent") in settings.ignore_user_agents:
            bottle.response.status = 403
            return {"status": "Failure", "error": ["User-Agent not allowed"]}
        return fn(*args, **kwargs)

    return _wrap


def rate(fn):
    """
    Decorator function that implements rate limiting for requests based on the client's IP address.
    It checks the number of attempts made by the client within a certain time period and blocks further requests if the limit is exceeded.
    """

    def _wrap(*args, **kwargs):
        generic_message = "Error."
        ip = bottle.request.environ.get(settings.http_ip_field)
        try:
            r = connect(settings.ratelimit_db)
        except:
            bottle.response.status = 500
            if bottle.request.method == "GET":
                return bottle.template(
                    "index.html",
                    generic_message=generic_message,
                    message="There was a problem communicating with the database",
                    company=settings.company,
                )
            else:
                return {"status": "Failure", "error": [generic_message]}
        try:
            attempts = r.get(ip)
            if not attempts:
                attempts = bytes([0])
        except:
            logger.exception("Failed to initialize ratelimit db")
            bottle.response.status = 500
            if bottle.request.method == "GET":
                return bottle.template(
                    "index.html",
                    generic_message=generic_message,
                    message="The ratelimit function is not working as expected",
                    company=settings.company,
                )
            else:
                return {"status": "Failure", "error": [generic_message]}
        attempts = bytes_to_int(attempts)
        attempts += 1
        r.setex(ip, 5, int_to_bytes(attempts))
        if attempts > 50:
            generic_message = (
                "You have been temporarily banned due to excessive requests"
            )
            message = "If you feel like this is/was a mistake please contact the system owner."
            r.setex(ip, 86400, int_to_bytes(attempts))
            bottle.response.status = 429
            if bottle.request.method == "GET":
                return bottle.template(
                    "index.html",
                    generic_message=generic_message,
                    message=message,
                    company=settings.company,
                )
            else:
                return {"status": "Failure", "error": [generic_message]}
        return fn(*args, **kwargs)

    return _wrap


def bytes_to_int(b):
    """
    Convert bytes to an integer.
    """
    return int.from_bytes(b, "big")


def int_to_bytes(i):
    """
    Convert an integer to bytes.
    """
    return bytes([i])


def encrypt(message, salt=settings.salt):
    """
    Encrypt a message using the provided key.
    """
    key = base64.urlsafe_b64encode(salt.encode())
    f = Fernet(key)
    return f.encrypt(message.encode())


def decrypt(message, salt=settings.salt):
    """
    Decrypt a message using the provided key.
    """
    key = base64.urlsafe_b64encode(salt.encode())
    try:
        f = Fernet(key)
    except ValueError:
        return False
    return f.decrypt(message.decode())


def connect(db=settings.db):
    """
    Connect to the Redis database.
    """
    return redis.StrictRedis(
        settings.redis_host,
        port=settings.redis_port,
        db=db,
        password=settings.redis_pass,
    )


def update_redis(key, message, ttl=3600):
    """
    Store a message in Redis with the specified key and time-to-live (TTL).
    """
    r = connect()
    h = r.setex(key, ttl, message)
    return h


def generate_key():
    """
    Generate a unique key for storing messages.
    """
    return hashlib.sha256(
        f"{str(uuid.uuid4())} - {str(time.time())}".encode()
    ).hexdigest()


def validate_message(message):
    """
    Validate the message to ensure it doesn't contain any prohibited characters.
    """
    if not message:
        return False
    if any(c in settings.bad_chars for c in message):
        return False
    return True


def validate_link(link):
    """
    Validate the link to ensure it is in the correct format and length.
    """
    if link in ["hello"]:
        return True
    if len(link) != 64:
        return False
    if any(i not in string.ascii_letters and i not in string.digits for i in link):
        return False
    return True


def generate_salt():
    return re.sub(
        "[^a-zA-Z0-9]",
        "",
        requests.get("https://en.wikipedia.org/wiki/Special:Random").url.split("/")[-1],
    )


def allowed_creator(ip):
  return any(ipaddress.ip_address(ip) in ipaddress.ip_network(cidr) for cidr in settings.cidrs)


@bottle.get("/static/style/<filepath:re:.*\.(css)>")
def style(filepath):
    return bottle.static_file(filepath, root="static/style")


@bottle.get("/static/fonts/<filepath:re:.*\.(otf|ttf)>")
def font(filepath):
    return bottle.static_file(filepath, root="static/fonts")


@bottle.get("/static/img/<filepath:re:.*\.(jpg|png|gif|ico|svg)>")
def img(filepath):
    return bottle.static_file(filepath, root="static/img")


@bottle.get("/static/script/<filepath:re:.*\.(js)>")
def script(filepath):
    return bottle.static_file(filepath, root="static/script")


@bottle.post("/")
@rate
def add_message():
    """
    Route handler for adding a new message.
    This function expects a JSON payload containing the message and stores it in Redis with a generated key.
    It returns the generated link for accessing the message.
    """
    if not allowed_creator(bottle.request.get_header("X-Real-Ip")):
        bottle.response.status = 403
        return {
            "status": "Failure",
            "error": ["Only authorized users can create messages at this time."],
        }
    try:
        byte = bottle.request.body
        request_body = json.loads(byte.read().decode("UTF-8"))
        message = request_body["message"]
    except:
        bottle.response.status = 400
        return {"status": "Failure", "error": ["Wrong input parameters"]}

    if not validate_message(message):
        bottle.response.status = 400
        return {"status": "Failure", "error": ["Bad characters in payload"]}

    display_salt = False
    salt = settings.salt
    if "salt" in request_body:
        if request_body["salt"]:
            display_salt = True
            salt = hashlib.sha256(request_body["salt"].encode()).hexdigest()[:32]

    ttl = 3600
    if "ttl" in request_body:
        if request_body["ttl"]:
            if isinstance(request_body["ttl"], int):
                ttl = request_body["ttl"]
                if ttl > 604800:
                    ttl = 604800

    try:
        r = connect()
    except:
        bottle.response.status = 500
        return {
            "status": "Failure",
            "error": ["There was a problem communicating with the database"],
        }

    key = generate_key()
    encrypted_message = encrypt(message, salt)

    if update_redis(key, encrypted_message, ttl):
        bottle.response.status = 200
        if display_salt:
            link = f"{settings.uri}/?link={key}&salt={salt}"
        else:
            link = f"{settings.uri}/?link={key}"
        return {
            "status": "Success",
            "message": {
                "link": link,
                "key": key,
                **({"salt": salt} if display_salt else {}),
            },
        }
    else:
        bottle.response.status = 500
        return {"status": "Failure", "error": ["Failed to store message in database"]}


@bottle.get("/")
@rate
def display_message():
    """
    Route handler for displaying a message.
    This function retrieves the message from Redis based on the provided link, deletes it from Redis, and displays the message.
    """
    generic_message = "Welcome"
    message = textwrap.dedent(
        f"""\
                    This is a one-time message delivery application.
                    You can generate your own secret message by making a POST request to this URL.
                    In the request body, submit a valid JSON containing the message.
                    Eg:
                    curl -XPOST -d '{{"message":"This is your secret message!"}}' {settings.uri}

                    You will receive your unique link in the response body.

                    Eg:
                    curl -s -XPOST -d '{{"message":"This is your secret message!"}}' {settings.uri} | jq
                    {{
                        "status": "Success",
                        "message": {{
                            "link": "{settings.uri}?link=3a2669a5df9add71aa79469e3194a68ebf4848c8a9bfafd1db0f3056f58b7c41",
                            "key": "3a2669a5df9add71aa79469e3194a68ebf4848c8a9bfafd1db0f3056f58b7c41"
                            }}
                        }}

                    Or submitting a message via the form below.


                    Caution:
                    There is a rate limiter in place.


                    """
    )

    link = bottle.request.query.link
    try:
        salt = bottle.request.query.salt
        if not salt:
            # Check if salt is empty string
            salt = settings.salt
    except:
        salt = settings.salt

    if not link:
        """
        If no link is provided, display the welcome message.
        """
        bottle.response.status = 200
        return bottle.template(
            "index.html",
            generic_message=generic_message,
            message=message,
            company=settings.company,
            submit=True,
            salt=generate_salt(),
        )

    real_ip = bottle.request.get_header("X-Real-Ip")
    user_agent = bottle.request.get_header("User-Agent")
    logger.info(f"Connection from: {real_ip} - Using: {user_agent}")
    link = bottle.request.query["link"]
    if not validate_link(link):
        """
        If the link is not valid, display an error message.
        """
        generic_message = "Bad link."
        bottle.response.status = 400
        logger.info(f"The link provided is not valid: {link}")
        return bottle.template(
            "index.html",
            generic_message=generic_message,
            message="The link you have provided is not valid",
            company=settings.company,
        )

    try:
        r = connect()
    except:
        """
        If there is a problem connecting to Redis, display an error message.
        """
        generic_message = "Error"
        bottle.response.status = 500
        logger.error("Failed to connect to database, when trying to get message")
        return bottle.template(
            "index.html",
            generic_message=generic_message,
            message="There was a problem communicating with the database.",
            company=settings.company,
        )

    message = r.get(link)
    ttl = r.ttl(link)

    if not message:
        """
        If the message is not found, display an error message.
        """
        generic_message = "Message not found"
        message = "No message found on that link"
        bottle.response.status = 200
        logger.info(f"No message found on this link: {link}")
        return bottle.template(
            "index.html",
            generic_message=generic_message,
            message=message,
            company=settings.company,
        )

    if link in ["hello"]:
        """
        If the link is a reserved keyword, display an example message.
        """
        bottle.response.status = 200
        generic_message = "This message has been deleted and will not be visible again"
        return bottle.template(
            "index.html",
            generic_message=generic_message,
            message=message,
            company=settings.company,
        )

    if salt:
        try:
            decrypted_message = decrypt(message, salt=salt)
        except:
            decrypted_message = False
    else:
        decrypted_message = decrypt(message)

    if not decrypted_message:
        """
        If the message cannot be decrypted, display an error message.
        """
        generic_message = "Bad link."
        bottle.response.status = 403
        logger.warning(f"The link provided does not match the salt: {link}")
        return bottle.template(
            "index.html",
            generic_message=generic_message,
            message="The link you have provided is not valid",
            company=settings.company,
        )

    try:
        r.delete(link)
    except:
        """
        If the message cannot be deleted, display an error message.
        """
        generic_message = "Failed to delete message"
        message = textwrap.dedent(
            f"""\
                        Since the message was not deleted, we will not send it.
                        If the error persists, please contact the system owner.

                        Time left before your message expires: {ttl}
                        """
        )
        bottle.response.status = 500
        logger.warning(f"Failed to delete message from database: {link}")
        return bottle.template(
            "index.html", generic_message=generic_message, message=message
        )

    """
    If the message is successfully deleted, display the message.
    """
    generic_message = "This message has been deleted and will not be visible again"
    bottle.response.status = 200
    logger.info(f"The message has been read by the user at link: {link}")
    return bottle.template(
        "index.html",
        generic_message=generic_message,
        message=decrypted_message,
        company=settings.company,
        _help=False,
    )


if __name__ == "__main__":
    """
    Start the Bottle server when the script is executed directly.
    """
    try:
        port = int(sys.argv[1])
    except:
        port = 8080

    bottle.run(host="0.0.0.0", port=port, debug=False, reloader=True)
