"""
Test script to directly locate and import the ntruencrypt module
"""
import os
import sys

def find_ntruencrypt():
    print("Searching for ntruencrypt.py...")
    
    # Get the path to the external_libs directory
    external_libs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external_libs')
    pyntru_dir = os.path.join(external_libs_dir, 'PyNTRU')
    
    if not os.path.exists(pyntru_dir):
        print(f"PyNTRU directory not found at {pyntru_dir}")
        return False
    
    # Search for ntruencrypt.py in the repository
    ntruencrypt_path = None
    for root, dirs, files in os.walk(pyntru_dir):
        print(f"Checking directory: {root}")
        for file in files:
            print(f"  File: {file}")
        if 'ntruencrypt.py' in files:
            ntruencrypt_path = os.path.join(root, 'ntruencrypt.py')
            break
    
    if ntruencrypt_path:
        print(f"Found ntruencrypt.py at {ntruencrypt_path}")
        
        # Try to import the module
        print("\nAttempting to import the module...")
        
        # Add the directory containing ntruencrypt.py to the Python path
        module_dir = os.path.dirname(ntruencrypt_path)
        sys.path.append(module_dir)
        print(f"Added {module_dir} to Python path")
        
        try:
            # Try direct import
            print("Trying direct import...")
            from ntruencrypt import NtruEncrypt
            print("Successfully imported NtruEncrypt!")
            
            # Test the module
            print("\nTesting NtruEncrypt...")
            ntru = NtruEncrypt(439, 3, 2048)
            public_key, private_key = ntru.generate_keypair()
            message = b"Hello, NTRU!"
            encrypted = ntru.encrypt(message, public_key)
            decrypted = ntru.decrypt(encrypted, private_key)
            
            print(f"Original message: {message}")
            print(f"Decrypted message: {decrypted}")
            print(f"Test successful: {message == decrypted}")
            
            return True
        except ImportError as e:
            print(f"Direct import failed: {e}")
            
            try:
                # Try import using spec
                print("\nTrying import using spec...")
                import importlib.util
                spec = importlib.util.spec_from_file_location("ntruencrypt", ntruencrypt_path)
                ntruencrypt = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ntruencrypt)
                
                # Check if NtruEncrypt exists in the module
                if hasattr(ntruencrypt, 'NtruEncrypt'):
                    NtruEncrypt = ntruencrypt.NtruEncrypt
                    print("Successfully imported NtruEncrypt using spec!")
                    
                    # Test the module
                    print("\nTesting NtruEncrypt...")
                    ntru = NtruEncrypt(439, 3, 2048)
                    public_key, private_key = ntru.generate_keypair()
                    message = b"Hello, NTRU!"
                    encrypted = ntru.encrypt(message, public_key)
                    decrypted = ntru.decrypt(encrypted, private_key)
                    
                    print(f"Original message: {message}")
                    print(f"Decrypted message: {decrypted}")
                    print(f"Test successful: {message == decrypted}")
                    
                    return True
                else:
                    print(f"NtruEncrypt class not found in the module")
                    return False
            except Exception as e:
                print(f"Import using spec failed: {e}")
                return False
    else:
        print("ntruencrypt.py not found in the repository")
        return False

if __name__ == "__main__":
    find_ntruencrypt()
