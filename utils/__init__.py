# -*- coding: utf-8 -*-

# Import modules
import pandas as pd
import asyncio
import os
import re
import sys

# import submodules
from configparser import ConfigParser
from urllib.parse import urlparse
from datetime import datetime

# Import Telegram API submodules
from api import full_channel_req


'''
Creating functions
'''

# Get config attrs
def get_config_attrs():
	'''
	'''
	path = './config/config.ini'
	
	# config parser
	config = ConfigParser()
	config.read(path)

	# Telegram API credentials
	attrs = config['Telegram API credentials']
	return dict(attrs)
'''
manage context
'''

def log_management (path_dataset,log_file):
	log_path = f'{path_dataset}/context/{log_file}'
	if os.path.exists(log_path):
		print (f'--> context from  {log_path}')
		df = pd.read_csv(
				log_path,
				encoding='utf-8'
		)
		list_downloaded = df[df['type'] == 'downloaded']['channel']
		f_log = open(log_path, 'a')
	else:
		print (f'--> new context  {log_path}')
		os.makedirs(f'{path_dataset}/context/', exist_ok=True)
		f_log = open(log_path, 'a')
		f_log.write('channel,type,date\n')
		list_downloaded = pd.Series()
	return(f_log,list_downloaded)


# event loop
loop = asyncio.get_event_loop()

def check_channel (root):
	channel_id = None
	channel = os.path.basename(root)
	if not os.path.exists(root):
		os.makedirs(f'{root}', exist_ok=True)
	else:
		channel_info = f'{root}/collected_chats.csv'
		if os.path.exists(channel_info):
			with open(channel_info, 'r', encoding='utf-8', errors='replace') as file: 
				df = pd.read_csv(
					file,
					sep=',',
					low_memory=False,
					usecols=chats_dataset_columns(),
					dtype=chats_dataset_dtypes(),
					on_bad_lines='skip'
			)
			row = df.loc[df['username'].str.lower() == channel.lower()]
			if len(row) == 1:
				row.reset_index(drop=True, inplace=True)
				channel_id = int(row.loc[0,'id'])
	return channel_id

# Create new folders
def create_dirs(root, subfolders=None):

	root = root if subfolders == None else f'{root}/{subfolders}/'
	channel_id = check_channel(root)
	print(f'created {root}')
	# create dir context for logs
	if not os.path.exists(f'{root}/context'):
		os.makedirs(f'{root}/context', exist_ok=True)
		print(f'created {root}/context')
	if not os.path.exists(f'{root}/_exceptions-channels.txt'):
		with open(f'{root}/_exceptions-channels.txt', 'w') as file: file.write('') 
		print(f'created {root}/_exceptions-channels.txt')
	return channel_id
'''
Access the context of the last message download to obtain only
the new ones, if any.
'''
def get_last_download_context(file_context):
	if os.path.exists(file_context):
		download_context_df = pd.read_csv (file_context)
		i = len(download_context_df)
		last_msg = download_context_df['last_msg'][i-1]
		num_msg = download_context_df['num_msg'][i-1]
		print (f' get context: last_msg: {last_msg} , num_msg: {num_msg}')
		return(last_msg,num_msg)
	else:
			return(0,0)
def put_last_download_context(file_context,time_download,last_msg,num_msg):
	print (f' put context: downloaded {num_msg} messages since message {last_msg}')
	data_context= {'time_download': [time_download],
								 'last_msg' : [last_msg],
								 'num_msg' : [num_msg]}
								

	data_context_df = pd.DataFrame.from_dict(data_context)
	data_context_df.to_csv(
		file_context,
		encoding='utf-8',
		mode='a',
		index=False,
		header=not os.path.isfile(file_context)
	)

'''
Save found channels
'''

