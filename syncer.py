import os
import sys
import time
from datetime import datetime
from paramiko import SSHClient
from paramiko.ssh_exception import SSHException
from scp import SCPClient, SCPException
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
                os.startfile(file)
        else:
            os.startfile(path)


def get_all_files_in_dir(path):
    results = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if not str(file).startswith('.'):
                results.append(os.path.join(root, file))
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


def execute_commands():
    for command in commands:
        stdin, stdout, stderr = ssh.exec_command(command)
        err = [line for line in stderr]
        if len(err) > 0:
            print('Команда "' + command + '" завершилась с ошибкой:')
            for line in err:
                print(line)


def start_synchronization():
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

    ssh.exec_command('rm -rf ' + destination)
    for path in paths:
        scp.put(path, remote_path=destination, recursive=True)
        execute_commands()

    print('Синхронизация файлов началась.')
    print('Нажмите CTRL + C для остановки.')

    try:
        while True:
            for path in paths:
                files = get_changed_files(path)
                if len(files) == 0:
                    continue
                for file in files:
                    try:
                        name = file[len(path):]
                        scp.put(file, destination + name)
                        print('Файл "' + name + '" сохранен в ' +
                              datetime.now().strftime("%H:%M:%S") + '.')
                    except SCPException:
                        print('Возникла ошибка при сохранении "' + path + '".')
                execute_commands()
            time.sleep(1)
    except SSHException:
        print('Соединение с сервером было разорвано: выполняется повторное подключение.')
        start_synchronization()
    except KeyboardInterrupt:
        scp.close()
        print()
        print('Синхронизация файлов остановлена. До встречи :3')


if __name__ == '__main__':
    paths = filter_paths(paths)
    ssh = SSHClient()
    start_synchronization()
