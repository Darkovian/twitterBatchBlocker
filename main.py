import os
import pickle
import sys
import time
import webbrowser

import numpy as np
import tweepy


def handle_secrets() -> tweepy.OAuthHandler:
    """
    Checks for a keys file. If one is found, loads those keys. Otherwise it prompts the user to input the consumer key and secret, and saves them to a new keys file.
    Returns a tweepy OAuthHandler object.
    """
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
    return tweepy.OAuthHandler(KEYS[0], KEYS[1])


def handle_user_secrets(tweepy_auth: tweepy.OAuthHandler) -> tweepy.API:
    """
    Checks for a tokens.pkl file. If one is found it loads those tokens, otherwise it initiates user authentication and saves those tokens to tokens.pkl.
    Returns a tweepy api object.
    """
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
    return api


def get_users_to_block(api: tweepy.API):
    """
    Takes a tweepy api object. Prompts user to input username of account to block the followers of.
    Returns an array of user_ids which are not already blocked by the authenticated user.
    """
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
    if already_blocked > 1:
        print(f'You were already blocking {already_blocked} of them! Nice!')
    return np.asarray(user_ids)


def do_blocks(api: tweepy.API, np_ids):
    """ Takes a tweepy api object and an array of user_ids and blocks each id as the authenticated user """
    curr_block = 1
    curr_percent = 0.0
    for user_id in np_ids:
        while True:
            try:
                api.create_block(user_id=user_id)
                break
            except tweepy.RateLimitError:
                print(f'\n[{time.localtime().tm_hour}:{time.localtime().tm_min}] Rate limiting detected. Waiting 15 minutes before resuming...\n')
                time.sleep(15*60)
                continue
            except Exception as e:
                if 'lock' in str(e):
                    print('WARNING: Twitter may have locked the account. Visit Twitter to unlock it. Exiting.')
                    sys.exit(1)
                else:
                    print(f'\nError blocking {user_id}.\n\tError: {str(e)}\n')
                    break

        curr_block += 1
        last_percent = curr_percent
        curr_percent = round((curr_block / np_ids.size) * 100, 1)
        if curr_percent != last_percent:
            print(f'\r{curr_percent:04}% of {np_ids.size} users blocked', end='')


tweepy_auth = handle_secrets()
api = handle_user_secrets(tweepy_auth=tweepy_auth)
user_choice = 'Y'

while user_choice.lower() != 'n':
    np_ids = get_users_to_block(api=api)

    if input(f'Proceed to block {np_ids.size} users? Y/N: ').lower() == 'n':
        sys.exit(0)
    else:
        do_blocks(api=api, np_ids=np_ids)

    user_choice = input('Block another batch of grossies? Y/N: ')