def store_channels_download(file_collected_channels,channel,output_folder):
	if os.path.exists(file_collected_channels):
		collected_channels_df = pd.read_csv(file_collected_channels,
													dtype={'channel': str, 'nun_datsets': int, 'datasets': str})
		#print(f'---> collected_channels_df {collected_channels_df}')
		if channel in collected_channels_df['channel'].values:
			#print(f'--->Detectado canal {channel}')
			channel_df = collected_channels_df.loc[collected_channels_df['channel'] == channel]
			channel_df.reset_index(inplace = True)
			#print(f'--->channel_df {channel_df}')
			#print(type(channel_df['datasets']))
			datasets = str(channel_df['datasets'][0])
			#print(f'--->datasets {datasets}')
			list_datasets = str(channel_df['datasets'][0]).split('-')
			#print(f'--->list_datasets {list_datasets}')
			if output_folder not in list_datasets:
				print(f'---> add new dataset to {output_folder}')
				num_datasets = int(channel_df['num_datasets'][0])
				num_datasets = round (num_datasets + 1, 0)
				datasets = (f'{datasets}-{output_folder}')
				collected_channels_df.loc[collected_channels_df['channel'] == channel, 'num_datasets'] = num_datasets
				collected_channels_df.loc[collected_channels_df['channel'] == channel, 'datasets'] = datasets
			else:
				pass
				#collected_channels_df.reset_index(inplace=True)
		else:
			new_row = {'channel': [channel],
								'num_datasets' : 1,
								'datasets' : output_folder
								}
			new_row_df = pd.DataFrame.from_dict(new_row)
			collected_channels_df = pd.concat([collected_channels_df, new_row_df], ignore_index=True)
	else:
		new_row = {'channel': [channel],
							 'num_datasets' : 1,
							 'datasets' : output_folder
							}
		collected_channels_df = pd.DataFrame.from_dict(new_row)

	collected_channels_df.to_csv(
		file_collected_channels,
		encoding='utf-8',
		mode='w',
		index=False
		)
	return 
def store_channels_related(file_related_channels,channels,output_folder):

	if os.path.exists(file_related_channels):
		exist_file_channels_related = True
		related_channels_df = pd.read_csv(file_related_channels,
													dtype={'channel': str, 'nun_datsets': int, 'datasets': str})
	else:
		exist_file_channels_related = False
	for channel in channels:
		if exist_file_channels_related:
			#print(f'---> related_channels_df {related_channels_df}')
			if channel in related_channels_df['channel'].values:
				#print(f'--->Detectado canal {channel}')
				channel_df = related_channels_df.loc[related_channels_df['channel'] == channel]
				channel_df.reset_index(inplace = True)
				#print(f'--->channel_df {channel_df}')
				#print(type(channel_df['datasets']))
				datasets = str(channel_df['datasets'][0])
				#print(f'--->datasets {datasets}')
				list_datasets = str(channel_df['datasets'][0]).split('-')
				#print(f'--->list_datasets {list_datasets}')
				if output_folder not in list_datasets:
					#print(f'---> add new dataset to {output_folder}')
					num_datasets = int(channel_df['num_datasets'][0])
					num_datasets = round (num_datasets + 1, 0)
					datasets = (f'{datasets}-{output_folder}')
					related_channels_df.loc[related_channels_df['channel'] == channel, 'num_datasets'] = num_datasets
					related_channels_df.loc[related_channels_df['channel'] == channel, 'datasets'] = datasets
				else:
						pass
					#related_channels_df.reset_index(inplace=True)
			else:
				new_row = {'channel': [channel],
								'num_datasets' : 1,
								'datasets' : output_folder
								}
				new_row_df = pd.DataFrame.from_dict(new_row)
				related_channels_df = pd.concat([related_channels_df, new_row_df], ignore_index=True)
		else:
			new_row = {'channel': [channel],
								 'num_datasets' : 1,
								  'datasets' : output_folder
							}
			related_channels_df = pd.DataFrame.from_dict(new_row)
			exist_file_channels_related = True
	related_channels_df.to_csv(
		file_related_channels,
		encoding='utf-8',
		mode='w',
		index=False
	)
	return 
	
# Process collected chats
def process_participants_count(client, channel_id):
	'''

	Returns:
		Participants count
	'''
	channel_request = loop.run_until_complete(
		full_channel_req(client, channel_id)
	)

	return channel_request.full_chat.participants_count


