import os
import sys
import subprocess

def fix_pyntru_import():
    print("Fixing PyNTRU import issues...")
    
    # Get the path to the external_libs directory
    external_libs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external_libs')
    pyntru_dir = os.path.join(external_libs_dir, 'PyNTRU')
    
    if not os.path.exists(pyntru_dir):
        print(f"PyNTRU directory not found at {pyntru_dir}")
        print("Attempting to clone the repository...")
        
        os.makedirs(external_libs_dir, exist_ok=True)
        os.chdir(external_libs_dir)
        
        try:
            subprocess.run(
                ['git', 'clone', 'https://github.com/smarky7CD/PyNTRU.git'],
                check=True
            )
            print("PyNTRU repository cloned successfully")
        except Exception as e:
            print(f"Error cloning repository: {e}")
            return False
    
    # Examine the structure of the PyNTRU repository
    print(f"Examining PyNTRU repository structure at {pyntru_dir}...")
    
    # List all directories and files in the PyNTRU directory
    print("Directory structure:")
    for root, dirs, files in os.walk(pyntru_dir):
        level = root.replace(pyntru_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                print(f"{sub_indent}{file}")
    
    # Check if the PyNTRU module exists
    pyntru_module_dir = os.path.join(pyntru_dir, 'PyNTRU')
    if not os.path.exists(pyntru_module_dir):
        print(f"PyNTRU module directory not found at {pyntru_module_dir}")
        print("Looking for ntruencrypt.py in the repository...")
        
        # Search for ntruencrypt.py in the repository
        ntruencrypt_path = None
        for root, dirs, files in os.walk(pyntru_dir):
            if 'ntruencrypt.py' in files:
                ntruencrypt_path = os.path.join(root, 'ntruencrypt.py')
                break
        
        if ntruencrypt_path:
            print(f"Found ntruencrypt.py at {ntruencrypt_path}")
            
            # Create a simple wrapper to import the module
            wrapper_dir = os.path.join(external_libs_dir, 'pyntru_wrapper')
            os.makedirs(wrapper_dir, exist_ok=True)
            
            # Create __init__.py in the wrapper directory
            with open(os.path.join(wrapper_dir, '__init__.py'), 'w') as f:
                f.write("# PyNTRU wrapper package\n")
            
            # Create a wrapper module that imports the ntruencrypt module
            with open(os.path.join(wrapper_dir, 'ntruencrypt.py'), 'w') as f:
                f.write(f"""
# Import the NtruEncrypt class from the original module
import sys
import os

# Add the directory containing ntruencrypt.py to the Python path
sys.path.append(os.path.dirname('{ntruencrypt_path.replace('\\', '\\\\')}'))

try:
    from ntruencrypt import NtruEncrypt
except ImportError:
    # If that fails, try to import directly from the file
    import importlib.util
    spec = importlib.util.spec_from_file_location("ntruencrypt", "{ntruencrypt_path.replace('\\', '\\\\')}")
    ntruencrypt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ntruencrypt)
    NtruEncrypt = ntruencrypt.NtruEncrypt
""")
            
            print(f"Created wrapper module at {wrapper_dir}")
            
            # Create a test file to verify the wrapper
            test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_pyntru_fixed.py')
            with open(test_file, 'w') as f:
                f.write(f"""
import sys
import os

# Add the external_libs directory to the Python path
external_libs_path = '{external_libs_dir.replace('\\', '\\\\')}'
sys.path.append(external_libs_path)

try:
    # Try to import from the wrapper
    from pyntru_wrapper.ntruencrypt import NtruEncrypt
    print("PyNTRU imported successfully through wrapper!")
    
    # Test basic functionality
    ntru = NtruEncrypt(439, 3, 2048)
    public_key, private_key = ntru.generate_keypair()
    message = b"Hello, NTRU!"
    encrypted = ntru.encrypt(message, public_key)
    decrypted = ntru.decrypt(encrypted, private_key)
    
    print(f"Original message: {{message}}")
    print(f"Decrypted message: {{decrypted}}")
    print(f"Test successful: {{message == decrypted}}")
    
except ImportError as e:
    print(f"Failed to import PyNTRU: {{e}}")
except Exception as e:
    print(f"Error testing PyNTRU: {{e}}")
""")
            
            print(f"Created test file: {test_file}")
            print("Run 'python test_pyntru_fixed.py' to verify the fix.")
            
            # Update the crypto/ntru.py file to use the wrapper
            ntru_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'crypto', 'ntru.py')
            if os.path.exists(ntru_py_path):
                print(f"Updating {ntru_py_path} to use the wrapper...")
                
                with open(ntru_py_path, 'r') as f:
                    content = f.read()
                
                # Replace the import statement
                content = content.replace(
                    "from PyNTRU.PyNTRU.ntruencrypt import NtruEncrypt",
                    "from pyntru_wrapper.ntruencrypt import NtruEncrypt"
                )
                
                with open(ntru_py_path, 'w') as f:
                    f.write(content)
                
                print(f"Updated {ntru_py_path}")
            
            return True
        else:
            print("Could not find ntruencrypt.py in the repository")
            return False
    else:
        print(f"PyNTRU module directory found at {pyntru_module_dir}")
        
        # Check if ntruencrypt.py exists in the PyNTRU module directory
        ntruencrypt_path = os.path.join(pyntru_module_dir, 'ntruencrypt.py')
        if os.path.exists(ntruencrypt_path):
            print(f"ntruencrypt.py found at {ntruencrypt_path}")
            
            # Create a test file to verify the import
            test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_pyntru_fixed.py')
            with open(test_file, 'w') as f:
                f.write(f"""
import sys
import os

# Add the external_libs directory to the Python path
external_libs_path = '{external_libs_dir.replace('\\', '\\\\')}'
sys.path.append(external_libs_path)

try:
    # Try to import directly from the PyNTRU directory
    sys.path.append('{pyntru_dir.replace('\\', '\\\\')}')
    from PyNTRU.ntruencrypt import NtruEncrypt
    print("PyNTRU imported successfully!")
    
    # Test basic functionality
    ntru = NtruEncrypt(439, 3, 2048)
    public_key, private_key = ntru.generate_keypair()
    message = b"Hello, NTRU!"
    encrypted = ntru.encrypt(message, public_key)
    decrypted = ntru.decrypt(encrypted, private_key)
    
    print(f"Original message: {{message}}")
    print(f"Decrypted message: {{decrypted}}")
    print(f"Test successful: {{message == decrypted}}")
    
except ImportError as e:
    print(f"Failed to import PyNTRU: {{e}}")
except Exception as e:
    print(f"Error testing PyNTRU: {{e}}")
""")
            
            print(f"Created test file: {test_file}")
            print("Run 'python test_pyntru_fixed.py' to verify the fix.")
            
            # Update the crypto/ntru.py file to use the correct import
            ntru_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'crypto', 'ntru.py')
            if os.path.exists(ntru_py_path):
                print(f"Updating {ntru_py_path} to use the correct import...")
                
                with open(ntru_py_path, 'r') as f:
                    content = f.read()
                
                # Replace the import statement
                content = content.replace(
                    "from PyNTRU.PyNTRU.ntruencrypt import NtruEncrypt",
                    "from PyNTRU.ntruencrypt import NtruEncrypt"
                )
                
                with open(ntru_py_path, 'w') as f:
                    f.write(content)
                
                print(f"Updated {ntru_py_path}")
            
            return True
        else:
            print(f"ntruencrypt.py not found at {ntruencrypt_path}")
            
            # Search for ntruencrypt.py in the repository
            ntruencrypt_path = None
            for root, dirs, files in os.walk(pyntru_dir):
                if 'ntruencrypt.py' in files:
                    ntruencrypt_path = os.path.join(root, 'ntruencrypt.py')
                    break
            
            if ntruencrypt_path:
                print(f"Found ntruencrypt.py at {ntruencrypt_path}")
                
                # Create a test file to verify the import
                test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_pyntru_fixed.py')
                with open(test_file, 'w') as f:
                    f.write(f"""
import sys
import os

# Add the directory containing ntruencrypt.py to the Python path
ntruencrypt_dir = '{os.path.dirname(ntruencrypt_path).replace('\\', '\\\\')}'
sys.path.append(ntruencrypt_dir)

try:
    from ntruencrypt import NtruEncrypt
    print("PyNTRU imported successfully!")
    
    # Test basic functionality
    ntru = NtruEncrypt(439, 3, 2048)
    public_key, private_key = ntru.generate_keypair()
    message = b"Hello, NTRU!"
    encrypted = ntru.encrypt(message, public_key)
    decrypted = ntru.decrypt(encrypted, private_key)
    
    print(f"Original message: {{message}}")
    print(f"Decrypted message: {{decrypted}}")
    print(f"Test successful: {{message == decrypted}}")
    
except ImportError as e:
    print(f"Failed to import PyNTRU: {{e}}")
except Exception as e:
    print(f"Error testing PyNTRU: {{e}}")
""")
                
                print(f"Created test file: {test_file}")
                print("Run 'python test_pyntru_fixed.py' to verify the fix.")
                
                # Update the crypto/ntru.py file to use the correct import
                ntru_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'crypto', 'ntru.py')
                if os.path.exists(ntru_py_path):
                    print(f"Updating {ntru_py_path} to use the correct import...")
                    
                    with open(ntru_py_path, 'r') as f:
                        content = f.read()
                    
                    # Replace the import statement and path setup
                    updated_content = content.replace(
                        "# Try to import PyNTRU\ntry:\n    # Check if PyNTRU is in external_libs\n    pyntru_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), \n                              'external_libs', 'PyNTRU', 'PyNTRU')\n    \n    if os.path.exists(pyntru_path):\n        # Add PyNTRU to sys.path if it exists\n        sys.path.append(os.path.dirname(pyntru_path))\n        \n        # Try to import NtruEncrypt from PyNTRU\n        from PyNTRU.PyNTRU.ntruencrypt import NtruEncrypt\n        HAS_PYNTRU = True\n        print(\"Successfully imported PyNTRU\")\n    else:\n        HAS_PYNTRU = False\n        print(f\"PyNTRU directory not found at {pyntru_path}\")",
                        f"# Try to import PyNTRU\ntry:\n    # Add the directory containing ntruencrypt.py to the Python path\n    ntruencrypt_dir = '{os.path.dirname(ntruencrypt_path).replace('\\', '\\\\')}'\n    sys.path.append(ntruencrypt_dir)\n    \n    # Try to import NtruEncrypt from ntruencrypt.py\n    from ntruencrypt import NtruEncrypt\n    HAS_PYNTRU = True\n    print(\"Successfully imported PyNTRU\")"
                    )
                    
                    with open(ntru_py_path, 'w') as f:
                        f.write(updated_content)
                    
                    print(f"Updated {ntru_py_path}")
                
                return True
            else:
                print("Could not find ntruencrypt.py in the repository")
                return False

if __name__ == "__main__":
    fix_pyntru_import()
