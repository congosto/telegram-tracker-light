# -*- coding: utf-8 -*-

# import modules
import pandas as pd
import argparse
import asyncio
import nest_asyncio # change by congosto
import tempfile
import json
import time
import sys
import os
import logging 
# import submodules
from datetime import datetime
from tqdm import tqdm
# import Telegram API submodules
from api import *
from utils import (
	get_config_attrs, create_dirs, 
	write_collected_chats,get_last_download_context,
	put_last_download_context,store_channels_download,store_channels_related,
	msgs_dataset_columns,chats_dataset_columns, chats_dataset_dtypes, write_collected_msgs
)



'''

Arguments

'''

parser = argparse.ArgumentParser(description='Arguments.')
parser.add_argument(
	'--telegram-channel',
	type=str,
	required=True,
	help='Specifies a Telegram Channel.'
)

parser.add_argument(
	'--limit-download-to-channel-metadata',
	action='store_true',
	help='Will collect channels metadata only, not posts data.'
)

# chaged by congosto
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

Output
'''
parser.add_argument(
	'--output',
	'-o',
	type=str,
	default='./data',
	required=False,
	help='Folder to save collected data. Default: `./data`'
)


# parse arguments
args = vars(parser.parse_args())
config_attrs = get_config_attrs()

args = {**args, **config_attrs}

text = f'Init program at {time.ctime()}'
print (text)


'''

Variables

'''

# Telegram API credentials

'''

FILL API KEYS
'''
sfile = 'session_file'
api_id = args['api_id']
api_hash = args['api_hash']
phone = args['phone']

# event loop
# Change by congosto
nest_asyncio.apply()
loop = asyncio.get_event_loop()

# data collection
counter = {}

'''

> Get Client <API connection>

'''

# get `client` connection
client = loop.run_until_complete(
	get_connection(sfile, api_id, api_hash, phone)
)

# request type
channel = args['telegram_channel']

# chaged by congosto
# reading | max-msgs
if args['max_msgs']:
	max_msgs = args['max_msgs']
	limited_msgs = True
else:
	limited_msgs = False
	max_msgs = 0  # not limitedf
output = args['output']
output_folder= f'{output}/{channel}'
# create dirs
channel_id = create_dirs(output_folder) # If channel exists, returns its ID
exceptions_path = os.path.join(output_folder,'_exceptions-channels.txt')
logging.basicConfig(filename= exceptions_path, level=logging.ERROR) 

'''

Methods

- GetHistoryRequest
- SearchGlobalRequest

'''

#change by congosto
'''
Channels are downloaded one by one
'''
	
# add by congosto
'''
get context download
'''
(start_msg,num_msgs_downloaded) = get_last_download_context(f'{output_folder}/context/{channel}_log.csv')

'''

Process arguments
-> channels' data

-> Get Entity <Channel's attrs>
-> Get Full Channel request.
-> Get Posts <Request channels' posts>

'''

# new line
print ('')
print (f'> Collecting data from Telegram Channel -> {channel}')
print ('> ...')
print ('')

channel_request = None
while True:
	try:
		if  channel_id == None:
			entity_attrs = loop.run_until_complete(
				get_entity_attrs	(client, channel)
				)
			#Get Channel ID | convert output to dict
			if  entity_attrs:
				channel_id = entity_attrs.id
			else:
				logging.error (f'{datetime.now()},Error,{channel}, ID not found')
				break
		# Collect Source -> GetFullChannelRequest
		channel_request = loop.run_until_complete(
			full_channel_req(client, channel_id)
		)
		print('Get entity attribs')
		break
	except errors.FloodWaitError as e:
		# e.seconds contiene el número de segundos que debes 
		print(f'ratelimit at {datetime.now()}')
		hours, remainder = divmod(e.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		print(f'Flood wait for {e.seconds} seconds ({hours} hours, {minutes} minutes y {seconds} seconds)')
		time.sleep (e.seconds)
	except Exception as e:
		print (f'¡¡¡ An exception has happened, ruled out {channel} {str(e)}!!!\n')
		print(str(e), file=sys.stderr)
		logging.error (f'{datetime.now()},Exception ,{channel}, {str(e)}')
		break
		


'''

collected chats

