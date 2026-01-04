import os
import importlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from feedgen.feed import FeedGenerator

FEEDS_DIR = "feeds"
MAX_WORKERS = 6
SLOW_THRESHOLD = 10.0

# ---------------------------------------
# Создаём каталог output/
# ---------------------------------------
Path("output").mkdir(exist_ok=True)

# ---------------------------------------
# Monkey patch FeedGenerator.rss_file
# ---------------------------------------
_original_rss_file = FeedGenerator.rss_file

def patched_rss_file(self, filename, *args, **kwargs):
    # если путь не содержит папку — подставляем output/
    if not str(filename).startswith("output/"):
        filename = f"output/{filename}"
    return _original_rss_file(self, filename, *args, **kwargs)

FeedGenerator.rss_file = patched_rss_file
# ---------------------------------------

def run_module(modname: str) -> None:
    start = time.monotonic()

    try:
        module = importlib.import_module(f"{FEEDS_DIR}.{modname}")

        if hasattr(module, "generate"):
            module.generate()
        elif hasattr(module, "main"):
            module.main()
        else:
            print(f"⚠️  {modname}: нет generate() или main()")
            return

        elapsed = time.monotonic() - start
        prefix = "🐢" if elapsed >= SLOW_THRESHOLD else "⚡"
        print(f"{prefix} {modname}: {elapsed:.2f}s")

    except Exception as e:
        elapsed = time.monotonic() - start
        print(f"❌ {modname}: ошибка через {elapsed:.2f}s — {e}")

def main() -> None:
    modules = [
        fname[:-3]
        for fname in os.listdir(FEEDS_DIR)
        if (
            fname.endswith(".py")
            and not fname.startswith("_")
            and fname != "__init__.py"
            and not fname.startswith(".")
        )
    ]

    print(f"▶️  Запуск {len(modules)} парсеров (max_workers={MAX_WORKERS})")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(run_module, mod): mod for mod in modules}

        for future in as_completed(futures):
            try:
                future.result()
            except Exception:
                pass

    print("🏁 Все парсеры завершены")

if __name__ == "__main__":
    main()
