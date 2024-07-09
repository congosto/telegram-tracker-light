import re
import os
import sys
import nltk
import pandas as pd
import dask.dataframe as dd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from adjustText import adjust_text
import matplotlib.ticker as ticker
from si_prefix import si_format
from wordcloud import WordCloud
from datetime import datetime
from nltk.corpus import stopwords
# Get start time
'''

graphics style

'''
# Graphics style
sns.set(style = "whitegrid")
plt.rcParams.update({'font.size': 12, 'font.family': 'sans-serif'})
RED = 'r'
BLUE = 'b'
COLOR_TEXT = "#5a5856"
COLOR_GRID = "#d0c9c7"

# Formatting function for numbers
def si_formatter(x, pos):
    return si_format(x, precision=0)
'''

messages vs. attribute

'''
def create_timeline_lineplot(ddf, attribute_a, attribute_b, filter_b, title, title_a, title_b, output_path):
  start_time_chart = datetime.now()
  print(f"----> Graphic of {title_a} vs. {title_b}...")

  # Filter rows before adding attributes
  if filter_b:
    df_a = ddf[['date',attribute_a,attribute_b]]
    # filter attribute_a
    df_a = df_a[df_a[attribute_a] == 0]
    # Group by date and sum the attribute_b (with filter)
    df_b = df_a[['date', attribute_b]].dropna().compute()
  else:
    df_a = ddf[['date',attribute_a]]
    # filter attribute_a
    df_a = df_a[df_a[attribute_a] == 0]
    # Group by date and sum the attribute_b (without filter)
    df_b = ddf[['date', attribute_b]].dropna().compute()

  df_b['date'] = df_b['date'].dt.date  # Convert to date without time
  df_b = df_b.groupby('date').sum().reset_index()
  # Group by date and sum the attribute_a
  df_a = df_a[['date', attribute_a]].dropna().compute()
  df_a['date'] = df_a['date'].dt.date  # Convert to date without time
  df_a = df_a.groupby('date').count().reset_index()
  # Calculate statistics
  max_value = int(df_b[attribute_b].max())
  min_value = int(df_b[attribute_b].min())
  mean_value = int(df_b[attribute_b].mean())
  if max_value == 0:
    print(f'There are no {attribute_b}')
    return
  # We separate the figure into two overlapping objects
  fig, ax1 = plt.subplots()
  # create line chart
  plt.figure(figsize=(14, 8))
  ax1.grid (color = COLOR_GRID) # Add grid
  ax1 = sns.lineplot(data=df_a, x='date', y=attribute_a, color=BLUE, linewidth=1.5)
  ax2 = plt.twinx()
  ax2 = sns.lineplot(data=df_b, x='date', y=attribute_b, color=RED, linewidth=1.5)
  ax1.grid (False) # remove grid
  ax1.yaxis.set_major_formatter(ticker.FuncFormatter(si_formatter))
  ax2.yaxis.set_major_formatter(ticker.FuncFormatter(si_formatter))
  # Add labels to the maximum 5 values
  top_2 = df_b.nlargest(2, attribute_b)
# Annotate top values
  offset = 0
  for i, row in top_2.iterrows():
    plt.text(row['date'], row[attribute_b] + offset,
      f"{row['date'].strftime('%d-%m-%Y')}\n{int(row[attribute_b]):,}".replace(',', '.'),
      fontsize=10, ha='right', color=COLOR_TEXT)
    offset -= row[attribute_b] * 0.1  # Move each label down 10% to avoid overlapping
# complete details with matplotlib
  plt.title(title, fontsize=16)
  ax1.set_ylabel (title_a, fontsize=14, color=BLUE)
  ax1.set_xlabel ("")
  ax1.yaxis.set_tick_params(labelsize=12,labelcolor=BLUE)

  ax2.set_ylabel (title_b , fontsize=14, color=RED)
  ax2.set_xlabel ("")
  ax2.yaxis.set_tick_params(labelsize=12,labelcolor=RED)
 
  # Add box with statistics
  stats_text = f"{attribute_b}\nMax: {max_value:,}\nMin: {min_value:,}\nMedia: {mean_value:,}".replace(',', '.')
  plt.gcf().text(0.1, 0.75, stats_text, fontsize=12,color = COLOR_TEXT,
    bbox=dict(facecolor='white', alpha=0.6))
  plt.tight_layout()
  plt.savefig(output_path)
  plt.close()
  print(f"Successfully saved in {output_path}.")
  print(f'Last {datetime.now()- start_time_chart} ')