# Write collected chats
def write_collected_chats(
		chats_object,
		file,
		source,
		counter,
		req_type,
		client,
		output_folder
	):
	'''

	chats_object -> chats metadata from API requests: chats:Vector<Chat>
	file -> a txt file to write chats' data (id, username)
	source -> channel requested by the user through cmd
	counter -> dict object to count mentioned channels
	req_type -> request type (channel request or from messages)
	client -> Telegram API client
	output_folder -> Folder to save collected data

	'''
	metadata = []
	for c in chats_object:
		try:
			id_ = c['id']
			username = c['username']
			if username != None:
				file.write(f'{id_}\n')

				# collect metadata
				if id_ in counter.keys():
					counter[id_]['counter'] += 1
					counter[id_][req_type] += 1
					src = counter[id_]['source']
					if source not in src:
						counter[id_]['source'].append(source)
				else:
					counter[id_] = {
						'username': username,
						'counter': 1,
						'from_messages': 1 \
							if req_type == 'from_messages' else 0,
						'channel_request': 1 \
							if req_type == 'channel_request' else 0,
						'channel_req_targeted_by': {
							'channels': ['self']
						},
						'source': [source]
					}

					# Telegram API -> full channel request
					try:
						channel_request = loop.run_until_complete(
							full_channel_req(client, id_)
						)

						channel_request = channel_request.to_dict()
						collected_chats = channel_request['chats']
						for ch in collected_chats:
							if ch['id'] == channel_request['full_chat']['id']:
								ch['participants_count'] = \
									channel_request['full_chat']['participants_count']
							else:
								ch_id = ch['id']
								try:
									ch['participants_count'] = \
										process_participants_count(client, ch_id)
								#except TypeError:
								except:
									ch['participants_count'] = 0

								# write new id
								if ch['username'] != None:
									file.write(f'{ch_id}\n')

									# process in counter
									if ch_id in counter.keys():
										counter[ch_id]['counter'] += 1
										counter[ch_id]['channel_request'] += 1
										counter[ch_id]['channel_request_targeted_by']['channels'].append(username)
									else:
										counter[ch_id] = {
											'username': ch['username'],
											'counter': 1,
											'from_messages': 0,
											'channel_request': 1,
											'channel_req_targeted_by': {
												'channels': [username]
											},
											'source': [source]
										}

						metadata.extend(
							[
								i for i in collected_chats
								if i['username'] != None 
							]
						)
					except ValueError:
						'''
						Save exceptions to new file
						'''
						_o = output_folder
						exceptions_path = f'{_o}/_exceptions-users-not-found.txt'
						w = open(exceptions_path, encoding='utf-8', mode='a')
						w.write(f'ID - {id_}\n')
						w.close()
		except KeyError:
			pass


	df = pd.DataFrame(metadata)
	#print (f'lenght {len(df)} cabecera {df.columns.tolist()}')
	if len(df) >0:
		df = df[chats_dataset_columns()]
		csv_path = f'{output_folder}/collected_chats.csv'
		df.to_csv(
			csv_path,
			encoding='utf-8',
			mode='a',
			index=False,
			header=not os.path.isfile(csv_path)
		)

	return counter

# Time - date attributes
def timestamp_attrs(data, col='date'):
	'''
	'''
	# process dates
	# Change by Congosto
	t = pd.to_datetime(
		data[col],
		#infer_datetime_format=True,    
		#yearfirst=True
		format = '%Y-%m-%d %H:%M:%S+00:00'
	)

	# timestamp attributes
	data[f'{col}'] = t.dt.strftime('%Y-%m-%d %H:%M:%S')
	data[f'{col}_string'] = t.dt.strftime('%Y-%m-%d')
	data[f'{col}_year'] = t.dt.year
	data[f'{col}_month_name'] = t.dt.month_name()
	data[f'{col}_day'] = t.dt.day
	data[f'{col}_day_name'] = t.dt.day_name()
	data[f'{col}_time_hour'] = t.dt.strftime('%H:%M:%S')
	data[f'{col}_quarter'] = t.dt.quarter
	data[f'{col}_dayofyear'] = t.dt.dayofyear
	data[f'{col}_weekofyear'] = t.dt.isocalendar().week

	return data

# Clean msg
def clean_msg(text):
	'''
	'''
	#text = text.replace("\r\n", " ")
	return ' '.join(text.split()).strip()

# Message attributes
def msg_attrs(msg, res):
	'''
	'''
	t = msg['from_id']
	if t:
		# main peer attr
		attr = t['_']

		# parser
		parser = {
			'PeerUser': 'user_id',
			'PeerChat': 'chat_id',
			'PeerChannel': 'channel_id'
		}

		# get attr id
		attr_id = parser[attr]

		# assign attr
		res['msg_from_peer'] = attr
		res['msg_from_id'] = t[attr_id]

	return res

# Get channel name
def get_channel_name(channel_id, channels):
	'''
	'''
	channel_name = None
	try:
		channel_name = channels[
			channels['id'] == channel_id
		]['username'].iloc[0]
	except IndexError:
		pass

	return channel_name

