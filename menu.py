# -*- coding: utf-8 -*-

# import modules
import os
import sys

if os.name == 'nt':
	copy = 'copy'
else:
	copy = 'cp'
exit = 'n'
data_path = './data'
dataset_path = './dataset'
try:
	while exit != 'y':
		print ('--------------------------------')
		print ('What function do you want to run?')
		print ('--------------------------------')
		print ('1. Get a channel')
		print ('2. Get a snowball from a channel')
		print ('3. Get a channel list')
		print ('4. Get charts')
		print ('5. get graph (gexf format)')
		print ('6. get summary (xlsx format)')
		print ('7. update channels')
		print ('8. Exit')
		print (' ')
		while True:
			try:
				option = int(input('--> Enter option: '))
				if option in range (1,9):
					break
				else:
					print('type a number from 1 to 7')
			except:
				print('type a number from 1 to 7')
			'''
			Get a channel
			'''
		if option == 1:
			channel = input ('Enter channel name: ')
			channel_path = f'{data_path}/{channel}'
			print(f'Output on {channel_path}')
			print(f'Download channel {channel}')
			os.system('python main.py' +
				f' --telegram-channel {channel}')
		'''
		Get a snowball from a user
		'''
		if option == 2:
			channel_root = input ('root channel (must have been downloaded before): ')
			channel_list = f'{data_path}/{channel_root}/related_channels.csv'
			if not os.path.exists(channel_list):
				print(f'{channel_root} must have been downloaded before')
			else:
				os.system('' +
					'python build-dataset.py' +
					f' --dataset-name {channel_root}_n2' +
					f' --channel-list {channel_list}') 
			'''
			Get a list channels
			'''
		if option == 3:
			dataset_name = input ('Enter dataset name: ')
			if not os.path.exists(f'{dataset_path}/{dataset_name}/channel_list.csv'):
				channel_list = input ('Enter file with the list of channels: ')
			else:
				channel_list = f'{dataset_path}/{dataset_name}/channel_list.csv'
			os.system('' +
				'python build-dataset.py' +
				f' --dataset-name {dataset_name}' +
				f' --channel-list {channel_list}')
			'''
			Get charts
			'''
		if option == 4:
			dataset_name = input ('Enter dataset or channel name: ')
			if os.path.exists(f'./data/{dataset_name}'):
				print(f'--------> draw charts from channel {dataset_name}')
				os.system (f'python draw_charts.py --channel {dataset_name}')
			elif os.path.exists(f'./dataset/{dataset_name}/'):
				print(f'--------> draw charts from dataset {dataset_name}')
				os.system (f'python draw_charts.py --dataset {dataset_name}')
			else:
				print(f'{dataset_name} does not exist')
			'''
			Get graph
			'''
		if option == 5:
			dataset_name = input ('Enter dataset or channel name: ')
			if os.path.exists(f'./dataset/{dataset_name}/'):
				print(f'--------> Get graph from dataset {dataset_name}')
				os.system (f'python net.py --dataset {dataset_name}')
			else:
				print(f'{dataset_name} does not exist')
			'''
			Get summary channels
			'''
		if option == 6:
			flag_dataset = input ('Dataset summary? (y | n) : ')
			flag_channel = input ('Channels summary? (y | n) : ')
			if flag_channel.lower() == 'y':
				if os.path.exists('./data'):
					print('--------> Get channels summary')
					os.system ('python ./summary_channels.py')
				else:
					print('data dir does not exist')
			if flag_dataset.lower() == 'y':
				if os.path.exists('./dataset'):
					print('--------> Get datasets summary')
					os.system ('python ./summary_datasets.py')
				else:
					print('datasets dir does not exist')
			'''
			update channels
			'''
		if option == 7:
			print('--------> update channels')
			os.system ('python ./update_channels.py')
			'''
			Exit
			'''
		elif option == 8:
			exit = 'y'
			break
except KeyboardInterrupt:
	print ('\nGoodbye!')
	sys.exit(0)