'''

Bar chart of top 15 domains by totals

'''
def create_top_domains_barplot(ddf, title, output_path):
  start_time_chart = datetime.now()
  print("----> Bar chart of top 15 domains by totals...")

  # Count the occurrences of each domain
  domain_counts = ddf['domain'].value_counts().compute().reset_index()
  domain_counts.columns = ['domain', 'count']

  # Select top 15
  top_15_domains = domain_counts.nlargest(15, 'count')

  # Create bar chart
  plt.figure(figsize=(14, 8))
  sns.barplot(data=top_15_domains, x='count', y='domain')

  plt.title(title, fontsize=16)
  plt.xlabel('Total', fontsize=14)
  plt.ylabel('Dominio', fontsize=14)
  plt.xticks(rotation=0)

  plt.tight_layout()
  plt.savefig(output_path)
  plt.close()
  print(f"Successfully saved in {output_path}.")
  print(f'Last {datetime.now()- start_time_chart} ')

'''

create line chart with cumulative total of top 10 most mentioned domains by date

'''
def create_top_domains_timeline(ddf, title, output_path):
  start_time_chart = datetime.now()
  print("----> Create line chart with cumulative total of top 10 most mentioned domains by date...")
  # Count the occurrences of each domain
  domain_counts = ddf['domain'].value_counts().compute().reset_index()
  domain_counts.columns = ['domain', 'count']
  # Select top 15
  top_10_domains = domain_counts.nlargest(10, 'count')['domain']

  # Filter the DataFrame to include only the top 10 domains
  ddf_top_10 = ddf[ddf['domain'].isin(top_10_domains)].compute()

  # Create a column for the date without the time
  ddf_top_10['date'] = ddf_top_10['date'].dt.date
  # Group by date and domain and count occurrences
  df_grouped = ddf_top_10.groupby(['date', 'domain']).size().reset_index(name='count')

  # Create cumulative count column
  df_grouped['cumulative_count'] = df_grouped.groupby('domain')['count'].cumsum()
  #df_grouped= df_grouped.sort_values(by=['cumulative_count','domain'], ascending=[False, False])
  color_lines = sns.color_palette("tab10")
  # Create the line chart
  plt.figure(figsize=(14, 8))
  sns.lineplot(data=df_grouped, x='date', y='cumulative_count', hue='domain', palette='tab10', linewidth=1.5)
# Annotate top values
  i_color = 0
  texts = []
  for domain in top_10_domains:
    rows = df_grouped.loc[df_grouped['domain'] == domain, :].head(1)
    for i, row in rows.iterrows():
      text = plt.text(row['date'], row['cumulative_count'],
        f"{row['domain']}({int(row['cumulative_count']):,})".replace(',', '.'),
        color = color_lines[i_color])
      i_color += 1
      texts.append(text)
  adjust_text(texts, arrowprops=dict(arrowstyle='-', color='grey'))
  plt.title(title, fontsize=16)

  plt.xlabel('', fontsize=14)
  plt.ylabel('Cumulative total of mentions', fontsize=14)
  plt.xticks(rotation=0)
  plt.legend('',frameon=False)

  plt.tight_layout()
  plt.savefig(output_path)
  plt.close()
  print(f"Successfully saved in {output_path}.")
  print(f'Last {datetime.now()- start_time_chart} ')

'''
Clean text

'''
# remove URLs and convert to lowercase
def clean_text(text):
    text = re.sub(r'http\S+', '', text)  # Eliminar URLs
    text = text.lower()  # Pasar a minúsculas
    return text
'''

Create a word cloud

'''


