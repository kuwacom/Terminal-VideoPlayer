import cv2
import shutil
import time

def rgbAnsi(r, g, b, txt):
    return f'\033[38;2;{r};{g};{b}m{txt}\033[0m'

def frameToConsole(
        frame, width=30, height=30,
        colorMode='color',
        fontColor=[255, 255, 255], # 完全な白だとコンソールソフト側で色が上書きされることがある
        renderMode='line'):
    # Resize frame
    frame = cv2.resize(frame, (width, height))
    
    char='█'

    # Print to console
    if colorMode=='color': # フルカラー表示
        if renderMode=='once':
            # まとめて描画
            print(f'\033[{height}A', end='')
            lines = ''
            for row in frame:
                line = ''.join(rgbAnsi(pixel[2], pixel[1], pixel[0], char) for pixel in row)
                lines += line + '\n'
            print(lines, end='')
        else: # line
            # 一行ずつ描画
            print(f'\033[{height}A', end='')
            for row in frame:
                line = ''.join(rgbAnsi(pixel[2], pixel[1], pixel[0], char) for pixel in row)
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
        
        # Print to console
        if renderMode=='once':
            print(f'\033[{height}A', end='')
            lines = ''
            for row in gray:
                line = ''.join(chars[pixel] for pixel in row)
                if not fontColor == None:
                    line = rgbAnsi(fontColor[0], fontColor[1], fontColor[2], line)
                lines += line + '\n'
            print(lines, end='')
        else:
            print(f'\033[{height}A', end='')
            for row in gray:
                line = ''.join(chars[pixel] for pixel in row)
                if not fontColor == None:
                    line = rgbAnsi(fontColor[0], fontColor[1], fontColor[2], line)
                print(line)

def videoToConsole(video_path):
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        consoleSize = shutil.get_terminal_size()

        frameToConsole(
            frame, width=consoleSize.columns, height=consoleSize.lines-1,
            colorMode='mono',
            fontColor=None,
            renderMode='once'
        )
        # time.sleep(1 / 24)  # frame interval

    cap.release()

# Video file path
videoPath = './video.webm'

# Play video on console
videoToConsole(videoPath)
