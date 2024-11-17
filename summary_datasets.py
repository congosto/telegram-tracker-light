# -*- coding: utf-8 -*-

# import modules
import pandas as pd
import dask.dataframe as dd
import os
import sys
# import submodules
from tqdm import tqdm
from datetime import datetime
from utils import (
	chats_dataset_columns,
	chats_dataset_dtypes,
	msgs_dataset_columns,
	msgs_dataset_dtypes
	)
data_path = './data'
dataset_path = './dataset'
output_path = './summary'
dataset_info_file = 'collected_chats.csv'
dataset_msgs = 'msgs_dataset.csv'
output_file = os.path.join(output_path,'summary_datasets.xlsx')
output_file_wrongs = os.path.join(output_path,'wrong_datasets.csv')
if not os.path.exists(output_path):
	os.makedirs(f'{output_path}', exist_ok=True)
f_wrong = open(output_file_wrongs, 'w')
first_dataset = True
datasets = [nombre for nombre in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path,nombre))]
cols = ['dataset', 'mode', 'num_channels', 'num_channels_downloaded','num_channels_no_downloaded',
				'num_channels_next_level', 'num_msgs','last_download']
summary_datasets = pd.DataFrame(columns=cols)
for dataset in tqdm(datasets, desc="find datasets", unit="dataset"):
	dataset_info = os.path.join(dataset_path,dataset, dataset_info_file)
	#get dataset data
	try:
		if dataset.endswith("_n2"):
			mode = 'snowball'
			channel_list_file = os.path.join(data_path,dataset[:-3],'related_channels.csv')
		else:
			mode = 'list_channels'
			channel_list_file = os.path.join(dataset_path,dataset,'channel_list.csv')
		channel_list = pd.read_csv(channel_list_file, low_memory=False)
		num_channels = len (channel_list) + 1
	# Read profiles
		with open(dataset_info, 'r', encoding='utf-8', errors='replace') as file: 
			df = pd.read_csv(
				file,
				sep=',',
				low_memory=False,
				usecols=chats_dataset_columns(),
				dtype=chats_dataset_dtypes(),
				on_bad_lines='skip'
		)
		num_channels_next_level = len (df)
		msgs_file = os.path.join(dataset_path, dataset, dataset_msgs)
		with open(msgs_file, 'rb') as f:
			num_msgs = sum(1 for line in f) 
		log_file = os.path.join(dataset_path, dataset, 'context', f'{dataset}_log.csv')
		log = pd.read_csv(log_file)
		num_channels_downloaded = len(log)
		num_channels_no_downloaded = num_channels - num_channels_downloaded
		# Get last row
		last_row = log.iloc[-1]
		date_obj = datetime.strptime(last_row ['date'], "%Y-%m-%d %H:%M:%S.%f")
		last_download = date_obj.strftime("%Y-%m-%d %H:%M:%S")
		summary_datasets.loc[len(summary_datasets)] = [dataset, mode, num_channels, num_channels_downloaded,
												num_channels_no_downloaded, num_channels_next_level, num_msgs, last_download]
	except Exception as e:
		f_wrong.write (f'{dataset}, {e}\n')
	except KeyboardInterrupt:
		print ('\nGoodbye!')
		sys.exit(0)
summary_datasets.to_excel(output_file, index=False)
f_wrong.close()
print(f'summay datasets in {output_file}\n')
print(f'wrong datasets in in{output_file_wrongs}\n')





