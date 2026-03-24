from deepagents.backends.filesystem import FilesystemBackend
fb = FilesystemBackend('.')
import inspect
for name, obj in inspect.getmembers(fb):
    if name.startswith('get_') and 'tool' in name:
        print(name, obj())
