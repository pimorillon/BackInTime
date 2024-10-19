#!/usr/bin/python3

import os
import configparser
import logging
from datetime import date

from utils import addLastSlashToDir

hostname = os.uname().nodename

def interpretVariableInConfigFile(string):
#Replace $USER and $HOST by actual values. Case insensitive.
    dollar_indexes = []
    for index,character in enumerate(string):
        if character == '$':
            dollar_indexes.append(index)
            dollar_indexes.reverse()
    for index in dollar_indexes:
        if string[index+1:index+5].upper() == 'USER':
            string = string[:index] + user_name + string[index+5:] 
        elif string[index+1:index+5].upper() == 'HOST':
            string = string[:index] + hostname + string[index+5:] 
        else:
            return True,string
    return False,string

def areAllOptionsPresent(config,mandatory,logger):
#mandatory is a dictionnary where keys are the  mandatories sections 
#   and values the list of mandatories options for each section.
    flag = True
    for section in mandatory:
        for option in mandatory[section]:
            if not config.has_option(section,option):
                logger.error("Missing mandatory option %s in %s section",option,section)
                flag = False
    return flag

       

def readConfiguration(user,source,ini_files):
    logger = logging.getLogger(__name__)
    config = configparser.ConfigParser()
    global user_name
    user_name = user

    #Mandatories option for the root ini_files
    #Will be changed at the end of the first iteration of following for loop
    mandatory = {"Destination" : ["directory","mountpoint","read-only",'name'],
                }
    #These options can only be set in the root configuration file
    non_modifiable_keys = {"Destination" : ["directory","mountpoint","read-only",'name']}

    # Initialize a dictionary with default configuration for non mandatory options
    final_config = {"Source" : {"frequency" : 1, "exclude" : None},
                    "Log" : {"directory" : "/var/log/backup/", "name" : "backtothefile.log","level" :"WARNING"},
                    "Rotation" : {"number_backups_keep" : 3, "duration_backups_keep" : 30}
                    }

 
    for ini_file in ini_files:
        #Reset Exclude list
        if "Source" in final_config:
            if "Exclude" in final_config["Source"]:
                final_config["Source"]["Exclude"] = None

        config.read(ini_file)
        if not areAllOptionsPresent(config,mandatory,logger):
            logger.critical("At least one mandatory option is absent from %s", ini_files[0])
            exit(41)
 
        for section in config.sections():
            if section not in final_config:
                final_config[section] = {}
 
            for key, value in config.items(section):
                # Check if the current section-key pair is in the non-modifiable list
                if section in non_modifiable_keys and key in non_modifiable_keys[section]:
                    # If the key was already defined in this section, skip updating it
                    if key in final_config[section]:
                        continue
                final_config[section][key] = value
        final_config["Source"]['directory'] = source 
        sanitize(final_config,ini_file,logger)
        #Only mandatory section in the user ini file is Frequency
        mandatory = {"Source" : ["frequency"]}

    return final_config

def sanitize(config,ini_file,logger):
    for section in ['Destination','Source','Log']: 
        config[section]['directory'] = addLastSlashToDir(config[section]['directory'])
        if not os.path.exists(config[section]['directory']):
            logger.error("%s directory %s configured in %s does not exists" \
                    ,section,config[section]['directory'],ini_file)
            exit(42)

    for boolean_option in ['mountpoint','read-only']:
        if isinstance(config['Destination'][boolean_option],bool):
            continue

        if config['Destination'][boolean_option].lower() == "true":
            config['Destination'][boolean_option] = True
        elif config['Destination'][boolean_option].lower() == "false":
            config['Destination'][boolean_option] = False
        else:
            logger.error("%s in Destination section configured in %s is not set to True or False" \
                    ,boolean_option,ini_file)
            exit(43)

    #Read-Only should be set to True only if Mountpoint is also set to True
    if config['Destination']['read-only'] and not config['Destination']['mountpoint']:
        logger.error("Read-Only is True but Mountpoint is False. Please verify %s",ini_file)
        exit(44)

    #if Mountpoint is True, we check that is actually a mountpoint
    if config['Destination']['mountpoint'] and not os.path.ismount(config['Destination']['directory']):
        logger.error("%s is not a mount point but is configured as such. Please verify /etc/fstab"\
                ,config['Destination']['directory'])
        exit(45)


    for section in ['Destination','Log']: 
        warn, config[section]['name']  = interpretVariableInConfigFile(config[section]['name'])
        if warn:
            logger.warning("Name in %s section configured in %s cannot be interpreted. Only $USER and $HOST are accepeted as variable"\
                    ,section,ini_file)

    date_today = str(date.today())
    config['Destination']['full_path'] = config['Destination']['directory'] + \
            config['Destination']['name'] + '-' + date_today + '/'
    
    frequency = config['Source']['frequency']
    if str(frequency.isdigit()):
        config['Source']['frequency'] = frequency
    elif frequency.lower() == 'daily':
        config['Source']['frequency'] = 1
    elif frequency.lower() == 'weekly':
        config['Source']['frequency'] = 7
    elif frequency.lower() == 'monthly':
        config['Source']['frequency'] = 28
    elif frequency.lower() == 'none':
        config['Source']['frequency'] = 0
    else:
        logger.error("Cannot interpret Frequency configured in %s. Should be a integer or None, Daily, Weekly or Monthly",ini_file)
        exit(46)

    exclude = config['Source']['exclude']
    if exclude == '':
        config['Source']['exclude'] = []
    else:
        config['Source']['exclude'] = exclude.split(',')
    for index,value in enumerate(config['Source']['exclude']):
        config['Source']['exclude'][index] = addLastSlashToDir(value)
        

    if config['Log']['level'].upper() in ['DEBUG','INFO','ERROR','CRITICAL']:
        config['Log']['level'] = config['Log']['level'].upper()
    else:
        config['Log']['level'] = 'WARNING'

    if str(config['Rotation']['number_backups_keep']).isdigit():
        config['Rotation']['number_backups_keep'] = int(config['Rotation']['number_backups_keep'])
    else:
        logger.error('number_backups_keep configured in %s should be an integer',ini_file)
        exit(47)

    if str(config['Rotation']['duration_backups_keep']).isdigit():
        config['Rotation']['duration_backups_keep'] = int(config['Rotation']['duration_backups_keep'])
    else:
        logger.error('duration_backups_keep configured in %s should be an integer',ini_file)
        exit(48)


    return True
