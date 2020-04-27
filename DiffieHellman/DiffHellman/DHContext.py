import base64
import sys
import hashlib

from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime


# Retrieve public key bytes from PEM file
def getPublicKey(pem_file):
    with open(pem_file, "rb") as pem_data:
        key = load_pem_public_key(pem_data.read(), backend=default_backend())

    return key


# Retrieve private key bytes from PEM file
def getPrivateKey(pem_file):
    with open(pem_file, "rb") as pem_data:
        key = load_pem_private_key(pem_data.read(), password=None, backend=default_backend())

    return key


# HASH CONTENT HELPER METHOD (EXPECTS INPUT TO BE BYTE OBJECT))
# RETURNS HASH DIGEST AND DIGEST SIZE
def hashContent(data_bytes, mac=False, key=None):
    # HASH MESSAGE AND COMPARE TO RECEIVED HASH
    if mac:
        data_bytes = key + data_bytes
        hasher = hashlib.sha1()
        message_length = len(data_bytes)
        remainder = message_length % 64

        padding_length = (56 - remainder if remainder <= 56 else (56 + 64) - remainder)
        # print("Message length: {}".format(message_length))
        # print("Remainder length: {}".format(remainder))
        # print("Padding length: {}".format(padding_length))
        padding = [0] * padding_length
        padding[0] = 1 << 7
        padding_bytes = bytes(padding)

        data_bytes += padding_bytes
        message_length_bytes = bytes(format(message_length, '08b').encode())

        data_bytes += message_length_bytes
        # print("Message_length Length: {}".format(len(message_length_bytes)))
        # print("Total Length: {}".format(len(data_bytes)))
        # print(message_length_bytes)

        hasher.update(data_bytes)
        hashed_message = hasher.digest()


    else:
        hasher = hashlib.sha256()
        message_length = len(data_bytes)
        remainder = message_length % 64

        padding_length = (56 - remainder if remainder <= 56 else (56+64) - remainder)
        #print("Message length: {}".format(message_length))
        #print("Remainder length: {}".format(remainder))
        #print("Padding length: {}".format(padding_length))
        padding = [0] * padding_length
        padding[0] = 1 << 7
        padding_bytes = bytes(padding)

        data_bytes += padding_bytes
        message_length_bytes = bytes(format(message_length, '08b').encode())

        data_bytes += message_length_bytes
        #print("Message_length Length: {}".format(len(message_length_bytes)))
        #print("Total Length: {}".format(len(data_bytes)))
        #print(message_length_bytes)

        hasher.update(data_bytes)
        hashed_message = hasher.digest()

    return hashed_message


# VERIFY MESSAGE
def verifyContent(raw_contents, session_key):
    contents = base64.b64decode(raw_contents.decode())
    iv = hashContent(session_key)[0:16]

    # DECODE CONTENTS
    # VERIFY INTEGRITY AND AUTHENTICITY
    backend = default_backend()

    cipher = Cipher(algorithms.AES(session_key), modes.CBC(iv), backend=backend)
    c_decryptor = cipher.decryptor()

    decrypted_contents = c_decryptor.update(contents) + c_decryptor.finalize()
    # modified for perfect testing
    contents = removePadding(decrypted_contents)
    message, sent_hash = decrypted_contents.rsplit(b',', 1)
    sent_hash = removePadding(sent_hash)

    #decrypted_hash_split = decrypted_hash.split(b'\x00')[0]

    # HASH MESSAGE AND COMPARE TO RECEIVED HASH
    hashed_contents = hashContent(message)
    verified = True if hashed_contents == sent_hash else False

    #print("Content Length: {},\nContent Hash: {}\nSent Hash: {}".format(len(contents), hashed_contents, sent_hash))

    return decrypted_contents, verified


# VERIFY NO MAN IN MIDDLE
def verifyKey(contents, session_key, public_key):

    return None


# THIS HELPER METHOD IS USED TO ADD PROPER PADDING TO BYTE INPUT AND
# RETURN OUTPUT ENCRYPTED WITH THE PROVIDED CIPHER IN B64 RAW BYTES
def encryptContent(data, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    block_size = 16

    #DETERMINE PADDING SIZE
    #print("encryption raw data length: {}".format(len(data)))
    remainder = len(data) % block_size
    padding_length = 16 - remainder if remainder > 0 else 0
    #print("padding length: {}".format(padding_length))

    #ADD PADDING
    if padding_length > 0:
        padding = [0] * padding_length
        # Testing HERE
        padding[0] = padding_length
        padding_bytes = bytes(padding)
        data += padding_bytes
    #print("encryption input data (with padding) length: {}".format(len(data)))

    #ENCRYPT AND RETURN OUTPUT
    message = encryptor.update(data) + encryptor.finalize()

    return (base64.b64encode(message))


# Helper method to remove padding
def removePadding(data):
    data_len = len(data)
    check_n = 0
    for b in data[data_len:None:-1]:
        check_n += 1
        if b != 0:
            padding_len = int(b)
            break

    # In case there was NO padding
    # Data was block size and last
    # byte was not padding
    if check_n != padding_len:
        padding_len = 0

    return data[0:data_len-padding_len]
