
# -*- coding: utf-8 -*-

# import modules
import os
import sys
from datetime import datetime
import time
from tqdm import tqdm
import pandas as pd
import subprocess
import logging
from utils import (
	log_management, put_last_download_context,create_dirs
)

'''
Start script
'''

start_time = datetime.now()
print(f"Script start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

data_path = './data'
output_path = './update_channels'
create_dirs(f'{output_path}', subfolders=None)
exceptions_path = os.path.join(output_path,'_exceptions-channels.txt')
logging.basicConfig(filename= exceptions_path, level=logging.ERROR)
flood_wait = 300 #seconds
'''
iterate channels

Searches all channels in the data repository and updates them with the latest messages.
To avoid the rate limit when querying metadata, it orders the channels from most 
to least active and mixes them so that the metadata query is less frequent,
since downloading messages causes requests to be spaced out.
'''
# fin
channels = [nombre for nombre in os.listdir(data_path) if os.path.isdir(os.path.join(data_path,nombre))]
channel_size = {}
for channel in tqdm(channels, desc="find channels", unit="channel"):
	channel_context = os.path.join(data_path,channel,'context', f'{channel}_log.csv')
	if os.path.exists(channel_context):
		context = pd.read_csv(channel_context)
		# Get last row
		last_row = context.iloc[-1]
		channel_size[channel] = last_row['last_msg']
channels_order_desc = sorted(channel_size.items(), key=lambda x: x[1], reverse=True)
channels_order_asc = sorted(channel_size.items(), key=lambda x: x[1])
# mix channels
num_channels = len (channels_order_desc)
channels_mix = [val for pair in zip(channels_order_desc, channels_order_asc) for val in pair]
channels_mix = channels_mix[:num_channels]
i = 1
channels_list = [x[0] for x in channels_mix]
(f_log, list_downloaded) = log_management(f'{output_path}','update_channels_log.csv')
for channel in channels_list:
	if channel in list_downloaded.values:
		print(f'--------> already downloaded {channel} ({i} of {num_channels})')
	else:
		print(f'--> downloading {channel} ({i} of {num_channels}) ')
		try:
			time_ini_update = datetime.now()
			result = subprocess.run(['python', 'main.py','--telegram-channel', f'{channel}'],
													check=True, text=True, capture_output=False, stderr=subprocess.PIPE
			)
			f_log.write(f'{channel},downloaded,{datetime.now()}\n')
			f_log.flush()
		except subprocess.CalledProcessError as e:
			# subprocess.run always return error. The result is stored in the error log if stderr is an empty string
			if e.stderr != '':
				logging.error (f'{datetime.now()},Exception , {channel}, {e.stderr}')
			else: # No es error 
				f_log.write(f'{channel},downloaded,{datetime.now()}\n')
				f_log.flush()
				duration = (datetime.now() - time_ini_update).total_seconds()
		except KeyboardInterrupt:
			print ('\nGoodbye!')
			sys.exit(0)
		except Exception as e:
			print (f'\n¡¡¡ An exception has happened, ruled out {channel}!!!')
			logging.error (f'{datetime.now()},Exception , {channel}, {str(e)}') 
	i += 1
f_log.close()

'''
End script
'''
print(f'Last {datetime.now()- start_time} ')




