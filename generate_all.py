import os
import importlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

FEEDS_DIR = "feeds"
MAX_WORKERS = 6  # можно менять / выносить в env
SLOW_THRESHOLD = 10.0  # сек — считаем сайт "медленным"

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

    print(f"▶️  Запуск {len(modules)} парсеров "
          f"(max_workers={MAX_WORKERS})")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(run_module, mod): mod
            for mod in modules
        }

        for future in as_completed(futures):
            # результат уже выведен внутри run_module
            try:
                future.result()
            except Exception:
                pass  # на всякий случай, но ошибок тут быть не должно

    print("🏁 Все парсеры завершены")

if __name__ == "__main__":
    main()
