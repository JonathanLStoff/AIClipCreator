import subprocess

def convert_webm_to_mp4(webm_path: str, mp4_path: str) -> None:
    """
    Convert a WEBM video file to MP4 format using ffmpeg.

    Args:
        webm_path: The file path to the source WEBM file.
        mp4_path: The destination file path for the converted MP4 video.

    Raises:
        subprocess.CalledProcessError: If the ffmpeg conversion fails.
    """
    command = [
        "ffmpeg",
        "-i", webm_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-c:a", "aac",
        mp4_path
    ]
    subprocess.run(command, check=True)