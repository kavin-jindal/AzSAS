from azure.storage.blob import BlobServiceClient
from pathlib import Path
import argparse

parser = argparse.ArgumentParser(prog="AzSaS", description="Azure Storage Enumeration using SAS Tokens")
subparsers = parser.add_subparsers(dest="command", required=True)

enumerate_parser = subparsers.add_parser("enumerate", help="Enumerate containers")
enumerate_parser.add_argument("--account", required=True, help="Azure Storage account name")
enumerate_parser.add_argument("--sas", required=True, help="SAS Token")

blobs_parser = subparsers.add_parser("blob", help="Enumerate blobs")
blobs_parser.add_argument("--account", required=True, help="Azure Storage account name")
blobs_parser.add_argument("--sas", required=True, help="SAS Token")
blobs_parser.add_argument("-c", "--container", help="Specific container to enumerate", required=True)

download_parser = subparsers.add_parser("download", help="Download accessible blobs")
download_parser.add_argument("--account", required=True, help="Azure Storage account name")
download_parser.add_argument("--sas", required=True, help="SAS Token")
download_parser.add_argument("-o", "--output", default="./", help="Download destination directory")
download_parser.add_argument("-c", "--container", help="Specific container to download", required=True)

info_parser = subparsers.add_parser("info", help="Display SAS token information")
info_parser.add_argument("--sas", required=True, help="Path to SAS token file")
args = parser.parse_args()
def banner():
   
    print(r"""
    +----------------------------------------------------------+
    |                                                          |
    |     /\\    AzSas                                         |
    |    /  \\   Azure Storage Enumeration using SAS           |
    |                                                          |
    |    By    : Kavin Jindal                                  |
    |    GitHub: https://github.com/kavin-jindal               |
    |                                                          |
    +----------------------------------------------------------+
    """)
banner()
def enumerate_c(account, sas):
    f = open(sas, 'r')
    sas_token = f.read()
    service_client = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=sas_token)
    containers = service_client.list_containers()
    container_list = [container for container in containers]
    print(f"No. of containers found: {len(container_list)}")
    for container in container_list:
        
        print('\t[!] ', container.name)

def blob_enum(account, sas, container):
    f = open(sas, 'r')
    sas_token = f.read()
    service_client = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=sas_token)
    container_client = service_client.get_container_client(container=container)
    files = container_client.list_blobs()
    print("Container: ", container)
    for i in files:
        print('\t[!] ', i.name)

    
def download_blob(account, sas, container, output):
    f = open(sas, 'r')
    sas_token = f.read()
    service_client = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=sas_token)
    container_client = service_client.get_container_client(container=container)
    files = container_client.list_blobs()
    files_list = []
    for i in files:
        files_list.append(i)

    print(f"{len(files_list)} files discovered. ")
    for i in files_list:
        
        blob_data = container_client.download_blob(blob=i.name, )
        
        output = Path(output)
        file_path = output / i.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(blob_data.readall())

    print("Download complete")

def info(sas):
    with open(sas, 'r') as f:
        sas_token = f.read()

    components = sas_token.split("&")
    print(components)


if args.command == "enumerate":
    account = args.account
    sas = args.sas
    enumerate_c(account, sas)

if args.command == "blob":
    account = args.account
    sas = args.sas
    container = args.container
    blob_enum(account, sas, container)

if args.command == "download":
    account = args.account
    sas = args.sas
    container = args.container
    output = args.output
    download_blob(account, sas, container, output)

if args.command == "info":
    sas = args.sas
    info(sas)

