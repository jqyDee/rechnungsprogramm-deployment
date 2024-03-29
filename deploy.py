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
        try:
            files_in_tmp = os.listdir(self.tmp_path)
        except FileNotFoundError:
            return logging.info('DEPLOY finished')
        for i in files_in_tmp:
            os.remove(f'{self.tmp_path}/{i}')
        if os.path.exists(self.tmp_path):
            os.rmdir(self.tmp_path)
        return logging.info('DEPLOY finished')

    def setup_logger(self):
        if self.debug_level == 'v':
            logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
            logging.debug('logging DEBUG')
        else:
            logging.basicConfig(level=logging.INFO, stream=sys.stderr)
            logging.info('logging INFO')

    def prepare_dirs(self):
        if not os.path.exists(self.tmp_path):
            os.makedirs(self.tmp_path)
            logging.info('made tmp dir')

    def import_login_data(self):
        with open(self.credential_path) as f:
            data = yaml.load(f, Loader=SafeLoader)
            self.host = data['host']
            logging.debug(f'host: {self.host}')
            self.username = data['user']
            logging.debug(f'user: {self.username}')
            self.password = data['pwd']
            logging.debug('pwd: **************')
        logging.info('extracted login credentials')

    def fetch_version_file(self):
        while self.running:
            try:
                logging.info('Requesting version.txt')
                urllib.request.urlretrieve('http://rechnungsprogramm.ffischh.de/version.txt', f'{self.tmp_path}/version.txt.tmp')
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
                logging.info('read remote version.txt')
                break

    def edit_version_file(self):
        if not self.version_number:
            logging.info('main Deploy needs version number')
            sys.exit()

        logging.debug(f'old version file data: {self.version_file_data}')

        if self.kind == 'm':
            self.version_file_data[0] = self.version_number
            self.version_file_data[1] = f'http://rechnungsprogramm.ffischh.de/main{self.version_number.replace(".", "-")}.py'
        elif self.kind == 'u':
            self.version_file_data[2] = self.version_number
            self.version_file_data[3] = f'http://rechnungsprogramm.ffischh.de/updater{self.version_number.replace(".", "-")}.py'

        logging.debug(f'new version file data: {self.version_file_data}')

        with open(f'{self.tmp_path}/version.txt', 'w') as f:
            for i in self.version_file_data:
                f.write(i+'\n')
        logging.info('updated data in local version.txt')

    def prepare_upload(self):
        shutil.copyfile(self.src_path, f'{self.tmp_path}/{os.path.basename(self.src_path)}')
        logging.info('Moved src file to tmp dir')

        if self.kind == 'm':
            self.dest_path = f'{os.path.dirname(self.dest_path)}/main{self.version_number.replace(".", "-")}' \
                             f'{os.path.splitext(os.path.basename(self.src_path))[1]}'
        if self.kind == 'u':
            self.dest_path = f'{os.path.dirname(self.dest_path)}/updater{self.version_number.replace(".", "-")}' \
                             f'{os.path.splitext(os.path.basename(self.src_path))[1]}'

        logging.debug(f'destination_path: {self.dest_path}')

    def sftp_connection(self) -> bool:
        with paramiko.SSHClient() as ssh:
            ssh.load_system_host_keys()
            logging.debug('loaded sys host keys')
            ssh.connect(self.host, username=self.username, password=self.password, port=22)
            logging.debug(f'established ssh connection to {self.host}:{self.username}:22')

            sftp = ssh.open_sftp()
            logging.debug('establishes sftp connection')

            sftp.put(self.src_path, self.dest_path)
            logging.debug('put src file to dest')

            if self.kind in ('m', 'u'):
                sftp.put(f'{self.tmp_path}/version.txt', f'{os.path.dirname(self.dest_path)}/version.txt')
            return True

    def create_gh_release(self):
        os.system(f'cd {os.path.dirname(self.src_path)}')
        os.system(f'gh release create v{self.version_number} --generate-notes --latest -t v{self.version_number}')


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
    if deployer.sftp_connection():
        deployer.create_gh_release()
    del deployer
