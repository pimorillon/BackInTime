# BackToTheFile

## Overview

This project is a python script that backup Linux based system. Intended for personal use.
It can use different configurations for user and for root. In practice, if a user has a .backtothefile.conf in their home directory, it will be saved apart from the root backup. At its core, it uses rsync and it's functionality to hard-link to make incremental saves.
The script check at midnight if another backup is necessary, depending on configuration. It also take care of rotation to not indefinitely use backup storage
Currently, it can only save the backup on a local disk.

## Installation



1.	Run install.sh /path/to/destination script as root.
2.	Configure the root config file /etc/BackToTheFile/settings.conf and optionally .backtothefile.conf for each user you wish to be backup separately,
3.	Run following command:

	    sudo systemctl enable backtothefile.timer

Then, it will take care for you of doing the backup depending of the frequency setting.
To restore a file, you can browse the location of the save and use rsync.

## Configuration

### Root file
You will find the root configuration file in /etc/BackToTheFile/settings.conf
The configuration here will be system-wide. It is a INI file. Here is a description of each option, with default configuration. Please note the Destination section need to be manually setup.

 - #### Destination

|Option |Explication  |Default |
|-|-|-|
|Directory  |Directory where to store all the backups  |None
|Mountpoint|Set to True if the backup directory is a independent mountpoint set in /etc/fstab (higly recommended)|None|
|Read-Only|Set to True if the backup directory should be read only when not used (higly recommended). Can be True only if Mountpoint is also True. In that case, don't forget the ro option in fstab|None|
|Name|Name of backup directories. Accept \$USER to get the username, $HOST for the hostname of the server(ie Name=\$USER@$HOST). Date (YYYY-MM-DD) will always be attached at the end|None

 - #### Source

|Option |Explication  |Default |
|-|-|-|
|Frequency  |Frequency at which backup will be taken. Frequency can be equal to a number of days, or None, Daily, Weekly or Monthly  |Daily
|Exclude|Exclude list, separated via comma. Files finishing with .bak extension and git directories are always excluded without further intervention. Also some directories are always excluded from / (see note below) |None|

Note: List of always excluded from / :
- /dev
- /efi
- /mnt
- /proc
- /run
- /sys
- /tmp
- /var/run
- /var/tmp
 - #### Log
 |Option |Explication |Default |
|-|-|-|
|Directory |Directory where to store the log files |/var/log/backup
|Name|Name of log. Accept \$USER to get the username, $HOST for the hostname of the server. If these variable are not used, all logs will form different user will be in the same file |backtothefile.log|
|Level|Set level of logging|Warning
 - #### Rotation
|Option |Explication |Default |
|-|-|-|
|Number_Backups_Keep |Number of different versions to keep for each file. Adapt to storage capacity|3
|Duration_Backups_Keep|Maximum number of days to keep a backup. 0 means to always keep oldest directory, until Number_Backups_Keep is reached|30

### User file
Each user that which to have a different backup from root can edit a .backtothefile.conf file in their home directory. In that case, their home directory will automatically be excluded from root. The file accept the same option as the root file except Destination section. If an option is not explicitly specified, it will keep the one configured in the root configuration file.

Please note if you want all log in the same directory (for example /var/log/backup), you should set a $USER in the Log Name of the root file **AND NOT** change it back in the user file. In practice it means you sould only set up the log level here.

## To-Do

 - Externalization support
 - Encrypt backup
 - Restoration command
 - Send-Notification setting


