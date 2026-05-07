REQUIRED_MODULES = [
    "flask_cors",
    "flask_limiter",
    "langchain_community",
    "langchain_chroma",
    "joblib",
    "numpy",
    "pandas",
    "sklearn",
    "sqlalchemy",
    "lightgbm",
    "xgboost",
    "catboost",
    "tensorflow",
]


def main() -> int:
    missing = []
    for module_name in REQUIRED_MODULES:
        try:
            __import__(module_name)
        except Exception:
            missing.append(module_name)

    if missing:
        print("Missing modules: " + ", ".join(missing))
        return 1

    print("Python dependencies OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
