from pydub import AudioSegment
from pydub.playback import play
import asyncio
import edge_tts
import io

import threading
import queue
import os

import codecs
import chardet
import string

# tts文字转语音程序
VOICE = "zh-CN-XiaoxiaoNeural"
OUTPUT_FILE = ""
async def tts(TEXT):
    communicate = edge_tts.Communicate(TEXT, VOICE)
    audio_stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_stream.write(chunk["data"])
    audio_stream.seek(0)
    audio = AudioSegment.from_file(audio_stream)
    return audio

# 消费音频文件
def play_sound():
    while True:
        audio = sound_queue.get()
        play(audio)

# 判断tts文本是否由纯标点符号组成
def is_punctuation(s):
    # 定义中文标点符号
    # chinese_punctuation = "，。、；：！？《》（）【】‘’“”"
    punctuation = string.punctuation + string.whitespace
    for c in s:
        if c not in punctuation:
            return False
    return True

# 主程序
def main(tts_length):
    # 交互
    txt_files = []
    idx = 0
    for filename in os.listdir():
        if filename.endswith('.txt'):
            txt_files.append(filename)
            print(f'{idx}. {filename}')
            idx += 1
    selection = input('Enter the number of the file you want to read: ')
    selected_file = txt_files[int(selection)]

    # 检测文件编码，检测头部32个字符
    with open(selected_file, 'rb') as f:
        result = chardet.detect(f.read(32))
    encoding = result['encoding']
    print(f'selected file:{selected_file}\nfile Encoding: {encoding}\n')

    # 读取数据并处理
    tmp_tts_text = ''
    with codecs.open(selected_file, 'r', encoding=encoding) as file:
        while True:
            chunk = file.read(tts_length)
            if not chunk:
                break
            # 用标点符号，将文字分段
            for idx, c in enumerate(chunk[::-1]):
                if c in ",;:!?，。；：！？\n":
                    # idx为零，及第一个字符就是标点符号，特殊处理
                    if idx:
                        tts_text = tmp_tts_text + chunk[:-idx]
                        tmp_tts_text = chunk[-idx:]
                    else:
                        tts_text = tmp_tts_text + chunk
                        tmp_tts_text = ''
                    break
            if is_punctuation(tts_text):
                continue
            audio = asyncio.run(tts(tts_text))
            sound_queue.put(audio)
            print(tts_text, end='')

        # 处理最后一块文字
        if tmp_tts_text:
            if is_punctuation(tmp_tts_text):
                return
            audio = asyncio.run(tts(tmp_tts_text))
            sound_queue.put(audio)
            print(tmp_tts_text)

if __name__ == '__main__':
    # 队列最大容量，1即可保证连续无停顿
    queue_size = 1
    # 单次tts文本长度，太小可能无法分段处理，语音会有停顿
    tts_length = 512

    # 创建一个共享的队列来存储音频文件
    sound_queue = queue.Queue(maxsize=queue_size)
    # 创建两个进程，分别执行生产和消费函数，并把队列和事件作为参数传递给它们
    printer_thread = threading.Thread(target=play_sound)
    printer_thread.start()

    main(tts_length)
