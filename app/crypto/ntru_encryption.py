"""
SafeDrive Hybrid Encryption Module (Simulated PQC)

Encrypts and decrypts files using a hybrid of password-derived key and 
simulated Post-Quantum Cryptography (PQC) shared key.
"""
"""
import os
import json
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# ----- Simulated PQC key generation and encapsulation -----

FIXED_PQC_SHARED_SECRET = b'\x01' * 32  # Fixed 256-bit symmetric key for demonstration

def pqc_generate_keypair():
    # Simulated public/private key pair
    return b"pqc_public_key_sim", b"pqc_private_key_sim"

def pqc_encapsulate_key(pqc_public_key):
    # Simulate encapsulation: returns fixed ciphertext and shared secret
    ciphertext = b"pqc_encapsulated_key_sim"
    return ciphertext, FIXED_PQC_SHARED_SECRET

def pqc_decapsulate_key(pqc_private_key, ciphertext):
    # Simulate decapsulation: return same fixed shared secret
    return FIXED_PQC_SHARED_SECRET

# ---------------------------------------------------------

def derive_key_from_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key, salt

def encrypt_with_aes(data, key):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(b"SafeDrive-Encrypted-File")
    encrypted_data = encryptor.update(data) + encryptor.finalize()
    tag = encryptor.tag
    return encrypted_data, iv, tag

def decrypt_with_aes(encrypted_data, key, iv, tag):
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    decryptor.authenticate_additional_data(b"SafeDrive-Encrypted-File")
    return decryptor.update(encrypted_data) + decryptor.finalize()

def encrypt_file(input_path, password, output_path=None):
    if output_path is None:
        output_path = input_path + '.enc'

    with open(input_path, 'rb') as f:
        data = f.read()

    pqc_public_key, pqc_private_key = pqc_generate_keypair()
    pqc_ciphertext, pqc_symmetric_key = pqc_encapsulate_key(pqc_public_key)
    classical_key, salt = derive_key_from_password(password)

    # Combine both keys into a hybrid key (XOR for demonstration)
    hybrid_key = bytes(a ^ b for a, b in zip(classical_key, pqc_symmetric_key))
    encrypted_data, iv, tag = encrypt_with_aes(data, hybrid_key)

    with open(output_path, 'wb') as f:
        metadata = {
            'algorithm': 'PQC-Hybrid-AES-256-GCM',
            'salt': base64.b64encode(salt).decode(),
            'iv': base64.b64encode(iv).decode(),
            'tag': base64.b64encode(tag).decode(),
            'pqc_ciphertext': base64.b64encode(pqc_ciphertext).decode(),
            'version': '1.0'
        }
        metadata_json = json.dumps(metadata).encode('utf-8')
        f.write(len(metadata_json).to_bytes(4, byteorder='big'))
        f.write(metadata_json)
        f.write(encrypted_data)

    print(f"[✓] File encrypted and saved to {output_path}")
    return output_path

def decrypt_file(input_path, password, output_path=None):
    if output_path is None:
        output_path = input_path[:-4] if input_path.endswith('.enc') else input_path + '.dec'

    with open(input_path, 'rb') as f:
        metadata_length = int.from_bytes(f.read(4), byteorder='big')
        metadata_json = f.read(metadata_length)
        metadata = json.loads(metadata_json.decode('utf-8'))
        encrypted_data = f.read()

    if metadata.get('algorithm') != 'PQC-Hybrid-AES-256-GCM':
        raise ValueError(f"Unsupported encryption algorithm: {metadata.get('algorithm')}")

    salt = base64.b64decode(metadata['salt'])
    iv = base64.b64decode(metadata['iv'])
    tag = base64.b64decode(metadata['tag'])
    pqc_ciphertext = base64.b64decode(metadata['pqc_ciphertext'])

    classical_key, _ = derive_key_from_password(password, salt)
    _, pqc_private_key = pqc_generate_keypair()
    pqc_symmetric_key = pqc_decapsulate_key(pqc_private_key, pqc_ciphertext)

    hybrid_key = bytes(a ^ b for a, b in zip(classical_key, pqc_symmetric_key))

    try:
        decrypted_data = decrypt_with_aes(encrypted_data, hybrid_key, iv, tag)
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}. Possibly incorrect password or corrupted file.")

    with open(output_path, 'wb') as f:
        f.write(decrypted_data)

    print(f"[✓] File decrypted and saved to {output_path}")
    return output_path
"""

