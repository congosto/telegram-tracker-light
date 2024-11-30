
# -*- coding: utf-8 -*-

# import modules
import os
import sys
import argparse
from datetime import datetime
import pandas as pd
import subprocess
import logging 
from utils import (
	log_management, put_last_download_context,create_dirs
)
if os.name == 'nt':
	copy = 'copy'
else:
	copy = 'cp'
#defino argumentos de script

'''
Start script
'''

start_time = datetime.now()
print(f"Script start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

'''
Arguments

'''

'''
dataset name'''
parser = argparse.ArgumentParser(description='Arguments.')

parser.add_argument(
	'--dataset-name',
	type=str,
	required=True,
	help='Specify a name for dataset'
)
'''
channel-list
'''
parser.add_argument(
	'--channel-list',
	type=str,
	required=True,
	help='Specify a file with the list of channels'
)

'''
Output
'''
parser.add_argument(
	'--output',
	'-o',
	type=str,
	required = False,
	default = './dataset',
	help='Folder to save collected data. Default: `./dataset`'
)
'''
max-msgs
'''
parser.add_argument(
	'--max-msgs',
	type=int,
	required=False,
	help='Maximum number of messages to download. Default: all messages'
)

'''

parse arguments

'''

args = vars(parser.parse_args())
dataset_name = args['dataset_name']
channel_list = args['channel_list']
dataset_path = args['output']
if args['max_msgs']:
	max_msgs = args['max_msgs']
	limit = f'--max-msgs {max_msgs}'
else:
	limit = ''


'''
Create dirs
'''
data_path = './data'
create_dirs(f'{dataset_path}/{dataset_name}', subfolders=None)
exceptions_path = os.path.join(dataset_path, dataset_name,'_exceptions-channels.txt')
logging.basicConfig(filename= exceptions_path, level=logging.ERROR)
'''
iterate channels

Search for each channel in the channel database. 
If it exists, it will be updated with the latest posts.
If it does not exist, all posts will be downloaded.
'''
if not os.path.exists(channel_list):
	print(f'{channel_list} does not exist')
else:
	channel_list_path = os.path.join(dataset_path, dataset_name, 'channel_list.csv')
	with open(channel_list, 'r') as inputfile:
		channels = inputfile.readlines()
	with open(channel_list_path, 'w') as outputfile:
		for channel in channels:
			outputfile.write(f"{channel}")
		outputfile.close()
	num_channels = len (channels)
	i = 1
	(f_log, list_downloaded) = log_management(f'{dataset_path}/{dataset_name}',f'{dataset_name}_log.csv')
	for channel in channels:
		channel = channel.strip('\n') # remove line break
		if channel in list_downloaded.values:
			print(f'--------> already downloaded {channel} ({i} of {num_channels})')
			i += 1
		else:
			print(f'--> downloading {channel} ({i} of {num_channels}) ')
			try:
				result = subprocess.run(['python', 'main.py','--telegram-channel', f'{channel}'],
														check=True, text=True, capture_output=False, stderr=subprocess.PIPE
				)
			except subprocess.CalledProcessError as e:
				# subprocess.run always return error. The result is stored in the error log if stderr is an empty string
				if e.stderr != '':
					logging.error (f'{datetime.now()},Exception , {channel}, {e.stderr}') 
			#Read msgs CSV file 
			try:
				if os.path.exists(f'{data_path}/{channel}/collected_chats.csv'):
					print(f'----> Reading CSV file...{data_path}/{channel}/collected_chats.csv')
					df = pd.read_csv(f'{data_path}/{channel}/collected_chats.csv')
					print(f'--------> append {channel} data to {dataset_name} ')
					# Append to dataset CSV file 
					if not os.path.exists(f'{dataset_path}/{dataset_name}/collected_chats.csv'):
						df.to_csv(f'{dataset_path}/{dataset_name}/collected_chats.csv',
							mode='w',
							encoding='utf-8',
							index=False)
					else:
						df.to_csv(f'{dataset_path}/{dataset_name}/collected_chats.csv',
							encoding='utf-8',
							mode='a',
							header = False,
							index=False)
					# Read msgs CSV file
					print(f'----> Reading CSV file...{data_path}/{channel}/msgs_dataset.csv')
					df = pd.read_csv(f'{data_path}/{channel}/msgs_dataset.csv') 
					print(f'--------> append {channel} data to {dataset_name} ')
					# Append to dataset CSV file  
					if not os.path.exists(f'{dataset_path}/{dataset_name}/msgs_dataset.csv'):
						df.to_csv(f'{dataset_path}/{dataset_name}/msgs_dataset.csv',
							mode='w',
							encoding='utf-8',
							index=False)
					else:
						df.to_csv(f'{dataset_path}/{dataset_name}/msgs_dataset.csv',
						mode='a',
						encoding='utf-8',
						header = False,
						index=False)
					f_log.write(f'{channel},downloaded,{datetime.now()}\n')
					f_log.flush()
				i += 1
			except KeyboardInterrupt:
				print ('\nGoodbye!')
				sys.exit(0)
			except Exception as e:
				print('paso-4')
				print (f'\n¡¡¡ An exception has happened, ruled out {channel}!!!')
				logging.error (f'{datetime.now()},Exception , {channel}, {str(e)}') 
				i += 1
	f_log.close()
	'''

	Remove duplicate channel metadata

	'''
	print(f'--------> remove duplicates of {dataset_path}/{dataset_name}/collected_chats.csv')
	df = pd.read_csv(
	f'{dataset_path}/{dataset_name}/collected_chats.csv',
	encoding='utf-8',
	low_memory=False
	)
	df.drop_duplicates(subset=['id'], keep='last', inplace=True) 
	df.to_csv(
		f'{dataset_path}/{dataset_name}/collected_chats.csv',
		mode='w',
		index=False,
		encoding='utf-8'
	)


'''
End script
'''
print(f'Last {datetime.now()- start_time} ')




