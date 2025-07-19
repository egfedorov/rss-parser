import os
import importlib

def main():
    feeds_dir = 'feeds'
    for fname in os.listdir(feeds_dir):
        # Игнорируем не-Python-файлы, скрытые файлы, __init__.py и всё, что начинается с "_"
        if (
            not fname.endswith('.py')
            or fname.startswith('_')
            or fname == '__init__.py'
            or fname.startswith('.')
        ):
            continue
        modname = fname[:-3]
        try:
            module = importlib.import_module(f'{feeds_dir}.{modname}')
            if hasattr(module, 'generate'):
                print(f'Generating feed: {modname}')
                module.generate()
            else:
                print(f'⚠️  {modname}: нет функции generate()')
        except Exception as e:
            print(f'❌ Ошибка при генерации {modname}: {e}')

if __name__ == '__main__':
    main()
    