'''


if channel_request != None:
	
	# save full channel request
	full_channel_data = channel_request.to_dict()
	# collect chats
	chats_path = f'{output_folder}/chats.txt'
	chats_file = open(chats_path, mode='a', encoding='utf-8')
	# channel chats
	counter = write_collected_chats(
	full_channel_data['chats'],
		chats_file,
		channel,
		counter,
		'channel_request',
		client,
		output_folder
	)
	'''

	collected messages

	'''
	# collect messages
	msgs_path = f'{output_folder}/msgs_dataset.csv'
	
	last_msg = start_msg
	num_msgs = 0
	min_id = start_msg
	if not args['limit_download_to_channel_metadata']:
		# Collect posts
		if start_msg == 0: # changed by congosto
			print('Downloading all messages')
			posts = loop.run_until_complete(
				get_posts(client, channel_id)
			)
		else:
			print(f'Downloading from msg {start_msg}')
			posts = loop.run_until_complete(
				get_posts(client, channel_id, min_id=min_id)
			)

		data = posts.to_dict()

		# Change by Congosto
		'''
		get most recent msg 
		'''
		pbar_flag = False
		if len(posts.messages) > 0:
			msgs_tmp = tempfile.NamedTemporaryFile(delete=False)
			write_collected_msgs (data['messages'], channel, data['chats'],msgs_tmp.name)
			offset_id = min([i['id'] for i in data['messages']])
			last_msg = data['messages'][0]['id']
			num_msgs = len(posts.messages)
			pbar = tqdm(total=last_msg - start_msg, desc = 'Downloading posts', file=sys.stdout)
			pbar_flag = True
		# Get offset ID | Get messages
		while len(posts.messages) > 0:
			if start_msg > 0: # changed by congosto
				posts = loop.run_until_complete(
					get_posts(
						client,
						channel_id,
						min_id=min_id,
						offset_id=offset_id
					)
				)	
			else:
				posts = loop.run_until_complete(
					get_posts(
						client,
						channel_id,
						offset_id=offset_id
					)
				)
			# Update data dict
			if posts.messages:
				tmp = posts.to_dict()

				# Adding unique chats objects
				all_chats = [i['id'] for i in data['chats']]
				chats = [
					i for i in tmp['chats']
					if i['id'] not in all_chats
				]
				# channel chats in posts
				counter = write_collected_chats(
					tmp['chats'],
					chats_file,
					channel,
					counter,
					'from_messages',
					client,
					output_folder
				)
				# Adding unique users objects
				all_users = [i['id'] for i in data['users']]
				users = [
					i for i in tmp['users']
					if i['id'] not in all_users
				]
				# extend UNIQUE chats & users
				data['chats'].extend(chats)
				data['users'].extend(users)
				write_collected_msgs (tmp['messages'], channel, data['chats'],msgs_tmp.name)
				# Get offset ID
				offset_id = min([i['id'] for i in tmp['messages']])
				'''
				get most recent msg and show post downloaded
				'''
				num_msgs = num_msgs + len(posts.messages)
				pbar.update(len(posts.messages))
				if limited_msgs & (num_msgs >= max_msgs):
					break
		# Close pbar connection
		if pbar_flag:
			pbar.close()
else:
		'''
		Channel not found or is private or you lack permission to access it
		'''
		logging.error (f'{datetime.now()},Error, {channel}, channel not downloaded')
		sys.exit(0)
'''

Clean generated chats text file

'''

# close chat file
chats_file.close()

# get collected chats
collected_chats = list(set([
	i.rstrip() for i in open(chats_path, mode='r', encoding='utf-8')
]))

# re write collected chats
chats_file = open(chats_path, mode='w', encoding='utf-8')
for c in collected_chats:
	chats_file.write(f'{c}\n')

# close file
chats_file.close()


# Process counter
counter_df = pd.DataFrame.from_dict(
	counter,
	orient='index'
).reset_index().rename(
	columns={
		'index': 'id'
	}
)

# save counter
counter_df.to_csv(
	f'{output_folder}/counter.csv',
	encoding='utf-8',
	index=False
)

# merge dataframe
with open(f'{output_folder}/collected_chats.csv', 'r', encoding='utf-8', errors='replace') as file: 
	df = pd.read_csv(
				file,
				sep=',',
				low_memory=False,
				usecols=chats_dataset_columns(),
				on_bad_lines='skip'
		)

#remove possible duplicates
df.drop_duplicates(subset=['id'], keep='last', inplace=True) # Change by Congosto

df.to_csv(
	f'{output_folder}/collected_chats.csv',
	mode='w', # Change by Congosto  avoid duplicates
	index=False,
	encoding='utf-8'
)

# Change by Congosto
'''
Save names of related channels
'''
users_names = df["username"]
users_names.to_csv(
	f'{output_folder}/related_channels.csv',
	mode='w', 
	header=False,
	index=False,
	encoding='utf-8'
)
del counter_df['username'] 
df = df.merge(counter_df, how='left', on='id')
'''
The metadata and counters are saved in collected_chats_full.csv,
to avoid problems when making 
 successive merges when extracting the channel data again
'''
df.to_csv(
	f'{output_folder}/collected_chats_full.csv',
	mode='w', # Change by Congosto para que no duplique entradas
	index=False,
	encoding='utf-8'
)

'''
store msgs in csv
 '''
 # merge dataframe
if 'msgs_tmp' in globals():
	if os.name == 'nt':
		append = 'type'
	else:
		append = 'cat'
	print (f'stored channel messages {channel}')
	# Put head to msgs_path if not exit
	if not os.path.exists(msgs_path):
		df = pd.DataFrame(columns = msgs_dataset_columns())
		df.to_csv(
			msgs_path,
			mode='w', 
			index=False,
			encoding='utf-8'
			)
	path_msgs_nor = os.path.normpath(msgs_path)
	path_tmp_nor = os.path.normpath(msgs_tmp.name)
	print(f'{append} {path_tmp_nor} >> {path_msgs_nor}')
	os.system(f'{append} {path_tmp_nor} >> {path_msgs_nor}')
	msgs_tmp.close()
	os.remove(msgs_tmp.name)
'''
Save downloaded context
'''
put_last_download_context(f'{output_folder}/context/{channel}_log.csv',time.ctime(),last_msg,num_msgs)


'''
Save collected_channel
'''

store_channels_download(f'./{output_folder}/context/collected_channel_log.csv',channel,output_folder)
# log results

'''
Save related_channel
'''
store_channels_related(f'./{output_folder}/context/related_channel_log.csv',users_names,output_folder)

# log results
text = f'End program at {time.ctime()}'

print (text)
sys.exit(0)