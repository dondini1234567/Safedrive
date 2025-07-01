import os
import sys
import subprocess
import shutil

def setup_pyntru():
    print("Setting up PyNTRU library...")
    
    # Create a directory for external libraries
    external_libs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external_libs')
    os.makedirs(external_libs_dir, exist_ok=True)
    print(f"Created directory: {external_libs_dir}")
    
    # Change to the external_libs directory
    os.chdir(external_libs_dir)
    
    # Clone the PyNTRU repository
    pyntru_dir = os.path.join(external_libs_dir, 'PyNTRU')
    if os.path.exists(pyntru_dir):
        print(f"PyNTRU directory already exists at {pyntru_dir}")
    else:
        print("Cloning PyNTRU repository...")
        try:
            subprocess.run(
                ['git', 'clone', 'https://github.com/smarky7CD/PyNTRU.git'],
                check=True
            )
            print("PyNTRU repository cloned successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            return False
        except FileNotFoundError:
            print("Git command not found. Please make sure Git is installed and in your PATH.")
            return False
    
    # Install numpy and sympy directly (avoid using requirements.txt from PyNTRU)
    try:
        print("Installing numpy and sympy...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'numpy', 'sympy'],
            check=True
        )
        print("Installed numpy and sympy successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing numpy and sympy: {e}")
        return False
    
    # Create or update .env file with PYTHONPATH
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Read existing .env file if it exists
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Update PYTHONPATH
    pythonpath = env_vars.get('PYTHONPATH', '')
    if external_libs_dir not in pythonpath:
        if pythonpath:
            env_vars['PYTHONPATH'] = f"{pythonpath};{external_libs_dir}"
        else:
            env_vars['PYTHONPATH'] = external_libs_dir
    
    # Write updated .env file
    with open(env_file, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"Updated {env_file} with PYTHONPATH={env_vars.get('PYTHONPATH')}")
    
    # Create a test file to verify PyNTRU installation
    test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_pyntru.py')
    with open(test_file, 'w') as f:
        f.write("""
import sys
import os

# Add external_libs to Python path
external_libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external_libs')
sys.path.append(external_libs_path)

try:
    from PyNTRU.PyNTRU.ntruencrypt import NtruEncrypt
    print("PyNTRU imported successfully!")
    
    # Test basic functionality
    ntru = NtruEncrypt(439, 3, 2048)
    public_key, private_key = ntru.generate_keypair()
    message = b"Hello, NTRU!"
    encrypted = ntru.encrypt(message, public_key)
    decrypted = ntru.decrypt(encrypted, private_key)
    
    print(f"Original message: {message}")
    print(f"Decrypted message: {decrypted}")
    print(f"Test successful: {message == decrypted}")
    
except ImportError as e:
    print(f"Failed to import PyNTRU: {e}")
except Exception as e:
    print(f"Error testing PyNTRU: {e}")
""")
    
    print(f"Created test file: {test_file}")
    print("PyNTRU setup complete!")
    print(f"Run 'python test_pyntru.py' to verify the installation.")
    
    return True

if __name__ == "__main__":
    setup_pyntru()
