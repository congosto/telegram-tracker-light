'''
This script is based on one made by Marcelino Madrigal
'''
import re
import os
import sys
import pandas as pd
import networkx as nx
import dask.dataframe as dd
from tqdm import tqdm
import argparse
from datetime import datetime
from utils import (
	chats_dataset_dtypes,msgs_dataset_dtypes
)

start_time = datetime.now()
print(f"Script start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

'''

Arguments

'''
parser = argparse.ArgumentParser(description='Arguments.')
'''
dataset
'''
parser.add_argument(
	'--dataset',
	type=str,
	required=True,
	help='Specifies a dataset.'
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
Parse arguments

'''
args = vars(parser.parse_args())
dataset = args['dataset']
output = args['output']
# Variable for file processing path
base_path = f'{output}/{dataset}'
if not os.path.exists(base_path):
	print(f'{dataset} does not exist')
	sys.exit()

'''

read channel metadata and messages

'''

# Read CSV file using dask with specified data types
print("----> Reading CSV file...")
channel_metadata = pd.read_csv(f'{base_path}/collected_chats.csv', on_bad_lines='skip', engine='python')
df = dd.read_csv(
	f'{base_path}/msgs_dataset.csv',
	dtype=msgs_dataset_dtypes(),
	usecols=['channel_name','forward_msg_from_peer_name'],
	on_bad_lines='skip', engine='python')
print(f'Last {datetime.now()- start_time} ')

'''
start_time_step = datetime.now()
print('----> Reading collected_chats.csv and msgs_dataset.csv')
channel_metadata = pd.read_csv(f'{base_path}/collected_chats.csv')
df = pd.read_csv(f'{base_path}/msgs_dataset.csv', dtype=msgs_dataset_dtypes(), usecols=['channel_name','forward_msg_from_peer_name'] )
print(f'Last {datetime.now()- start_time_step} ')
'''

'''
create node attributes
'''
start_time_step = datetime.now()
print('----> Create node attributes')
forward_in = df[df['forward_msg_from_peer_name'].notnull()]
forward_in = forward_in.groupby('forward_msg_from_peer_name').size().compute()
forward_in = forward_in.reset_index()
forward_in = forward_in.rename(columns={ 0:'forward_in'})
forward_out = df[df['forward_msg_from_peer_name'].notnull()].\
	groupby('channel_name').size().reset_index().rename(columns={ 0:'forward_out'})
forward_out = forward_out.compute()
#		rename(columns={ 0:'forward_out'})
print(f'Last {datetime.now()- start_time_step} ')	
nodes = channel_metadata[['username','date','participants_count','verified','megagroup','gigagroup','fake']]
nodes = nodes.set_index('username')
forward_in = forward_in.set_index('forward_msg_from_peer_name')
forward_out = forward_out.set_index('channel_name')
nodes = nodes.join(forward_in)
nodes = nodes.join(forward_out)
nodes = nodes.fillna(0)
nodes['forward_tot'] = nodes['forward_in'] + nodes['forward_out']
nodes['year'] = pd.DatetimeIndex(nodes['date']).year
nodes = nodes[(nodes['forward_tot'] > 0)].sort_values("forward_tot", ascending=False)

'''
Generate nodes
'''
start_time_step = datetime.now()
G = nx.DiGraph()
for index, row in tqdm(nodes.iterrows(), total=nodes.shape[0], desc="processing nodes"):
	G.add_node(index)
	G.nodes[index]['participants_count'] = row['participants_count']
	G.nodes[index]['forward_tot'] = row['forward_tot']
	G.nodes[index]['forward_in'] = row['forward_in']
	G.nodes[index]['forward_out'] = row['forward_out']
	G.nodes[index]['date'] = row['date']
	G.nodes[index]['year'] = row['year']
	G.nodes[index]['verified'] = row['verified']
	G.nodes[index]['megagroup'] = row['megagroup']
	G.nodes[index]['gigagroup'] = row['gigagroup']
	G.nodes[index]['fake'] = row['fake']
print(f'Last {datetime.now()- start_time_step} ')		
'''
Generate forward arcs
'''
start_time_step = datetime.now()
# Filter rows where 'forward_msg_from_peer_name' has content
#filtered_df = df[df['forward_msg_from_peer_name'].notna()]
filtered_df = df.dropna(subset=['forward_msg_from_peer_name'])
# Group by 'channel_name' and 'forward_msg_from_peer_name' and count occurences
#grouped_df = filtered_df.groupby(['channel_name', 'forward_msg_from_peer_name']).value_counts().reset_index().\
#		rename(columns={ 'count':'weight'})

# Agrupar por 'channel_name' y 'forward_msg_from_peer_name', luego contar los elementos
grouped_df = filtered_df.groupby(['channel_name', 'forward_msg_from_peer_name']).size().\
	reset_index().rename(columns={ 0:'weight'})

# Computar el resultado y convertirlo en un DataFrame de pandas si es necesario
grouped_df = grouped_df.compute()
# Add nodes and edges to the graph with progress bar
for index, row in tqdm(grouped_df.iterrows(), total=grouped_df.shape[0], desc="processing arcs"):
	source = row['channel_name']
	target = row['forward_msg_from_peer_name']
	weight = row['weight']
	G.add_edge(source, target, weight=weight)

print(f'Last {datetime.now()- start_time_step} ')
# Export the graph to a GEXF file
nx.write_gexf(G, f'{base_path}/{dataset}.gexf')

print(f'Graph successfully exported to {base_path}/{dataset}.gexf')
print(f'Last {datetime.now()-start_time} ')		





