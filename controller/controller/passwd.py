import hashlib

""" 
  This is the Tableau password storage algorithm. 
  NOTE: str() is called to convert from unicode.
"""
def tableau_hash(password, salt):
    return hashlib.sha1(str(password) + "fnord" + str(salt)).hexdigest()
