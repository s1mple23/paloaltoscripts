"""
SSL Certificate Generation Helper
"""
import os
import ipaddress
from datetime import datetime, timedelta
from config import config

def generate_ssl_certificates():
    """
    Generate self-signed SSL certificates for HTTPS
    
    Returns:
        Tuple of (cert_file, key_file) or (None, None) if failed
    """
    cert_file = config.SSL_CERT_FILE
    key_file = config.SSL_KEY_FILE
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✅ SSL certificates already exist")
        return cert_file, key_file
    
    print("=" * 60)
    print("🔒 Generating SSL certificates for HTTPS...")
    print("=" * 60)
    
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate subject and issuer
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Palo Alto Tool"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        # Create certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now()
        ).not_valid_after(
            datetime.now() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("✅ SSL certificates generated successfully")
        return cert_file, key_file
        
    except ImportError:
        print("⚠️  SSL certificate generation requires 'cryptography' package")
        print("   Installing cryptography...")
        try:
            import subprocess
            subprocess.check_call(["pip", "install", "cryptography"])
            print("   ✅ Cryptography installed. Please restart the application to enable HTTPS")
        except subprocess.CalledProcessError:
            print("   ❌ Failed to install cryptography. Please install manually: pip install cryptography")
        return None, None
        
    except Exception as e:
        print(f"⚠️  Could not generate SSL certificates: {e}")
        print("   Falling back to HTTP mode")
        return None, None

def check_ssl_certificates():
    """
    Check if SSL certificates exist and are valid
    
    Returns:
        True if certificates exist and are readable, False otherwise
    """
    cert_file = config.SSL_CERT_FILE
    key_file = config.SSL_KEY_FILE
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        return False
    
    try:
        # Try to read the files to ensure they're valid
        with open(cert_file, 'rb') as f:
            cert_data = f.read()
        
        with open(key_file, 'rb') as f:
            key_data = f.read()
        
        # Basic validation - check if they contain PEM headers
        if b'BEGIN CERTIFICATE' not in cert_data or b'BEGIN PRIVATE KEY' not in key_data:
            return False
        
        return True
        
    except Exception as e:
        print(f"⚠️  SSL certificate validation failed: {e}")
        return False

def get_ssl_context():
    """
    Get SSL context for Flask application
    
    Returns:
        SSL context tuple (cert_file, key_file) or None
    """
    if check_ssl_certificates():
        return (config.SSL_CERT_FILE, config.SSL_KEY_FILE)
    
    cert_file, key_file = generate_ssl_certificates()
    if cert_file and key_file:
        return (cert_file, key_file)
    
    return None