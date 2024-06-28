import math
import cv2
import shutil
import time
import keyboard

import subprocess
import threading
import sys

from pydub import AudioSegment
from pydub.playback import play

def rgbAnsiBg(r, g, b, txt):
    return f'\033[48;2;{r};{g};{b}m{txt}\033[0m'
def rgbAnsi(r, g, b, txt):
    return f'\033[38;2;{r};{g};{b}m{txt}\033[0m'

def frameToConsole(
        frame, width=30, height=30,
        addLinesToBack=0, # デバッグ用の文字を映像の後の行に追加する
        colorMode='color',
        fontColor=[255, 255, 255], # 完全な白だとコンソールソフト側で色が上書きされることがある
        renderMode='line'):
    height = height - addLinesToBack
    # Resize frame
    frame = cv2.resize(frame, (width, height))
    
    # 色付き文字で描画する場合はこれ
    # char = '█' | line = ''.join(rgbAnsi(pixel[2], pixel[1], pixel[0], char) for pixel in row)
    char = ' '

    # Print to console
    print(f'\033[{height + addLinesToBack}A', end='') # 描画エリアの一番上に戻る
    if colorMode=='color': # フルカラー表示
        if renderMode=='once':
            # まとめて描画
            lines = ''
            for row in frame:
                line = ''.join(rgbAnsiBg(pixel[2], pixel[1], pixel[0], char) for pixel in row)
                lines += line + '\n'
            print(lines, end='')
        else: # line
            # 一行ずつ描画
            for row in frame:
                line = ''.join(rgbAnsiBg(pixel[2], pixel[1], pixel[0], char) for pixel in row)
                print(line)
    else: # モノクロ
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Map grayscale to ASCII
        chars = [
            ' ', '.', ':', '-', '=', '+', '*', '#', '%', '@', 
            '░', '▒', '▓', '█'
        ]
        gray = (gray / 255) * (len(chars) - 1)
        gray = gray.astype(int)
        
        if renderMode=='once':
            lines = ''
            for row in gray:
                line = ''.join(chars[pixel] for pixel in row)
                if not fontColor == None:
                    line = rgbAnsi(fontColor[0], fontColor[1], fontColor[2], line)
                lines += line + '\n'
            print(lines, end='')
        else:
            for row in gray:
                line = ''.join(chars[pixel] for pixel in row)
                if not fontColor == None:
                    line = rgbAnsi(fontColor[0], fontColor[1], fontColor[2], line)
                print(line)

def consoleInit():
    consoleSize = shutil.get_terminal_size()
    print('\n' * (consoleSize.lines - 1))

def mathFloor(num, fNum):
    fNum = (10 ** fNum)
    return math.floor(num * fNum) / fNum

def videoToConsole(videoPath, debug=False, playAudio=True, colorMode='color', fontColor=None, renderMode='line'):
    print('Loading Video File...')
    cap = cv2.VideoCapture(videoPath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frameInterval = mathFloor(1 / fps, 5)

    duration = 0
    fpsHistory = 0

    frameSkipDelay = 0

    # Play Sound
    if playAudio:
        print('Loading Sound File...')
        sound = AudioSegment.from_file('./temp.mp3')

    consoleInit()
    time.sleep(0.1)

    if playAudio:
        soundThread = threading.Thread(target=play, args=(sound,))
        soundThread.setDaemon(True)
        soundThread.start()
    
    videoStartTime = time.perf_counter()
    while cap.isOpened():
        checkQuit()
        if mathFloor(duration, 0) % 4 == 0:
            colorMode = colorChange(colorMode)
        frameStartTime = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            break
        currentFrameNum = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        addLinesToBack = 0
        if debug:
            addLinesToBack = 7

        consoleSize = shutil.get_terminal_size()
        frameToConsole(
            frame, width=consoleSize.columns, height=consoleSize.lines-1, addLinesToBack=addLinesToBack,
            colorMode=colorMode,
            fontColor=fontColor,
            # fontColor=[255, 255, 255],
            renderMode=renderMode
        )
        renderEndTime = time.perf_counter()
        consoleRenderTime = renderEndTime - frameStartTime

        realTime = renderEndTime - videoStartTime
        frameDelayTime = realTime - duration
        
        if duration < realTime - frameInterval:
            duration += frameInterval
            skipSleepTime, skipFrameNum = math.modf((frameDelayTime + frameSkipDelay) / frameInterval)
            
            skipStartTime = time.perf_counter()
            # cap.set(cv2.CAP_PROP_POS_FRAMES, currentFrameNum + int(skipFrameNum))
            for i in range(int(skipFrameNum)):
                cap.grab()
                duration += frameInterval
            skipEndTime = time.perf_counter()
            frameSkipDelay = skipEndTime - skipStartTime

            while duration > realTime:
                realTime = time.perf_counter() - videoStartTime

        else:
            duration += frameInterval
            while duration > realTime:
                realTime = time.perf_counter() - videoStartTime

        if debug:
            endTime = time.perf_counter()
            fps = mathFloor(1 / (endTime - frameStartTime), 2)
            fpsHistory += fps
            print('-'*consoleSize.columns)
            print('FPSAve: '+str(mathFloor(fpsHistory / currentFrameNum, 2)))
            print('FPS: '+str(fps))
            print('Frame Interval: '+str(frameInterval))
            print('console Render Time: '+str(mathFloor(consoleRenderTime, 6)))
            print('Duration: '+str(mathFloor(duration, 6))+' / RealTime'+str(mathFloor(realTime, 6)))
            print('-'*consoleSize.columns)

    videoEndTime = time.perf_counter()
    cap.release()

def checkQuit():
    if keyboard.is_pressed('q'):
        print('停止中...')
        exit()
        # signalHandler()
    return

def colorChange(colorMode):
    if keyboard.is_modifier('c'):
        return 'color' if colorMode == 'mono' else 'mono'
    return colorMode

def ffmpeg(inputFile, outputFile):
    command = ['ffmpeg', '-y', '-i', inputFile, outputFile]
    subprocess.run(command, check=True)

stopEvent = threading.Event()
def signalHandler(sig, frame):
    print('停止中...')
    sys.exit()

if __name__ == '__main__':
    # Video file path
    videoPath = './sikanoko.webm'

    # Convert Audio File
    print('Convert Audio File...')
    ffmpeg(videoPath, './temp.mp3')

    # Play video on console
    videoToConsole(videoPath, debug=False, playAudio=True, colorMode='color', fontColor=None, renderMode='line')