# Get forward attrs
def get_forward_attrs(msg, res, channels_data):
	'''
	'''
	date = msg['date']
	msg_id = msg['channel_post']

	# get from id value
	from_id = msg['from_id']
	if from_id:

		# parser
		parser = {
			'PeerUser': 'user_id',
			'PeerChat': 'chat_id',
			'PeerChannel': 'channel_id'
		}

		attr = from_id['_']
		attr_id = parser[attr]
		attr_id_value = from_id[attr_id]

		channel_name = get_channel_name(attr_id_value, channels_data)
	else:
		attr = None
		attr_id_value = None
		channel_name = None

	# process dates
	# Change by Congosto
	t = pd.to_datetime(
		date,
		#infer_datetime_format=True,    
		#yearfirst=True
		format = '%Y-%m-%d %H:%M:%S+00:00'
	)

	date = t.strftime('%Y-%m-%d %H:%M:%S')
	date_string = t.strftime('%Y-%m-%d')

	res['forward_msg_from_peer_type'] = attr
	res['forward_msg_from_peer_id'] = attr_id_value
	res['forward_msg_from_peer_name'] = channel_name
	res['forward_msg_date'] = date
	res['forward_msg_date_string'] = date_string

	if channel_name != None and msg_id != None:
		n = channel_name
		res['forward_msg_link'] = f'https://t.me/{n}/{msg_id}'

	return res

# Get reply attrs
def get_reply_attrs(msg, res, username):
	'''
	'''
	reply = msg['reply_to']
	if reply:
		reply_to_msg_id = msg['reply_to']['reply_to_msg_id']
		res['is_reply'] = 1
		res['reply_to_msg_id'] = reply_to_msg_id
		res['reply_msg_link'] = f'https://t.me/{username}/{reply_to_msg_id}'

	return res

def get_url_attrs(msg, res):
	'''
	get from msg
	'''

	has_url = 0
	url = None
	domain = None
	url = re.search(r'https?://\S+', msg)
	if url != None:
		url = url.group()
		domain = re.search(r'(?<=://)[^/]+', url)
		if domain != None:
			domain = re.sub ('^www\.|^WWW\.', "", domain.group())
			domain = re.sub ('m.youtu.be|youtu.be|m.youtube.com', "youtube.com", domain)
			domain = re.sub ('t.co', "twitter.com", domain)
		has_url = 1
	res['has_url'] = has_url
	res['url'] = url
	res['domain'] = domain
	return res


# Chats dataset -> columns
def chats_dataset_columns():

	return [
		'_',
		'id',
		'title',
		'photo',
		'date',
		'creator',
		'left',
		'broadcast',
		'verified',
		'megagroup',
		'restricted',
		'signatures',
		'min',
		'scam',
		'has_link',
		'has_geo',
		'slowmode_enabled',
		'call_active',
		'call_not_empty',
		'fake',
		'gigagroup',
		'noforwards',
		'join_to_send',
		'join_request',
		'forum',
		'stories_hidden',
		'stories_hidden_min',
		'stories_unavailable',
		'signature_profiles',
		'access_hash',
		'username',
		'restriction_reason',
		'admin_rights',
		'banned_rights',
		'default_banned_rights',
		'participants_count',
		'usernames',
		'stories_max_id',
		'color',
		'profile_color',
		'emoji_status',
		'level',
		'subscription_until_date'
	]
# Chats dataset ->types
def chats_dataset_dtypes():
	'''
	'''
	dtypes = {
		'_': 'object',
		'id': 'object',
		'title': 'object',
		'photo': 'object',
		'date': 'object',
		'creator': 'object',
		'left': 'object',
		'broadcast': 'object',
		'verified': 'object',
		'megagroup': 'object',
		'restricted': 'object',
		'signatures': 'object',
		'min': 'object',
		'scam': 'object',
		'has_link': 'object',
		'has_geo': 'object',
		'slowmode_enabled': 'object',
		'call_active': 'object',
		'call_not_empty': 'object',
		'fake': 'object',
		'gigagroup': 'object',
		'noforwards': 'object',
		'join_to_send': 'object',
		'join_request': 'object',
		'forum': 'object',
		'stories_hidden': 'object',
		'stories_hidden_min': 'object',
		'stories_unavailable': 'object',
		'signature_profiles': 'object',
		'access_hash': 'object',
		'username': 'object',
		'restriction_reason': 'object',
		'admin_rights': 'object',
		'banned_rights': 'object',
		'default_banned_rights': 'object',
		'participants_count': 'object',
		'usernames': 'object',
		'stories_max_id': 'object',
		'color': 'object',
		'profile_color': 'object',
		'emoji_status': 'object',
		'level': 'object',
		'subscription_until_date': 'object'
	}
	return (dtypes)