import os
import json
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from pqcrypto.kem.mceliece348864 import generate_keypair, encrypt, decrypt

# --- McEliece Keypair Wrapper ---
def pqc_generate_keypair():
    return generate_keypair()

def pqc_encapsulate_key(pk):
    return encrypt(pk)

def pqc_decapsulate_key(sk, ct):
    return decrypt(sk, ct)

# --- Password-Derived Key ---
def derive_key_from_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())
    return key, salt

# --- AES-GCM Encryption ---
def encrypt_with_aes(data, key):
    iv = os.urandom(12)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encryptor.authenticate_additional_data(b"SafeDrive-Encrypted-File")
    encrypted_data = encryptor.update(data) + encryptor.finalize()
    return encrypted_data, iv, encryptor.tag

def decrypt_with_aes(encrypted_data, key, iv, tag):
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    decryptor.authenticate_additional_data(b"SafeDrive-Encrypted-File")
    return decryptor.update(encrypted_data) + decryptor.finalize()

# --- File Encryption ---
def encrypt_file(input_path, password, output_path=None):
    if output_path is None:
        output_path = input_path + '.enc'

    with open(input_path, 'rb') as f:
        data = f.read()

    pqc_public_key, pqc_private_key = pqc_generate_keypair()
    pqc_ciphertext, pqc_symmetric_key = pqc_encapsulate_key(pqc_public_key)
    classical_key, salt = derive_key_from_password(password)

    hybrid_key = bytes(a ^ b for a, b in zip(classical_key, pqc_symmetric_key))
    encrypted_data, iv, tag = encrypt_with_aes(data, hybrid_key)

    with open(output_path, 'wb') as f:
        metadata = {
            'algorithm': 'PQC-McEliece-Hybrid-AES-256-GCM',
            'salt': base64.b64encode(salt).decode(),
            'iv': base64.b64encode(iv).decode(),
            'tag': base64.b64encode(tag).decode(),
            'pqc_ciphertext': base64.b64encode(pqc_ciphertext).decode(),
            'version': '1.0'
        }
        metadata_json = json.dumps(metadata).encode('utf-8')
        f.write(len(metadata_json).to_bytes(4, byteorder='big'))
        f.write(metadata_json)
        f.write(encrypted_data)

    with open(output_path + '.key', 'wb') as kf:
        kf.write(pqc_private_key)

    print(f"[✓] File encrypted using McEliece and saved to {output_path}")
    return output_path

# --- File Decryption ---
def decrypt_file(input_path, password, output_path=None):
    if output_path is None:
        output_path = input_path[:-4] if input_path.endswith('.enc') else input_path + '.dec'

    with open(input_path, 'rb') as f:
        metadata_length = int.from_bytes(f.read(4), byteorder='big')
        metadata_json = f.read(metadata_length)
        metadata = json.loads(metadata_json.decode('utf-8'))
        encrypted_data = f.read()

    if metadata.get('algorithm') != 'PQC-McEliece-Hybrid-AES-256-GCM':
        raise ValueError(f"Unsupported encryption algorithm: {metadata.get('algorithm')}")

    salt = base64.b64decode(metadata['salt'])
    iv = base64.b64decode(metadata['iv'])
    tag = base64.b64decode(metadata['tag'])
    pqc_ciphertext = base64.b64decode(metadata['pqc_ciphertext'])

    classical_key, _ = derive_key_from_password(password, salt)

    key_file_path = input_path + '.key'
    if not os.path.exists(key_file_path):
        raise FileNotFoundError(f"Missing private key file: {key_file_path}")

    with open(key_file_path, 'rb') as kf:
        pqc_private_key = kf.read()

    pqc_symmetric_key = pqc_decapsulate_key(pqc_private_key, pqc_ciphertext)

    hybrid_key = bytes(a ^ b for a, b in zip(classical_key, pqc_symmetric_key))

    try:
        decrypted_data = decrypt_with_aes(encrypted_data, hybrid_key, iv, tag)
    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}. Possibly incorrect password or corrupted file.")

    with open(output_path, 'wb') as f:
        f.write(decrypted_data)

    print(f"[✓] File decrypted and saved to {output_path}")
    return output_path

