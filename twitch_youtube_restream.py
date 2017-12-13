#!/usr/bin/python3

# Adapted from https://www.johannesbader.ch/2014/01/find-video-url-of-twitch-tv-live-streams-or-past-broadcasts/

import requests
import json
import re
import argparse
import random
import m3u8
import os
from time import sleep

config_str = open('config.json', 'r').read()
config_cleansed = re.sub(r'\\\n', '', config_str)
config_cleansed = re.sub(r'//.*\n', '\n', config_cleansed)

config = json.loads(config_cleansed)

USHER_API = 'http://usher.twitch.tv/api/channel/hls/{channel}.m3u8?player=twitchweb' +\
    '&token={token}&sig={sig}&$allow_audio_only=true&allow_source=true' + \
    '&type=any&p={random}'
TOKEN_API = 'http://api.twitch.tv/api/channels/{channel}/access_token?client_id={twitch_api_client_id}'.format(twitch_api_client_id=config['twitch_api_client_id'], channel=config['twitch_channel_name'])


def get_token_and_signature():
    url = TOKEN_API
    r = requests.get(url)
    txt = r.text
    data = json.loads(txt)
    sig = data['sig']
    token = data['token']
    return token, sig

def get_live_stream(channel):
    token, sig = get_token_and_signature()
    r = random.randint(0,1E7)
    url = USHER_API.format(channel=channel, sig=sig, token=token, random=r)
    r = requests.get(url)
    m3u8_obj = m3u8.loads(r.text)
    return m3u8_obj

def print_video_urls(m3u8_obj):
    print("Video URLs (sorted by quality):")
    for p in m3u8_obj.playlists:
        si = p.stream_info
        bandwidth = si.bandwidth/(1024)
        quality = p.media[0].name
        resolution = si.resolution if si.resolution else "?"
        uri = p.uri
        #print(p.stream_info, p.media, p.uri[1])
        txt = "\n{} kbit/s ({}), resolution={}".format(bandwidth, quality, resolution)
        print(txt)
        print(len(txt)*"-")
        print(uri)

if __name__=="__main__":
#    parser = argparse.ArgumentParser('get video url of twitch channel')
#    parser.add_argument('channel_name')
#    args = parser.parse_args()

    while config['continuous_retry']:

        m3u8_obj = get_live_stream(config['twitch_channel_name'])

        print_video_urls(m3u8_obj)

        if len(m3u8_obj.playlists) > 0:
            url = m3u8_obj.playlists[0].uri
            print('streaming to youtube from {}'.format(url))
            os.system("cvlc {} --sout '#transcode{{vcodec=FLV1,acodec=mp3,samplerate=44100}}:std{{access=rtmp,mux=ffmpeg{{mux=flv}},dst=rtmp://a.rtmp.youtube.com/live2/'{}".format(url, config['youtube_stream_key']))
        else:
            print('no twitch stream')

        sleep(int(config['stream_check_interval']))

