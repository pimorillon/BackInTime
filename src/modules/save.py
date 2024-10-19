#!/usr/bin/python3

import os
import re
import subprocess
import logging
from utils import getPreviousBackup

def excludeRoot(exclude_list):
# Only used when source is root
    excluded_root_list = ['/dev/',
                          '/efi/',
                          '/mnt/',
                          '/proc/',
                          '/run/',
                          '/sys/',
                          '/tmp/',
                          '/var/run/',
                          '/var/tmp/',
                          'lost+found']
    exclude_list.extend(excluded_root_list)

def findGitDirs(start_path,excluded_list,logger):
    exclude_dirs = []
    try:
        os.scandir(start_path)
    except PermissionError:
        logger.error("Permission Error in %s",start_path)
        return 20
    for entry in os.scandir(start_path):
        if entry.is_dir() and not entry.is_symlink():
            real_path = os.path.realpath(entry.path)
            real_path += os.sep
            if entry.name == '.git':
                exclude_dirs.append(os.path.realpath(start_path))
                break
            elif real_path not in excluded_list:
                try:
                    exclude_dirs.extend(findGitDirs(entry.path,excluded_list,logger))
                except TypeError:
                    return 20
    return exclude_dirs

def save(user,config):
    logger = logging.getLogger(__name__)
    command = ["rsync","-a","--delete","--exclude=*.bak","--exclude=*lost+found"]
    
    if config["Source"]["directory"] == "/":
        excludeRoot(config['Source']['exclude'])
    for entry in config['Source']['exclude']:
        command.append(f"--filter=- {entry}")
    
    #Remove git directories
    git_dirs = findGitDirs(config["Source"]["directory"],config['Source']['exclude'],logger)
    #Exiting if permission error in function
    if git_dirs == 20:
        return 20
    for entry in git_dirs:
        command.append(f"--filter=- {entry}")
    
    #Check for previous backup
    old = getPreviousBackup(config["Destination"]['directory'],config["Destination"]['name'])
    if old:
        logger.debug("Hard-linking files to %s",old)
        command.append(f"--link-dest={old}")
    else:
        logger.warning("No previous backup found in %s for user %s",config["Destination"]['directory'],user)
    
    command.append(config["Source"]["directory"])
    command.append(config["Destination"]["full_path"])
    logger.debug(command)
    
    #Try to create the destination directory
    try:
        os.makedirs(config["Destination"]["full_path"])
    except FileExistsError:
        logger.warning("Directory %s already exists, skipping save.",config["Destination"]["full_path"])
        return 30
    except PermissionError:
        logger.error("Permission denied: Cannot create directory %s.",config["Destination"]["full_path"])
        return 20
    except OSError as e:
        logger.error(f"OS error: {e}")
        return 11
    
    result = subprocess.run(command, shell=False,capture_output=True,encoding='utf-8')
    if result.stdout:
        logger.info(result.stdout)
    if result.stderr:
        logger.error(result.stderr)
        return 31
    return 0

if __name__ == "__main__":
    config = sys.arg[1]
    return_value = save(config)
