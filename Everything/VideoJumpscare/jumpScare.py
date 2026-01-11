import random # lets me generate random numbers
import subprocess #lets py run external commands
import time
from pathlib import Path

videoPath = Path("Put the path in here")
x = 10000 # this is the denominator, so 1/x
videoInterval = 1 # How often the chance occurs

def playvideo(videoPath: Path):
    #Obliterates any instances of VLC media
    subprocess.run(["pkill", "-f", "cvlc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    #Opens vlc with no UI, then exits when the video ends
    #cvlc = cmd line version
    #--fullscreen = forces fullscreen
    #--no-video-title-show = kills the ui
    #--play-and-exit = closes when the video ends

    subprocess.Popen(["cvlc", 
        "--fullscreen",
        "--no-video-title-show",
        "--play-and-exit",
        str(videoPath),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def main():
        if not videoPath.exists():
            raise FileNotFoundError(f"Fuck you buddy there's no video for me here")

        while True:
            roll = random.randrange(x)
            if roll == 0:
                playvideo(videoPath)
                #Cool down just in case we get the 1/x^2 chance of it playing twice in a row
                time.sleep(5)
            time.sleep(videoInterval)


if __name__ == "__main__":
    main() __
