import json
import os
import queue
from json import JSONDecodeError
from threading import Thread
from typing import Any
import fcntl    

q = queue.Queue()


class AttrDict(dict):
    """Provide dictionary with items accessible as object attributes."""

    def __getattr__(self, attr: str) -> Any:
        """Get attribut."""
        try:
            return self[attr]
        except KeyError as exception:
            raise AttributeError(f"AttrDict has no key {attr!r}") from exception

    def __setattr__(self, attr: str, value: Any) -> None:
        """Set attribut and call save to json file."""
        if isinstance(value, dict) and len(value) == 0:
            value = AttrDict()
        self[attr] = value
        q.put(attr)

    def __delattr__(self, attr: str) -> Any:
        """Delete attribut."""
        try:
            del self[attr]
        except KeyError as exception:
            raise AttributeError(f"AttrDict has no key {attr!r}") from exception


class JsonDB(AttrDict, object):
    """Class for store database to json file.

    Exemple:
        json_db = JsonDB("/var/settings.json", default={"name":"Doe"})
        json_db.surnename = "Joe"
        json_db.city = {}
        json_db.city.name = "Paris"

        print(json_db.name)
        print(json_db.city.name)
    """

    def __init__(self, path, default: dict[Any:Any] = None) -> None:
        """Initialize object.

        path : full qualified path json file , folder create if not exist
        default: default dict for initializing
        """

        def load(restore=False, retry=3) -> None:
            fpath = f"{path}.backup" if restore else path
            if os.path.isfile(fpath):
                with open(fpath, "r") as file:
                    try:
                        data = json.load(file, object_hook=lambda o: AttrDict(**o))
                    except JSONDecodeError as error:
                        if retry > 0:
                            retry -= 1
                            load(restore=False, retry=retry)
                        raise JsonDBException(
                            f"Error while loading file {fpath} ({error})"
                        )
            else:
                data = AttrDict(default)

            for k, v in data.items():
                setattr(self, k, v)

        def save(backup=False, **kwargs) -> None:
            folder = os.path.abspath(os.path.dirname(path))
            os.makedirs(folder, exist_ok=True)
            fpath = f"{path}.backup" if backup else path
            with open(fpath, "w") as file:
                json.dump(
                    self,
                    file,
                    default=lambda o: o.__dict__,
                    sort_keys=True,
                    indent=4,
                    **kwargs,
                )
                file.flush()
                os.fsync(file.fileno())
                file.close()

        def worker() -> None:
            while True:
                item = q.get()
                if item == "__backup__":
                    save(backup=True)
                if item == "__restore__":
                    load(path)
                save()
                q.task_done()

        Thread(target=worker, daemon=True).start()
        load()

    def backup(self):
        q.put("__backup__")

    def restore(self):
        q.put("__restore__")


class JsonDBException(Exception):
    """JsonDB Exception class."""

    pass
