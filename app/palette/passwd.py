"""
This module uses the pbkdf2_sha512 encryption algorithm - the current
recommendation as 1Q2014, see:
  http://pythonhosted.org/passlib/new_app_quickstart.html

The pbkdf2 algorithm and the methodologies employed here sastify the
current OWASP best-practices:
  https://www.owasp.org/index.php/Password_Storage_Cheat_Sheet
"""

from passlib.context import CryptContext

CONTEXT = CryptContext(
    schemes=["pbkdf2_sha512"],
    default="pbkdf2_sha512",

    # vary rounds parameter randomly when creating new hashes...
    all__vary_rounds=0.1,

    # this is default value for passlib
    # ... and supposedly the number of iterations used by iTunes.
    pbkdf2_sha512__default_rounds=10000,
    )

def verify(secret, hashed):
    return CONTEXT.verify(secret, hashed)

def encrypt(password):
    """ Returned format: $pbkdf2-digest$rounds$salt$checksum """
    return CONTEXT.encrypt(password)

import hashlib
def tableau_encrypt(password, salt):
    return hashlib.sha1(password + "fnord" + salt).hexdigest()
