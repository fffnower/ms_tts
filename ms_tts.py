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
        # elif chunk["type"] == "WordBoundary":
        #     print(f"WordBoundary: {chunk}")
    audio_stream.seek(0)
    audio = AudioSegment.from_file(audio_stream)
    return audio

# 消费音频文件
def play_sound():
    # 用一个循环来等待事件
    while True:
        audio = sound_queue.get()
        play(audio)

# 判断是否tts句子是否是纯标点符号组成的
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
    txt_files = []
    idx = 0
    for filename in os.listdir():
        if filename.endswith('.txt'):
            txt_files.append(filename)
            print(f'{idx}. {filename}')
            idx += 1

    selection = input('Enter the number of the file you want to read: ')
    selected_file = txt_files[int(selection)]

    # 检测文件编码
    with open(selected_file, 'rb') as f:
        result = chardet.detect(f.read(32))
    encoding = result['encoding']
    print(f'selected file:{selected_file}\nfile Encoding: {encoding}\n')

    tmp_tts_text = ''
    with codecs.open(selected_file, 'r', encoding=encoding) as file:
        while True:
            chunk = file.read(tts_length)
            if not chunk:
                break
            for idx, c in enumerate(chunk[::-1]):
                if c in ",;:!?，。；：！？\n":
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
    # 队列最大容量，默认为1
    queue_size = 1
    # 单次tts文本长度，默认为300字符
    tts_length = 300

    # 创建一个共享的队列来存储音频文件
    sound_queue = queue.Queue(maxsize=queue_size)
    # 创建两个进程，分别执行生产和消费函数，并把队列和事件作为参数传递给它们
    printer_thread = threading.Thread(target=play_sound)
    printer_thread.start()

    main(tts_length)
