# -*- coding: utf-8 -*-

# import modules
import pandas as pd

import os
import sys
# import submodules
from tqdm import tqdm
from datetime import datetime
from utils import (
	chats_dataset_columns,
	chats_dataset_dtypes
	)

data_path = './data'
channel_path = './data'
channel_info_file = 'collected_chats.csv'
channel_msgs = 'msgs_dataset.csv'
output_file = os.path.join(data_path,'summary_channels.xlsx')
output_file_wrongs = os.path.join(data_path,'wrong_channels.csv')
f_wrong = open(output_file_wrongs, 'w')

first_channel = True
channels = [nombre for nombre in os.listdir(data_path) if os.path.isdir(os.path.join(data_path,nombre))]
for channel in tqdm(channels, desc="find channels", unit="channel"):
	channel_info = os.path.join(data_path,channel, channel_info_file)
	#get channel data
	try:
	# Read profiles
		with open(channel_info, 'r', encoding='utf-8', errors='replace') as file: 
			df = pd.read_csv(
				file,
				sep=',',
				low_memory=False,
				usecols=chats_dataset_columns(),
				dtype=chats_dataset_dtypes(),
				on_bad_lines='skip'
		)
		df = df[['id', 'username', 'title', 'participants_count', 'date', 'creator', 'left', 'broadcast',
						 'verified', 'megagroup', 'gigagroup', 'restricted', 'fake', 'noforwards', 'join_to_send',
						  'join_request']]
		# Read log
		log_file = os.path.join(data_path, channel, 'context', f'{channel}_log.csv')
		log = pd.read_csv(log_file)
		# Get last row
		last_row = log.iloc[-1]
		# Read msgs
		msgs_file = os.path.join(data_path, channel, channel_msgs)
		msgs = pd.read_csv(msgs_file, low_memory=False)
		if { 'date', 'number_replies', 'number_forwards'}.issubset(msgs.columns):
			num_msgs = len(msgs)
			if num_msgs > 0:
				msgs['date'] = pd.to_datetime(msgs['date'], format= '%Y-%m-%d %H:%M:%S%z', errors='coerce')
				date_first_message = pd.to_datetime(msgs['date']).min().strftime('%Y-%m-%d %H:%M:%S%z')
				date_last_message = pd.to_datetime(msgs['date']).max().strftime('%Y-%m-%d %H:%M:%S%z')
				total_replies = msgs['number_replies'].sum()
				total_forwards = msgs['number_forwards'].sum()
			else:
				date_first_message = None
				date_last_message = None
				total_replies = 0
				total_forwards = 0
			# Add new columns to summary
		row = df.loc[df['username'] == channel]
		if len(row) > 0:
			df.loc[df['username'] == channel, 'num_msgs'] = num_msgs
			df.loc[df['username'] == channel, 'date_first_message'] = date_first_message
			df.loc[df['username'] == channel, 'date_last_message'] = date_last_message
			df.loc[df['username'] == channel, 'total_forwards'] = total_forwards
			df.loc[df['username'] == channel, 'total_replies'] = total_replies
			df.loc[df['username'] == channel, 'last_msg'] = last_row ['last_msg']
			last_download = datetime.strptime(last_row ['time_download'], "%a %b %d %H:%M:%S %Y")
			last_download = last_download.strftime("%Y-%m-%d %H:%M:%S")
			df.loc[df['username'] == channel, 'time_download'] = last_download
			row = df.loc[df['username'] == channel]
			if first_channel:
				summary_channels = row
				first_channel = False
			else:
				summary_channels = pd.concat([summary_channels, row],ignore_index=True)
		else:
			f_wrong.write (f'{channel}, mala estructura\n')
	except Exception as e:
		f_wrong.write (f'{channel}, {e}\n')
		#print(f'happened an error: {e} in {channel} ')
	except KeyboardInterrupt:
		print ('\nGoodbye!')
		sys.exit(0)
summary_channels.to_excel(output_file, index=False)
f_wrong.close()
print(f'summay channels in {output_file}\n')
print(f'wong channels in in{output_file_wrongs}\n')





