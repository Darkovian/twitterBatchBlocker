import webbrowser
import os
import sys
import tweepy
import pickle
import numpy as np

if os.path.exists('./keys'):
    with open('./keys', 'rb') as f:
        KEYS = pickle.load(f)
else:
    print('Please enter the following: ')
    KEYS = []
    KEYS.append(input('Consumer key: '))
    KEYS.append(input('Consumer secret: '))
    with open('./keys', 'wb') as f:
        pickle.dump(KEYS, f)

tweepy_auth = tweepy.OAuthHandler(KEYS[0], KEYS[1])

if not os.path.exists('./tokens.pkl'):
    try:
        redirect_url = tweepy_auth.get_authorization_url()
    except tweepy.TweepError:
        print('Error: Failed to get request token.')
        sys.exit(0)

    webbrowser.open_new_tab(redirect_url)
    print('If it doesn\'t open automatically, please go here and get the auth code: ' + redirect_url)
    verifier = input('Verifier: ')
    try:
        tweepy_auth.get_access_token(verifier)
    except tweepy.TweepError:
        print('Error: Verification failed')

    tokens = [tweepy_auth.access_token, tweepy_auth.access_token_secret]

    with open('./tokens.pkl', 'wb') as f:
        pickle.dump(tokens, f)
else:
    with open('./tokens.pkl', 'rb') as f:
        tokens = pickle.load(f)

if input(f'Logged in as: {tweepy_auth.get_username()}. Continue? Y/N:').lower() == 'n':
    os.remove('./tokens.pkl')
    sys.exit(0)

tweepy_auth.set_access_token(tokens[0], tokens[1])
api = tweepy.API(tweepy_auth)

user_choice = 'Y'

while user_choice.lower() != 'n':
    block_user = input('Enter screen name of user to block all followers of that user. Do not include @: ')
    my_blocks = np.asarray(api.blocks_ids())
    already_blocked = 0
    user_ids = []
    try:
        for user in api.followers_ids(block_user):
            if user not in my_blocks:
                user_ids.append(user)
            else:
                already_blocked += 1
    except tweepy.TweepError as e:
        print(f'Error: {str(e)}')
        sys.exit(0)

    np_ids = np.asarray(user_ids)
    if already_blocked > 1:
        print(f'You were already blocking {already_blocked} of them! Nice!')

    if input(f'Proceed to block {np_ids.size} users? Y/N: ').lower() == 'n':
        sys.exit(0)

    curr_block = 1
    for user_id in np_ids:
        try:
            api.create_block(user_id=user_id)
        except Exception as e:
            if 'lock' in str(e):
                print('WARNING: Twitter may have locked the account. Visit Twitter to unlock it. Exiting.')
                sys.exit(1)
            else:
                print(f'Error blocking {user_id}.\n\tError: {str(e)}')
        if curr_block % 10 == 0:
            print(f'{curr_block} / {np_ids.size} users blocked')
        curr_block += 1

    user_choice = input('Block another batch of grossies? Y/N: ')
