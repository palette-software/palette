import os
import hashlib
import base64

from Crypto.Cipher import AES
from Crypto import Random

AES_KEY_BITS = 256
AES_KEY_BYTES = (AES_KEY_BITS/8)
AES_KEY_FILE_DEFAULT = '/var/palette/.aes'

# pylint: disable=invalid-name
aes_key_file = AES_KEY_FILE_DEFAULT
# pylint: enable=invalid-name

#  This is the Tableau password storage algorithm.
#  NOTE: str() is called to convert from unicode.
def tableau_hash(password, salt):
    return hashlib.sha1(str(password) + "fnord" + str(salt)).hexdigest()

def set_aes_key_file(path):
    # pylint: disable=global-statement
    # pylint: disable=invalid-name
    global aes_key_file
    aes_key_file = path
    if not os.path.isfile(aes_key_file):
        return genaeskey()

def genaeskey():
    key = Random.new().read(AES_KEY_BYTES)
    tmp = os.path.abspath(aes_key_file + '.tmp')
    with open(tmp, 'w') as f:
        f.write(key)
    os.rename(tmp, aes_key_file)
    os.chmod(aes_key_file, 0600)
    return key

def aeskey():
    if not os.path.isfile(aes_key_file):
        return genaeskey()
    with open(aes_key_file, 'r') as f:
        key = f.read(AES_KEY_BYTES)
    return key

def aes_encrypt(cleartext):
    key = aeskey()
    ivec = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CFB, ivec)
    return base64.b16encode(ivec + cipher.encrypt(cleartext))

def aes_decrypt(ciphertext):
    key = aeskey()
    msg = base64.b16decode(ciphertext)
    ivec = msg[0:AES.block_size]
    cipher = AES.new(key, AES.MODE_CFB, ivec)
    return cipher.decrypt(msg[AES.block_size:])
