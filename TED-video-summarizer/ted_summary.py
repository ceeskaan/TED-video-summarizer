from argparse import ArgumentParser
from BertSum_utils import *
import moviepy
import moviepy.editor
from moviepy.editor import VideoFileClip
from nltk import sent_tokenize, word_tokenize
import os
import pytube
from pytube.cli import on_progress
from tedscraper import get_ted_summary, search_tedsummaries
from youtube_transcript_api import YouTubeTranscriptApi

parser = ArgumentParser(description='Generate audiovisual summary based on TED talk')
parser.add_argument('link', type=str, help = 'YouTube link of TED talk to be summarized')
parser.add_argument('name', type=str, help = 'Name of video')
args = parser.parse_args()

def download_video(link, name):
    try: 
        #object creation using YouTube which was imported in the beginning 
        yt = pytube.YouTube(link, on_progress_callback=on_progress) 
    except: 
        print("Connection Error") #to handle exception 
    video_path = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
    
    # rename the path
    new_path = video_path.split('/')
    new_filename = name + '.mp4'
    new_path[-1]= new_filename
    new_path='/'.join(new_path)
    os.rename(video_path, new_path)
        
    return new_path

def get_word_timestamps(response):
    """ Fetches timestamps for every word from YouTube transcript API """
    word_timestamps = []
    for res in response:
        for words in res['text'].split():
            word_timestamps.append([res['start'] , res['start'] + res['duration']])
    return word_timestamps
 
def get_sentence_timestamps(tokenized, word_timestamps):
    """ Fetches timestamps for every sentence from YouTube transcript API"""
    sentence_timestamps = []
    idx = 0
    for sentence in tokenized:
        start = []
        end = []
        for word in sentence.split():
            start.append(word_timestamps[idx][0])
            end.append(word_timestamps[idx][1])
            idx += 1
        sentence_timestamps.append([start[0], end[-1]])
    return sentence_timestamps

def timestamps_to_summary(original, save_as, summary):
    """
    Converts/saves the sentence_timestamps to a .mp4 video
    
    Parameters:
        original {str}          -- Name/location of original .mp4 video
        save_as {str}           -- Desired name/location of output .mp4 file 
        summary {lst}           -- list of selected sentence timestamps
    
    """
    
    clip = VideoFileClip(original)
    
    outputs = []
    for i in summary:
        start = i[0]
        end = i[1]

        outputs.append(clip.subclip(start, end))
    
    
    
    summary = moviepy.editor.concatenate_videoclips(outputs) 

    summary.write_videofile(save_as)
    clip.close()
    
    

if __name__ == "__main__":
    print('Downloading TED talk video...')
    download_video(args.link, args.name)
    title = pytube.YouTube(args.link).streams[0].title
    video_id = pytube.YouTube(args.link).video_id
    
    print('Fetching abstractive summary from tedsummaries.com...')
    summary = get_ted_summary(title)
    
    print('Downloading transcript...')
    response = YouTubeTranscriptApi.get_transcript(video_id)
    transcription = response[0]['text']
    for i in response[1:]:
        transcription += ' {}'.format(i['text'])
        
    word_timestamps = get_word_timestamps(response)
    doc_sent_list = sent_tokenize(transcription)
    sentence_timestamps = get_sentence_timestamps(doc_sent_list, word_timestamps)
    abstract_sent_list = sent_tokenize(summary)
    
    print('Generating extractive summary...')
    src = [word_tokenize(i) for i in doc_sent_list]
    tgt = [word_tokenize(i) for i in abstract_sent_list]
    idx = greedy_selection(src, tgt, 5)
    result = [doc_sent_list[i] for i in idx]
    
    print('Generating Video summary...')
    summary = []
    for idx, sentence in enumerate(doc_sent_list):
        if sentence in result:
            summary.append(sentence_timestamps[idx])
    timestamps_to_summary(args.name + '.mp4', args.name + '_summary.mp4', summary )
    os.remove(args.name + '.mp4')
    