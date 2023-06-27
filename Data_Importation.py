import time
import pandas as pd
from statistics import mean


df_full = pd.read_csv(r"C:\Users\sliwi\Documents\Courses\airlines_en.csv",
                      dtype={'_id': 'str',
                             'entities.user_mentions': 'str',
                             'id_str': 'str',
                             'in_reply_to_status_id_str': 'str',
                             'in_reply_to_user_id_str': 'str',
                             'text': 'str',
                             'timestamp_ms': 'Int64',
                             'user.id_str': 'str'},
                      usecols=['id_str', 'text', 'user.id_str', 'in_reply_to_status_id_str',
                               'in_reply_to_user_id_str', 'timestamp_ms'])

df_full.dropna(subset=['id_str'])

df_original = df_full[df_full[['in_reply_to_status_id_str', 'in_reply_to_user_id_str']].isna().all(1)].dropna(subset=[
    'id_str', 'text', 'user.id_str', 'timestamp_ms'])
df_replies = df_full[(~df_full['in_reply_to_status_id_str'].isna()) &
                     (~df_full['in_reply_to_user_id_str'].isna())
                     ].dropna(subset=['id_str', 'text', 'user.id_str', 'timestamp_ms']
                              ).drop_duplicates(subset='id_str')

df_original = df_original[df_original['id_str'].isin(df_replies['in_reply_to_status_id_str']
                                                     )].drop_duplicates(subset='id_str')
# original_dict = df_original.to_dict('records')
df_British_Airways = df_replies[(df_replies['user.id_str'] == '26223583') | (df_replies['in_reply_to_user_id_str'] == '26223583')]
print('bruh')

conversations_british_air = df_original[(df_original['id_str'].isin(df_British_Airways['in_reply_to_status_id_str']) |
                                         (df_original['user.id_str'] == '26223583'))]
BA_conv_to_dict = conversations_british_air.to_dict('records')


def conversation_miner(tweet_id_str):
    # Create an empty dictionary to store conversations
    conversations_per_tweet = {}

    # Initialize a list to hold the tweet IDs for the next iteration
    next_tweet_ids = [tweet_id_str]

    while next_tweet_ids:
        # Filter the DataFrame to include only the tweet IDs for the current iteration
        current_replies = df_replies[df_replies['in_reply_to_status_id_str'].isin(next_tweet_ids)]

        # Store the current replies in the conversations dictionary
        conversations_per_tweet.update({tweet_id: current_replies for tweet_id in next_tweet_ids})

        # Get the IDs of the current replies for the next iteration
        next_tweet_ids = current_replies['id_str'].tolist()

    return conversations_per_tweet


def process_tweet_ids(tweet_id_list):
    conversations_dict = {}

    for tweet_id in tweet_id_list:
        # Mine conversations for the current tweet ID
        new_conversations = conversation_miner(tweet_id)

        # Add the conversations to the local dictionary
        conversations_dict.update(new_conversations)

    return conversations_dict




def conversation_mine(row_dict):
    conversation_tweet = [row_dict]
    processed_indices = []

    replies = df_British_Airways[(df_British_Airways['in_reply_to_status_id_str'] == row_dict['id_str']) &
                                 (df_British_Airways['timestamp_ms'] > row_dict['timestamp_ms'])]
    processed_indices.extend(replies['id_str'])

    for _, reply in replies.iterrows():
        sub_conversation, sub_indices = conversation_mine(dict(reply))
        conversation_tweet.extend(sub_conversation)
        processed_indices.extend(sub_indices)

    return conversation_tweet, processed_indices


list_conversations = []
start_time = time.time()
completed_iterations = 0

for i in BA_conv_to_dict:
    completed_iterations +=1
    conversation, indices = conversation_mine(dict(i))
    df_British_Airways = df_British_Airways[~df_British_Airways['id_str'].isin(indices)]
    for j in conversation:
        list_conversations.append(j)
    print(completed_iterations)

df_conversations = pd.DataFrame(list_conversations)
df_conversations['group_index'] = df_conversations['in_reply_to_status_id_str'].isnull().cumsum()
conv_lengths_BA = df_conversations['group_index'].value_counts().tolist()
print(mean(conv_lengths_BA))
df_conversations.to_csv(r"C:\Users\sliwi\Documents\Courses\conversations_total_VirginAtlantic.csv", sep=',', index=False, encoding='utf-8')

end_time = time.time()  # End timing
elapsed_time = end_time - start_time  # Calculate elapsed time

print("Time taken: {:.2f} seconds".format(elapsed_time))

print('done')

