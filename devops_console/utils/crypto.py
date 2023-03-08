import os

import Cryptodome
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

# TODO get path from config
private_path = "./keys/private.pem"
public_path = "./keys/public.pem"


def generate_key_pair():
    if not os.path.exists("keys"):
        os.mkdir("keys")
    if not os.path.isfile(public_path) or not os.path.isfile(private_path):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.public_key().export_key()
        with open(private_path, "wb") as f:
            f.write(private_key)
        with open(public_path, "wb") as f:
            f.write(public_key)


def get_private_key():
    generate_key_pair()
    with open(private_path, "r") as f:
        return f.read()


def get_public_key():
    generate_key_pair()
    with open(public_path, "r") as f:
        return f.read()


def decrypt(encrypted_message: bytes):
    with open(private_path, "r") as f:
        key = RSA.import_key(f.read())
        cipher = PKCS1_OAEP.new(key, hashAlgo=Cryptodome.Hash.SHA256)
        decrypted = cipher.decrypt(encrypted_message)

        return decrypted
