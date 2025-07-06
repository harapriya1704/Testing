import requests
import zipfile
import io
import certifi
import os

def update_certifi():
    try:
        url = "https://pki.dell.com//Dell%20Technologies%20PKI%202018%20B64_PEM.zip"
        response = requests.get(url)
        response.raise_for_status()
        
        cert_path = certifi.where()
        dell_root_cert = "Dell Technologies Root Certificate Authority 2018.pem"
        dell_issuing_cert = "Dell Technologies Issuing CA 101_new.pem"
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            root_content = z.read(dell_root_cert).decode('utf-8')
            issuing_content = z.read(dell_issuing_cert).decode('utf-8')
            
            with open(cert_path, "a") as bundle:
                bundle.write("\n")
                bundle.write(root_content)
                bundle.write("\n")
                bundle.write(issuing_content)
                bundle.write("\n")
                
        return True
    except Exception as e:
        print(f"Certificate update failed: {e}")
        return False
