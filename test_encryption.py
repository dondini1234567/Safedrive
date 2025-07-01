"""
Test script for SafeDrive encryption functionality
"""
import os
import sys
import tempfile
import time

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the encryption module
try:
    from app.crypto.ntru import encrypt_file, decrypt_file
    
    print("Testing SafeDrive Hybrid Post-Quantum Encryption")
    
    # Create a test file
    test_content = b"This is a test file for SafeDrive encryption. It contains some secret information that needs to be protected."
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(test_content)
        original_file = temp_file.name
    
    # Create paths for encrypted and decrypted files
    encrypted_file = original_file + ".enc"
    decrypted_file = original_file + ".dec"
    
    # Test password
    password = "test-password-123"
    
    print("\nTesting encryption with hybrid post-quantum method...")
    
    # Measure encryption time
    start_time = time.time()
    encrypt_file(original_file, encrypted_file, password)
    encryption_time = time.time() - start_time
    
    print(f"Encryption completed in {encryption_time:.2f} seconds")
    
    # Check if encrypted file exists and is different from original
    if os.path.exists(encrypted_file):
        original_size = os.path.getsize(original_file)
        encrypted_size = os.path.getsize(encrypted_file)
        print(f"Original file size: {original_size} bytes")
        print(f"Encrypted file size: {encrypted_size} bytes")
        
        if encrypted_size > original_size:
            print("✓ Encrypted file is larger than original (expected)")
        else:
            print("⚠ Warning: Encrypted file is not larger than original")
    else:
        print("❌ Encrypted file was not created")
        sys.exit(1)
    
    print("\nTesting decryption...")
    
    # Measure decryption time
    start_time = time.time()
    decrypt_file(encrypted_file, decrypted_file, password)
    decryption_time = time.time() - start_time
    
    print(f"Decryption completed in {decryption_time:.2f} seconds")
    
    # Verify decrypted content matches original
    if os.path.exists(decrypted_file):
        with open(decrypted_file, 'rb') as f:
            decrypted_content = f.read()
        
        if decrypted_content == test_content:
            print("✓ Decrypted content matches original")
        else:
            print("❌ Decrypted content does not match original")
            print(f"Original: {test_content}")
            print(f"Decrypted: {decrypted_content}")
    else:
        print("❌ Decrypted file was not created")
    
    # Test with wrong password
    wrong_password = "wrong-password-456"
    wrong_decrypted_file = original_file + ".wrong"
    
    print("\nTesting decryption with wrong password (should fail)...")
    
    try:
        decrypt_file(encrypted_file, wrong_decrypted_file, wrong_password)
        print("❌ Decryption with wrong password succeeded (unexpected)")
    except Exception as e:
        print(f"✓ Decryption with wrong password failed as expected: {str(e)}")
    
    # Clean up
    print("\nCleaning up test files...")
    for file_path in [original_file, encrypted_file, decrypted_file]:
        if os.path.exists(file_path):
            os.unlink(file_path)
            print(f"Deleted {file_path}")
    
    if os.path.exists(wrong_decrypted_file):
        os.unlink(wrong_decrypted_file)
        print(f"Deleted {wrong_decrypted_file}")
    
    print("\nEncryption test completed successfully!")

except ImportError as e:
    print(f"Error importing encryption module: {str(e)}")
except Exception as e:
    print(f"Error during encryption test: {str(e)}")
