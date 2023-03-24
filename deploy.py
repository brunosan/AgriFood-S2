import os
import subprocess
import configparser
import datetime
import json


config = configparser.ConfigParser()

# read the config data from the file
config.read('config.ini')


db_user = config['DB']['username']
db_password = config['DB']['password']
db_name = config['DB']['dbname']
db_host = config['DB']['host']
db_port = int(config['DB']['port'])
db_file = config['DB']['database_file']

app_folder = config['APP']['app_folder']

#read remoteuser key value from json file deployed_resources.json
with open('deployed-resources.json', 'r') as f:
            resources = json.load(f)


remoteuser = 'ubuntu'
remote_server = resources['public_ip']
rsa_key = resources['rsa_key']

VERBOSE = True
def log(msg):
    if VERBOSE:
        print(f"{datetime.datetime.now().strftime('%H:%M:%S')} - {msg}")

try:   
    # # Export the PostgreSQL database to a file
    # log(f"{db_user} {db_name} {db_file} {app_folder} {remoteuser} {remote_server}")
    # pg_dump_command = f"pg_dump -F c -U {db_user} -d {db_name} -h {db_host} -p {db_port} -f {db_file}"
    # log(f"Exporting database with: {pg_dump_command}")
    # s= os.system(pg_dump_command)
    # if s != 0:
    #     raise Exception(f"Error exporting database with: {pg_dump_command}")
    
    # # Copy the required files to the remote server using scp
    # files_to_copy = f"{app_folder} {db_file}"
    # scp_command = f"scp -i {rsa_key}.rsa -r {files_to_copy} {remoteuser}@{remote_server}:~/"
    # log(f"Copying files to remote server with: {scp_command}")
    # s=subprocess.run(scp_command, shell=True)
    # if s.returncode != 0:
    #     raise Exception(f"Error copying files to remote server with: {scp_command}")

    # # Install the PostgreSQL database on the remote server
    # ssh_command = f"ssh -i {rsa_key}.rsa {remoteuser}@{remote_server} 'sudo apt-get update && sudo apt-get install postgresql python3 --yes'"
    # log(f"Installing PostgreSQL on remote server with: {ssh_command}")
    # s = subprocess.run(ssh_command, shell=True)
    # if s.returncode != 0:
    #     raise Exception(f"Error installing PostgreSQL on remote server with: {ssh_command}")

    # Restore the PostgreSQL database on the remote server from the exported file
    psql_commands = [f"psql postgres -c \"CREATE ROLE {db_user} WITH LOGIN PASSWORD '{db_password}' CREATEDB;\"",
                    f"psql postgres -c \"ALTER USER {db_user} WITH SUPERUSER;\"",
                    f"pg_restore -U {db_user} -C -d {db_name} {db_file}"]
    for c in psql_commands:
        ssh_psql_command = f"ssh {remote_server} '{c}'"
        log(f"Restoring database on remote server with: {ssh_psql_command}")
        s = subprocess.run(ssh_psql_command, shell=True)
        if s.returncode != 0:
            raise Exception(f"Error restoring database on remote server with: {ssh_psql_command}")

    # Start the Flask app on the remote server
    ssh_command = "ssh {remote_server} 'cd ~/flask_app && python3 app.py &'"
    log(f"Starting Flask app on remote server with: {ssh_command}")
    s = subprocess.run(ssh_command, shell=True)
    if s.returncode != 0:
        raise Exception(f"Error starting Flask app on remote server with: {ssh_command}")
    
except Exception as e:
        log(f"Error : {e}")
        raise
