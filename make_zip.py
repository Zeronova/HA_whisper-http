import zipfile
import os

with zipfile.ZipFile('whisper_http.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk('custom_components/whisper_http/'):
        for fn in files:
            path = os.path.join(root, fn)
            zf.write(path, path)
print('ZIP created')
