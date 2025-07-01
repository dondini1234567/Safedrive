# Crypto package initialization

"""
Crypto package initialization for quantum-resistant encryption
"""

# Import the encryption functions to make them available
try:
    from app.crypto.ntru_encryption import encrypt_file, decrypt_file
except ImportError:
    # Provide fallback or error message
    import sys
    print("Error: Could not import encryption functions. Make sure all dependencies are installed.", file=sys.stderr)
