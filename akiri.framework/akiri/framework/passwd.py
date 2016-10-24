"""
This module uses the current recommendation of the passlib library.
As of 4Q-2015: pbkdf2_sha512

See:
  http://pythonhosted.org/passlib/new_app_quickstart.html

This algorithm and the methodologies employed here satisfy the
current OWASP best-practices:
  https://www.owasp.org/index.php/Password_Storage_Cheat_Sheet
"""

try:
    from passlib.context import CryptContext
except ImportError:
    raise ImportError("cannot import '%s', passlib is not installed" % __name__)

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
    """ Check a password against a specified hash. """
    return CONTEXT.verify(secret, hashed)

def encrypt(secret):
    """ Returned format: $pbkdf2-digest$rounds$salt$checksum """
    return CONTEXT.encrypt(secret)
