import os
import subprocess
from datetime import datetime

def git_push_all(xml_dir, commit_message="Обновление всех RSS-лент"):
    for fname in os.listdir(xml_dir):
        if fname.endswith('.xml'):
            subprocess.run(['git', 'add', os.path.join(xml_dir, fname)])
    subprocess.run(['git', 'commit', '-m', f'{commit_message} {datetime.now().isoformat()}'])
    subprocess.run(['git', 'push'])

if __name__ == '__main__':
    git_push_all(".")
