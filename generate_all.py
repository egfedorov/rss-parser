import os
import importlib
from concurrent.futures import ThreadPoolExecutor, as_completed

FEEDS_DIR = "feeds"
MAX_WORKERS = 6  # оптимум для I/O-bound парсеров

def run_module(modname: str) -> None:
    module = importlib.import_module(f"{FEEDS_DIR}.{modname}")

    if hasattr(module, "generate"):
        print(f"⚙️  Generating via generate(): {modname}")
        module.generate()
    elif hasattr(module, "main"):
        print(f"⚙️  Generating via main(): {modname}")
        module.main()
    else:
        print(f"⚠️  {modname}: нет функций generate() или main()")

def main() -> None:
    modules: list[str] = []

    for fname in os.listdir(FEEDS_DIR):
        if (
            fname.endswith(".py")
            and not fname.startswith("_")
            and fname != "__init__.py"
            and not fname.startswith(".")
        ):
            modules.append(fname[:-3])

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(run_module, mod): mod
            for mod in modules
        }

        for future in as_completed(futures):
            mod = futures[future]
            try:
                future.result()
                print(f"✅ {mod}: готово")
            except Exception as e:
                print(f"❌ {mod}: ошибка — {e}")

if __name__ == "__main__":
    main()
