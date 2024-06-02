from pathlib import Path

from platformdirs import user_cache_path


class ConfigDict:
    creds_file: Path
    session_file: Path
    cache_dir: Path
    base_url: str
    creds_file: Path

    def __init__(self):
        self.__creds_file = Path(".auths/creds.json")
        self.__session_file = Path(".auths/app.json")
        self.__runtime_dir = Path('runtime')
        self.__cache_dir = Path('runtime/cache')
        self.__base_url = "https://www.yellowpages.com/"
        if not self.__cache_dir.exists():
            self.__cache_dir.mkdir(parents=True, exist_ok=True)

        ConfigDict.cache_dir = property(lambda self: self.__cache_dir)
        ConfigDict.runtime_dir = property(lambda self: self.__runtime_dir)
        ConfigDict.session_file = property(lambda self: self.__session_file)
        ConfigDict.base_url = property(lambda self: self.__base_url)
        ConfigDict.creds_file = property(lambda self: self.__creds_file)
