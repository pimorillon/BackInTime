#!/usr/bin/python3

import os
import logging
import logging.handlers
import time

from utils import remountFS,find_users_conf
from modules.readConfiguration import readConfiguration
from modules.save import save
from modules.rotation import rotation
from modules.rootLogger import save_logging_configuration, restore_logging_configuration

def backup(user,source,config_files,root_flag=False,users=None):
    logger = logging.getLogger(__name__)
    config = readConfiguration(user,source,config_files)
    global mount_directory
    global is_mount_readonly
    mount_directory = config["Destination"]['directory']
    is_mount_readonly = config["Destination"]['read-only']

    #Remove initial logger only on root instance and exclude users home directory
    #Do I really want to remove syslog handler?
    if root_flag:
        logger.removeHandler(syslog_handler)
        syslog_handler.close() 
        for user in users:
            #users[user][1] is the path to the user's conf file
            config["Source"]['exclude'].append(users[user][1])

    if not root_flag:
        root_logging = save_logging_configuration()

    logging.basicConfig(filename=config["Log"]["directory"]+config["Log"]["name"],\
            format="%(asctime)s [%(levelname)s] %(message)s",\
            datefmt='%d/%m/%Y %H:%M:%S', encoding='utf-8',\
            level=config["Log"]["level"],force=True)
    
    if config["Destination"]['mountpoint']:
        statvfs = os.statvfs(config["Destination"]['directory'])
        ST_RDONLY = getattr(os, 'ST_RDONLY', 1)
    if bool(statvfs.f_flag & ST_RDONLY):
        remountFS(config["Destination"]['directory'],'rw',logger)

    save_start = time.time()
    return_value = save(user,config)

    if return_value != 0 and return_value < 30:
        if config["Destination"]['read-only']:
            remountFS(config['Destination']['directory'],'ro',logger)
        return 1

    save_end = time.time()
    save_time = save_end - save_start
    logging.info("Backup time: %s",save_time)
    
    if return_value == 0:
        rotation(config['Destination']['directory'],\
                config['Destination']['name'],\
                config['Rotation']['number_backups_keep'],\
                config['Rotation']['duration_backups_keep'])
    
        rotation_end = time.time()
        rotation_time = rotation_end - save_end
        logging.info("Rotation time: %s",rotation_time)
    
    if not root_flag:
        restore_logging_configuration(root_logging)

    return 0


start = time.time()
logger = logging.getLogger(__name__)

# Set up logging to the system logger (journalctl via syslog)
syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
syslog_formatter = logging.Formatter("[%(levelname)s] %(message)s", datefmt='%d/%m/%Y %H:%M:%S')
syslog_handler.setFormatter(syslog_formatter)
logger.addHandler(syslog_handler)

if not os.path.isfile("/etc/BackToTheFile/settings.conf"):
    logger.error(f"Configuration file  /etc/BackToTheFile/settings.conf does not exist. Exiting program")
    exit(40)
root_conf = ("/etc/BackToTheFile/settings.conf")

users = find_users_conf()

#Root instance
return_value = backup('root','/',[root_conf],True,users)
if return_value != 0:
    exit(return_value)

for user in users:
    conf_list = [root_conf]
    # users[user][0] is home directory, [1] is conf file
    conf_list.append(users[user][1])
    logger.info("Starting backup of user %s",user)
    backup(user,users[user][0],conf_list)
    logger.info("Finished backup of user %s",user)

if is_mount_readonly : 
    remountFS(mount_directory,'ro',logger)

end = time.time()
total_time = end - start
logging.info("Total time: %s",total_time)
