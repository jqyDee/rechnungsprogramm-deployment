import os
import shutil
import sys
import urllib.request
import time
import logging
from urllib.error import URLError, HTTPError

import paramiko
import yaml
from yaml.loader import SafeLoader


class Deploy:
    host = None
    username = None
    password = None

    running = True
    version_file_data = []
    sleep_time = 30

    credential_path = os.getcwd()+f'/login.yml'
    tmp_path = os.getcwd()+f'/tmp/'

    def __init__(self, kind: str, src_path: str, dest_path: str, version_number: str = None,
                 debug_level: str = None, *args):
        """Initializes the Deploy class. Processes all given data"""

        self.kind = kind
        self.src_path = src_path
        self.dest_path = dest_path
        self.version_number = version_number
        self.debug_level = debug_level

    def __del__(self):
        self.running = False

    def setup_logger(self):
        if self.debug_level == 'v':
            logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
        else:
            logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    def prepare_dirs(self):
        if not os.path.exists(self.tmp_path):
            os.makedirs(self.tmp_path)

    def import_login_data(self):
        with open(self.credential_path) as f:
            data = yaml.load(f, Loader=SafeLoader)
            self.host = data['host']
            self.username = data['user']
            self.password = data['pwd']

    def fetch_version_file(self):
        while self.running:
            try:
                logging.info('Requesting version.txt')
                urllib.request.urlretrieve('https://ffischh.de/version.txt', f'{self.tmp_path}/version.txt.tmp')
            except HTTPError as e:
                logging.error('Error code: ', e.code)
                time.sleep(self.sleep_time)
            except URLError as e:
                logging.error('Reason: ', e.reason)
                time.sleep(self.sleep_time)
            else:
                logging.info('HTTP request good!')
                with open(f'{self.tmp_path}/version.txt.tmp', 'r') as f:
                    for i in f.readlines():
                        self.version_file_data.append(i.replace('\n', ''))
                break

    def edit_version_file(self):
        if self.kind == 'm':
            if not self.version_number:
                logging.info('main Deploy needs version number')
                sys.exit()

            self.version_file_data[0] = self.version_number
            self.version_file_data[1] = f'https://ffischh.de/main{self.version_number.replace(".", "-")}.py'
            with open(f'{self.tmp_path}/version.txt', 'w') as f:
                for i in self.version_file_data:
                    f.write(i+'\n')

    def prepare_upload(self):
        logging.info('Moved src file to tmp dir')
        shutil.copyfile(self.src_path, f'{self.tmp_path}/{os.path.basename(self.src_path)}')

        if self.kind == 'm':
            self.dest_path = f'{os.path.dirname(self.dest_path)}/main{self.version_number.replace(".", "-")}' \
                             f'{os.path.splitext(os.path.basename(self.src_path))[1]}'

    def sftp_connection(self):
        with paramiko.SSHClient() as ssh:
            ssh.load_system_host_keys()
            ssh.connect(self.host, username=self.username, password=self.password, port=22)

            sftp = ssh.open_sftp()

            sftp.put(self.src_path, self.dest_path)
            if self.kind == 'm':
                sftp.put(f'{self.tmp_path}/version.txt', f'{os.path.dirname(self.dest_path)}/version.txt')


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv[1:]) == 3:
        deployer = Deploy(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv[1:]) == 4:
        deployer = Deploy(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv[1:]) == 5:
        deployer = Deploy(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        sys.exit()

    deployer.setup_logger()
    deployer.prepare_dirs()
    deployer.import_login_data()
    deployer.fetch_version_file()
    deployer.edit_version_file()
    deployer.prepare_upload()
    deployer.sftp_connection()