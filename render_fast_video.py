import os
import subprocess
import imageio_ffmpeg

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
print(f"Using FFmpeg: {ffmpeg}")

parts = []
for i in range(1, 6):
    slide = f"video_assets/slide{i}.png"
    audio = f"video_assets/audio{i}.mp3"
    part = f"video_assets/part{i}.mp4"
    parts.append(f"file 'part{i}.mp4'\n")
    
    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-framerate", "24",
        "-i", slide,
        "-i", audio,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        part
    ]
    print(f"Encoding Scene {i}...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

with open("video_assets/concat.txt", "w") as f:
    f.writelines(parts)

out_video = "otto_demo_walkthrough.mp4"
concat_cmd = [
    ffmpeg, "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "video_assets/concat.txt",
    "-c", "copy",
    out_video
]
print("Concatenating into final MP4...")
subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"Successfully generated {out_video} (Size: {os.path.getsize(out_video) / 1024 / 1024:.2f} MB)")

