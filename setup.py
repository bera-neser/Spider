import sys
import os
import subprocess

subprocess.check_call(
    [
        sys.executable,
        "-m",
        "venv",
        "venv",
    ]
)

os.system("wget https://raw.githubusercontent.com/bera-neser/Spider/master/spider.py")
os.system("wget https://raw.githubusercontent.com/bera-neser/Spider/master/requirements.txt")
os.system("./venv/bin/pip install -r requirements.txt")
os.remove("requirements.txt")
