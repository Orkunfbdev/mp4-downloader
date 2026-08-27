from setuptools import setup, find_packages

setup(
    name="mp4-downloader",
    version="1.0.0",
    description="YouTube, TikTok, Twitter/X, Instagram ve 1000+ siteden eşzamanlı MP4 video indirici CLI",
    author="Orkun",
    py_modules=["downloader"],
    install_requires=[
        "yt-dlp>=2025.1.15",
        "rich>=13.7.0",
        "imageio-ffmpeg>=0.5.1",
        "curl-cffi>=0.7.0",
    ],
    entry_points={
        "console_scripts": [
            "orkunfb=downloader:main",
            "indir=downloader:main",
            "mp4=downloader:main",
        ],
    },
    python_requires=">=3.8",
)
