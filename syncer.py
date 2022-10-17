import os
import sys
import time
from datetime import datetime
from paramiko import SSHClient
from scp import SCPClient
from config import *


def filter_paths(values):
    filtered_values = [path for path in values if os.path.exists(path)]
    if len(filtered_values) == 0:
        print('Не нашлось ни одного рабочего файла :c')
        sys.exit(1)
    not_found_values = set(values) - set(filtered_values)
    if len(not_found_values) > 0:
        print('Некорректные файлы:')
        number = 1
        for not_found_value in not_found_values:
            print(str(number) + '. ' + not_found_value)
            number += 1
    return filtered_values


def open_files():
    for path in paths:
        if os.path.isdir(path):
            for file in get_all_files_in_dir(path):
                os.system('open ' + file)
        else:
            os.system('open ' + path)


def get_all_files_in_dir(path):
    results = []
    for root, dirs, files in os.walk(path):
        for f in files:
            results.append(os.path.join(root, f))
    return results


def get_changed_files(path):
    changed_files = []
    if os.path.isdir(path):
        files = get_all_files_in_dir(path)
    else:
        files = [path]
    for file in files:
        if os.stat(file).st_mtime + 1 >= time.time():
            changed_files.append(file)
    return changed_files


def start_synchronization():
    ssh = SSHClient()
    ssh.load_system_host_keys()
    try:
        ssh.connect(hostname=hostname, port=port, username=username, password=password)
        print('Соединение с сервером установлено :)')
    except:
        print('Не удалось подключиться к серверу :c')
        return

    scp = SCPClient(ssh.get_transport())

    if auto_open:
        open_files()

    print('Обновление всех файлов на сервере.')

    for path in paths:
        scp.put(path, remote_path=destination, recursive=True)

    print('Синхронизация файлов началась.')
    print('Нажмите CTRL + C для остановки.')

    try:
        while True:
            for path in paths:
                for file in get_changed_files(path):
                    print('Файл "' + file[len(path):] + '" сохранен в ' +
                          datetime.now().strftime("%H:%M:%S") + '.')
                    scp.put(file, destination)
            time.sleep(1)
    except KeyboardInterrupt:
        scp.close()
        print()
        print('Синхронизация файлов остановлена. До встречи :3')


if __name__ == '__main__':
    paths = filter_paths(paths)
    start_synchronization()
