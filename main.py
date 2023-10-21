import os
import math
import requests
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

API_KEY = '563492ad6f9170000100000171bec2c6579843a799328dd712cc05e3'


def get_user_input():
    folder_name = input("Enter the folder name where the videos and audio will be saved: ")
    article_text = input("Enter the article text: ")
    return folder_name, article_text


def create_directory(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


def extract_keywords(text):
    words = text.split()
    return set(words) - set(ENGLISH_STOP_WORDS)


def generate_voice_over(text, folder_name):
    tts = gTTS(text=text, lang='en')
    audio_file_path = os.path.join(folder_name, "voice_over.mp3")
    tts.save(audio_file_path)
    audio = AudioFileClip(audio_file_path)
    return audio


def fetch_video_clips_for_keywords(keywords, num_clips_needed, desired_size):
    clips = []
    for keyword in keywords:
        if len(clips) >= num_clips_needed:
            break

        url = "https://api.pexels.com/videos/search"
        headers = {"Authorization": API_KEY}
        response = requests.get(url, params={"query": keyword, "per_page": num_clips_needed - len(clips)}, headers=headers)
        if response.status_code != 200:
            continue

        videos = response.json().get('videos', [])

        for video in videos:
            if len(clips) >= num_clips_needed:
                break
            video_url = video['video_files'][0]['link']
            filename = os.path.join(folder_name, f"{video['id']}.mp4")
            with open(filename, 'wb') as f:
                f.write(requests.get(video_url).content)

            clip = VideoFileClip(filename).subclip(0, clip_duration)
            clip = clip.resize(newsize=desired_size)
            clip = clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=desired_size[0], height=desired_size[1])
            clips.append(clip)

    return clips


def create_final_video(clips, audio, audio_duration, folder_name):
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip = final_clip.subclip(0, audio_duration)
    final_clip = final_clip.set_audio(audio)
    final_clip.write_videofile(os.path.join(folder_name, "final_output.mp4"), fps=24)


if __name__ == '__main__':
    folder_name, article_text = get_user_input()
    create_directory(folder_name)
    keywords = extract_keywords(article_text)
    audio = generate_voice_over(article_text, folder_name)
    audio_duration = audio.duration
    clip_duration = 5
    num_clips_needed = math.ceil(audio_duration / clip_duration)
    desired_size = (1920, 1080)
    clips = fetch_video_clips_for_keywords(keywords, num_clips_needed, desired_size)
    create_final_video(clips, audio, audio_duration, folder_name)
