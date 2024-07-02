import argparse
import math
import cv2
import shutil
import time
import keyboard

import subprocess
import threading
import sys

import simpleaudio

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
            # ' ', '.', ':', '-', '=', '+', '*',
            # '░', '▒', '#', '%', '@', '▓', '█',
            ' ','.', ':', '-', '=', '+', '*', 
            '░', '▒', '▓', '█'
        ]
        gray = (gray / 256 * len(chars))
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

def play(sound):
    play = sound.play()
    play.wait_done()

def videoToConsole(videoPath, debug=False, playAudio=True, width=None, height=None, colorMode='color', fontColor=None, renderMode='line'):
    print('Loading Video File...')
    cap = cv2.VideoCapture(videoPath)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frameInterval = mathFloor(1 / fps, 5)

    videoWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    videoHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    aspectRatio = videoHeight / videoWidth

    fullSize = False
    if width != None and height == None:
        height = int(width * aspectRatio)
    elif width == None and height != None:
        width = int(height / aspectRatio)
    else:
        fullSize = True

    duration = 0
    fpsHistory = 0

    frameSkipDelay = 0

    # Play Sound
    if playAudio:
        print('Loading Sound File...')
        sound = simpleaudio.WaveObject.from_wave_file("./temp.wav")

    consoleInit()
    time.sleep(0.1)

    if playAudio:
        soundThread = threading.Thread(target=play, args=(sound,))
        soundThread.daemon = True
        soundThread.start()
    
    videoStartTime = time.perf_counter()
    while cap.isOpened():
        checkQuit()
        # if math.floor(duration) % 2 == 0:
        colorMode = colorChange(colorMode)
        frameStartTime = time.perf_counter()
        ret, frame = cap.read()
        if not ret:
            break
        currentFrameNum = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

        addLinesToBack = 0
        if debug:
            addLinesToBack = 7
        if fullSize:
            consoleSize = shutil.get_terminal_size()
            width=consoleSize.columns
            height=consoleSize.lines-1
        frameToConsole(
            frame, width=width, height=height, addLinesToBack=addLinesToBack,
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
    parser = argparse.ArgumentParser(description='Console Video Player')
    parser.add_argument('videoPath', type=str, help='再生するビデオファイルのpath')
    parser.add_argument('--loop', action='store_true', help='ループ再生')
    parser.add_argument('--width', type=int, help='幅')
    parser.add_argument('--height', type=int, help='高さ')
    parser.add_argument('--playAudio', action='store_true', help='Play audio along with video')
    parser.add_argument('--colorMode', type=str, choices=['mono', 'color'], default='mono', help='フルカラーかモノクロか')
    parser.add_argument('--fontColor', type=str, help='モノクロ時の文字色(例: 256,256,256)')
    parser.add_argument('--renderMode', type=str, choices=['once', 'line'], default='line', help='consoleへのテキストの描画方法')
    parser.add_argument('--debug', action='store_true', help='デバッグモード')
    args = parser.parse_args()
    
    # Video file path
    videoPath = './video.webm'
    if args.videoPath != None:
        videoPath = args.videoPath

    # Convert Audio File
    print('Convert Audio File...')

    if not args.playAudio:
        ffmpeg(videoPath, './temp.wav')

    fontColor=None
    if args.fontColor != None:
        fontColor = args.fontColor.split(',')

    # Play video on console
    while True:
        videoToConsole(videoPath,
            debug=args.debug,
            playAudio=not args.playAudio,
            width=args.width, height=args.height,
            colorMode=args.colorMode, fontColor=fontColor,
            renderMode=args.renderMode
        )
        if not args.loop:
            break