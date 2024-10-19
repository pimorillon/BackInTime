#!/usr/bin/python3
import os
import re
import pwd
import subprocess
from datetime import datetime

def addLastSlashToDir(directory):
    if directory[-1] != '/':
        directory += '/'
    return directory

def getPreviousBackup(backup_dir,backup_name):
    entries = os.listdir(backup_dir)
    entries = [entry for entry in entries if re.match(backup_name,entry) ]
    directories = [entry for entry in entries if os.path.isdir(os.path.join(backup_dir, entry))]
    directories.sort()
    if len(directories) == 0:
        return False
    else:
        return os.path.join(backup_dir,directories[-1])

def extract_timestamp(directory):
    #Assuming directories are named as 'BACKUP-YYYY-MM-DD'
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}$')
    match = date_pattern.search(directory)
    if match:
        try:
            return datetime.strptime(match.group(0), '%Y-%m-%d')
        except ValueError:
            return None
    return None

def is_valid_backup_directory(directory, prefix):
    if not directory.startswith(prefix):
        return False
    date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}$')
    match = date_pattern.search(directory)
    if match:
        try:
            datetime.strptime(match.group(0), '%Y-%m-%d')
            return True
        except ValueError:
            return False
    return False

def remountFS(mount_point, options,logger):
    try:
        subprocess.check_call(['sudo','mount', '-o', f'remount,{options}', mount_point],\
                stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
        logger.info("The mount point %s has been remounted as %s.",mount_point,options)
    except subprocess.CalledProcessError as e:
        logger.critical("Failed to remount %s as %s. Error: %s",mount_point,options,e)
        exit(10)

def find_users_conf():
    users = {}
    for user in pwd.getpwall():
        user_name = user.pw_name
        home_dir = user.pw_dir
        if user.pw_uid < 1000 or user.pw_uid == 65534:
            continue
        file_path = os.path.join(home_dir, '.backtothefile.conf')
        if os.path.exists(file_path):
            users[user_name] = [home_dir,file_path]
    return users