# Create a word cloud of the messages using a random sample of 10%
def create_wordcloud(ddf, column, output_path):
    print(f"Generating word cloud of {column}...")

    # Get a random sample of 10% of the messages
    sample_ddf = ddf[column].dropna().sample(frac=0.1, random_state=1).compute().astype(str)
    # Merge all messages into one text
    text = ' '.join(sample_ddf.tolist())
    size =len(text)
    print(size)
    return

    # Generate word cloud
    stop_words = set(stopwords.words('spanish') + stopwords.words('english'))
    wordcloud = WordCloud(width=1200, height=800, background_color='white', stopwords=stop_words).generate(text)

    # Get the 5 most used words
    top_5_words = list(wordcloud.words_.keys())[:5]

    # Mostrar y guardar nube de palabras
    plt.figure(figsize=(15, 10))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Successfully saved in {output_path}.")

    return top_5_words



'''

Start script


'''

start_time = datetime.now()
print(f"Script start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Download NLTK stopwords
nltk.download('stopwords')

'''

Arguments

'''

parser = argparse.ArgumentParser(description='Arguments.')
parser.add_argument(
	'--dataset',
	type=str,
	required=True,
	help='Specifies a dataset.'
)

# parse arguments
args = vars(parser.parse_args())
dataset = args['dataset']
# Variable for file processing path
base_path = f'./data/{dataset}/'
base_images_path = f'./data/{dataset}/images/'
if not os.path.exists(base_images_path):
	os.makedirs(f'{base_images_path}', exist_ok=True)
csv_file_path = f'{base_path}msgs_dataset.csv'

# Change matplotlib backend to 'Agg'
plt.close('all')


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
'''

read and clean data

'''
# Read CSV file using dask with specified data types
print("----> Reading CSV file...")
ddf = dd.read_csv(csv_file_path, dtype=dtypes, on_bad_lines='skip', engine='python')
#ddf = dd.read_csv(csv_file_path, on_bad_lines='skip', engine='python')
print(f'Last {datetime.now()- start_time} ')
# Convert 'date' column to datetime
ddf['date'] = dd.to_datetime(ddf['date'], errors='coerce')
# Filter rows with valid dates
ddf = ddf.dropna(subset=['date'])


'''

Creating line graphs of time distributions

'''
create_timeline_lineplot(ddf, 'is_forward','views', True,
  f'{dataset}: Temporal distribution of messages vs. views',
  'Num. of original msgs per day',
  'Views per day',
   base_images_path + 'timeline_views.png')
create_timeline_lineplot(ddf, 'is_forward','is_forward', False,
  f'{dataset}: Temporal distribution of messages vs. forwards send',
  'Num. of original msgs per day',
  'Forwards per day',
   base_images_path + 'timeline_forwards_send.png')
create_timeline_lineplot(ddf, 'is_forward','number_forwards', True,
  f'{dataset}: Temporal distribution of messages vs. forwards received',
  'Num. of original msgs per day',
  'Forwards per day',
   base_images_path + 'timeline_forwards_received.png')
create_timeline_lineplot(ddf, 'is_forward', 'is_reply', False,
  f'{dataset}: Temporal distribution of messages vs. replies send',
  'Num. of original msgs per day',
  'Replies per day',
  base_images_path + 'timeline_replies_send.png')
create_timeline_lineplot(ddf, 'is_forward', 'number_replies', True,
  f'{dataset}: Temporal distribution of messages vs. replies received',
  'Num. of original msgs per day',
  'Replies per day',
  base_images_path + 'timeline_replies_received.png')
'''

Creating domain graphs

'''
create_top_domains_barplot(ddf,
  f'{dataset}: Top 15 Dominios por Totales',
  base_images_path + 'top_15_domains.png'),

create_top_domains_timeline(ddf,
  f'{dataset}: Cumulative temporal distribution of the 10 most mentioned domains',
  base_images_path + 'top_10_domains_timeline.png')

'''

Creating word cloud

'''
# Apply cleanup function to message column
ddf['cleaned_message'] = ddf['message'].dropna().apply(clean_text, meta=('message', 'object'))
# Create the word cloud for clean messages and get the 5 most used words
#top_5_words = create_wordcloud(ddf, 'cleaned_message', base_images_path + 'wordcloud_messages.png')

'''

End script

'''
plt.close('all')
# Put end time
end_time = datetime.now()
print(f"Hora final del script: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

