from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key


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


def generateKey_pem(public_name, private_name, gen_public=True):
    # Generate Private Key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend())

    p_key = key.private_bytes(encoding=serialization.Encoding.PEM,
                              format=serialization.PrivateFormat.PKCS8,
                              encryption_algorithm=serialization.NoEncryption())

    with open(private_name, "wb") as pem_file:
        pem_file.write(p_key)

    if gen_public:
        pub_key = key.public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                  format=serialization.PublicFormat.SubjectPublicKeyInfo)
        with open(public_name, "wb") as pem_file:
            pem_file.write(pub_key)

    return

# Generate a pseudo CA signed key
def ca_sign_key(pem_file, ca_pem_file):
    pub_key = getPrivateKey(pem_file).public_key().public_bytes(encoding=serialization.Encoding.PEM,
                                                                format=serialization.PublicFormat.SubjectPublicKeyInfo)

    ca_private_key = getPrivateKey(ca_pem_file)

    digital_sig = ca_private_key.sign(pub_key,
                                      padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                                  salt_length=padding.PSS.MAX_LENGTH),
                                      hashes.SHA256())

    return digital_sig

generateKey_pem(None, 'client_key.pem', gen_public=False)
generateKey_pem(None, 'server_key.pem', gen_public=False)



