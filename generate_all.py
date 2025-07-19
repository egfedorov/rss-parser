import os
import importlib

def main():
    feeds_dir = 'feeds'
    for fname in os.listdir(feeds_dir):
        if fname.endswith('.py') and not fname.startswith('_'):
            modname = fname[:-3]
            module = importlib.import_module(f'{feeds_dir}.{modname}')
            if hasattr(module, 'generate'):
                print(f'Generating feed: {modname}')
                module.generate()

if __name__ == '__main__':
    main()
