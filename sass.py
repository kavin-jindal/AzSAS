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
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GRAY = "\033[90m"


def banner():
    print(f"""{CYAN}
    +----------------------------------------------------------+
    |                                                          |
    |     /\\\\    {BOLD}AzSas{RESET}{CYAN}                                         |
    |    /  \\\\   Azure Storage Enumeration using SAS           |
    |                                                          |
    |    {DIM}By    :{RESET}{CYAN} Kavin Jindal                                  |
    |    {DIM}GitHub:{RESET}{CYAN} https://github.com/kavin-jindal               |
    |                                                          |
    +----------------------------------------------------------+
    {RESET}""")
banner()
def enumerate_c(account, sas):
    with open(sas, 'r') as f:
        sas_token = f.read()
    service_client = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=sas_token)
    containers = service_client.list_containers()
    container_list = [container for container in containers]
    print(f"\n{BOLD}{CYAN}Containers found:{RESET} {DIM}({len(container_list)} container(s)){RESET}\n")
    if not container_list:
        print(f"  {DIM}No containers found.{RESET}\n")
        return
    for container in container_list:
        print(f"  {BOLD}{BLUE}[+]{RESET} {BOLD}{container.name}{RESET}")
    print()

def blob_enum(account, sas, container):

    with open(sas, 'r') as f:
        sas_token = f.read()
    service_client = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=sas_token)
    container_client = service_client.get_container_client(container=container)
    files = container_client.list_blobs(include=['versions'])

    blobs = {}
    for blob in files:
        blobs.setdefault(blob.name, []).append(blob)

    print(f"\n{BOLD}{CYAN}Container:{RESET} {container} {DIM}({len(blobs)} file(s)){RESET}\n")
    if not blobs:
        print(f"  {DIM}No blobs found.{RESET}")
        return

    for name, versions in blobs.items():
        print(f"  {BOLD}{BLUE}[+]{RESET} {BOLD}{name}{RESET}")
        versions.sort(key=lambda v: (bool(v.is_current_version), v.version_id or ""), reverse=True)
        for v in versions:
            if v.version_id is None:
                color, status, ver_str = GRAY, "UNVERSIONED", f"{DIM}N/A{RESET}"
            elif v.is_current_version:
                color, status, ver_str = GREEN, "CURRENT", v.version_id
            else:
                color, status, ver_str = YELLOW, "PREVIOUS", v.version_id
            label = f"[{status}]"
            print(f"      {color}{label:<13}{RESET} {DIM}Version:{RESET} {ver_str}")
    print()

    
def download_blob(account, sas, container, output):
    with open(sas, 'r') as f:
        sas_token = f.read()
    service_client = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=sas_token)
    container_client = service_client.get_container_client(container=container)
    files = container_client.list_blobs(include=['versions'])
    files_list = [i for i in files]

    print(f"\n{BOLD}{CYAN}Container:{RESET} {container} {DIM}({len(files_list)} blob version(s) discovered){RESET}\n")
    if not files_list:
        print(f"  {DIM}No files to download.{RESET}\n")
        return

    output_dir = Path(output)
    for i in files_list:
        download_kwargs = {"version_id": i.version_id} if i.version_id else {}
        blob_data = container_client.download_blob(blob=i.name, **download_kwargs)

        blob_path = Path(i.name)
        if i.version_id is None:
            color, status = GRAY, "UNVERSIONED"
            file_path = output_dir / blob_path
        elif i.is_current_version:
            color, status = GREEN, "CURRENT"
            file_path = output_dir / blob_path
        else:
            color, status = YELLOW, "PREVIOUS"
            safe_version = i.version_id.replace(":", "-")
            versioned_name = f"{blob_path.stem}_{safe_version}{blob_path.suffix}"
            file_path = output_dir / "versions" / blob_path.parent / versioned_name

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(blob_data.readall())

        label = f"[{status}]"
        ver_info = f" {DIM}({i.version_id}){RESET}" if status == "PREVIOUS" else ""
        print(f"  {GREEN}[+]{RESET} {color}{label:<13}{RESET} {BOLD}{i.name}{RESET}{ver_info} {DIM}-> {file_path}{RESET}")

    print(f"\n{BOLD}{GREEN}[+] Download complete{RESET}\n")

def info(sas):
    with open(sas, 'r') as f:
        sas_token = f.read().strip()

    components = [c for c in sas_token.split("&") if c]
    print(f"\n{BOLD}{CYAN}SAS Token Info:{RESET} {DIM}({len(components)} parameter(s)){RESET}\n")
    if not components:
        print(f"  {DIM}No parameters found.{RESET}\n")
        return

    for comp in components:
        if "=" in comp:
            key, val = comp.split("=", 1)
            print(f"  {BOLD}{BLUE}[+]{RESET} {CYAN}{key:<10}{RESET} {DIM}={RESET} {val}")
        else:
            print(f"  {BOLD}{BLUE}[+]{RESET} {comp}")
    print()


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