# Msgs dataset -> columns
def msgs_dataset_columns():
	'''
	'''
	return [
		'signature',
		'channel_id',
		'channel_name',
		'msg_id',
		'message',
		'date',
		'msg_link',
		'msg_from_peer',
		'msg_from_id',
		'views',
		'number_replies',
		'number_forwards',
		'is_forward',
		'forward_msg_from_peer_type',
		'forward_msg_from_peer_id',
		'forward_msg_from_peer_name',
		'forward_msg_date',
		'forward_msg_date_string',
		'forward_msg_link',
		'is_reply',
		'reply_to_msg_id',
		'reply_msg_link',
		'has_url',
		'url',
		'domain',
	]
# Msgs dataset -> columns
def msgs_dataset_dtypes():
# Specifying data types manually
	dtypes = {
		'signature': 'object',
		'channel_id': 'object',
		'channel_name': 'object',
		'msg_id': 'object',
		'message': 'object',
		'date': 'object',
		'msg_link': 'object',
		'msg_from_peer': 'object',
		'msg_from_id': 'object',
		'views': 'float64',
		'number_replies': 'float64',
		'number_forwards': 'float64',
		'is_forward': 'int32',
		'forward_msg_from_peer_type': 'object',
		'forward_msg_from_peer_id': 'object',
		'forward_msg_from_peer_name': 'object',
		'forward_msg_date': 'object',
		'forward_msg_date_string': 'object',
		'forward_msg_link': 'object',
		'is_reply': 'int32',
		'reply_to_msg_id': 'object',
		'reply_msg_link': 'object',
		'contains_media': 'object',
		'media_type': 'object',
		'has_url': 'object',
		'url': 'object',
		'domain': 'object',
		}
	return (dtypes)
'''

write collected msgs


def write_collected_msgs(
		msgs_object,
		channel,
		chats,
		file,
	):


	msgs_object -> msgs from API requests:<messages>
	username
	chats -> chats
	file -> a temporary file to store messages
	
	'''
def write_collected_msgs (messages, username, chats, msg_tmp):
	
	df_msgs = pd.DataFrame(columns = msgs_dataset_columns())
	response = {
		'channel_name': username
	}
	chats = pd.DataFrame(chats)
	for idx, item in enumerate(messages):
		try:
			'''
			Iterate posts
			'''
			if item['_'] == 'Message':
				df_msgs.index = df_msgs.index + 1
				# channel id
				response['channel_id'] = item['peer_id']['channel_id']
				#response['channel_id'] = item['peer_id']['channel_id']

				# message id
				msg_id = item['id']
				response['msg_id'] = msg_id

				# add attrs
				msg = clean_msg(item['message'])
				response['message'] = msg

				# timestamp
				date = item['date']
				response['date'] = date

				# signature and message link
				response['signature'] = \
					f'msg_iteration.{idx}.user.{username}.post.{msg_id}'
				response['msg_link'] = f'https://t.me/{username}/{msg_id}'

				# check peer
				response['msg_from_peer'] = None
				response['msg_from_id'] = None
				response = msg_attrs(item, response)

				# reactions
				response['views'] = 0 if item['views'] == None else item['views']
				response['number_replies'] = \
					item['replies']['replies'] if item['replies'] != None else 0
				response['number_forwards'] = 0 if item['forwards'] == None \
						else item['forwards']

				# Forward attrs
				forward_attrs = item['fwd_from']
				response['is_forward'] = 1 if forward_attrs != None else 0

				response['forward_msg_from_peer_type'] = None
				response['forward_msg_from_peer_id'] = None
				response['forward_msg_from_peer_name'] = None
				response['forward_msg_date'] = None
				response['forward_msg_date_string'] = None
				response['forward_msg_link'] = None
				if forward_attrs:
					response = get_forward_attrs(
						forward_attrs,
						response,
						chats
						)

				# Reply attrs
				response['is_reply'] = 0
				response['reply_to_msg_id'] = None
				response['reply_msg_link'] = None
				response = get_reply_attrs(
					item,
					response,
					username
					)
				# Media
				
				# URLs -> Constructor MessageMediaWebPage
				'''
				Extract fron message

				'''
				response = get_url_attrs(msg, response)

				df_msgs.loc[-1] = response
		except:
			print('an exception happened')

	df_msgs.to_csv(
		msg_tmp,
		mode='a', 
		header=False,
		index=False,
		encoding='utf-8'
	)
	return


'''

Network
'''
def normalize_values(data):
	'''

	data: a list of tuples -> based on G.degree
	'''
	max_v = max([v for i, v in data])
	min_v = min([v for i, v in data])

	return [
		int((i - (min_v)) / (max_v - min_v) * 450) + 50
		for l, i in data 
	]
