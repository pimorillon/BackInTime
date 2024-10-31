#!/usr/bin/python3
import os
import logging

from collections import defaultdict
from datetime import datetime

from utils import extract_timestamp, is_valid_backup_directory

def collect_files(directories,logger):
#Collect files in each backup directory
    file_info = defaultdict(list)

    for directory in directories:
        timestamp = extract_timestamp(directory)
        if timestamp is None:
            logger.warning("Skipping directory %s: Invalid timestamp format",directory)
            continue

        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
            #Ignore symlink to avoid counting several times same file
                if os.path.islink(file_path):
                    continue
                try:
                    #Get inode information (to check for hard links)
                    stat_info = os.stat(file_path)
                    inode = stat_info.st_ino
                    #Store the file path and its timestamp
                    file_info[inode].append((file_path, timestamp))
                except FileNotFoundError:
                    continue

    return file_info

def clean_old_files(file_info, keep_count=3,logger):
#Keep only the specified number of copies
    for inode, file_versions in file_info.items():
        if len(file_versions) > keep_count:
            # Sort by directory timestamp (most recent first)
            file_versions.sort(key=lambda x: x[1], reverse=True)
            to_delete = file_versions[keep_count:]
            for file_path, _ in to_delete:
                logger.info("Deleting %s",file_path)
                os.remove(file_path)

def rotation(directory,name,keep_count,keep_duration):
    logger = logging.getLogger(__name__)

    directories = []
    for entry in os.listdir(directory):
        path = os.path.join(directory, entry)
        if os.path.isdir(path) and is_valid_backup_directory(entry, name):
            directories.append(path)

    directories.sort(key=extract_timestamp, reverse=True)
    file_info = collect_files(directories,logger)
    clean_old_files(file_info, keep_count,logger)

