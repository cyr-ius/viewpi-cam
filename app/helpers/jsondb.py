import json
import os
from json import JSONDecodeError
from typing import Any
import logging

_LOGGER = logging.getLogger(__name__)


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
        self.__path = path
        self.__maping(default)

    def __maping(self, default, restore=False) -> None:
        fpath = f"{self.__path}.backup" if restore else self.__path
        saveset = False
        if os.path.isfile(fpath):
            with open(fpath, "r") as file:
                try:
                    data = json.load(file, object_hook=lambda o: AttrDict(**o))
                except JSONDecodeError as error:
                    raise JsonDBException(f"Error while loading file {fpath} ({error})")
        else:
            data = AttrDict(default)
            saveset = True

        for k, v in data.items():
            setattr(self, k, v)

        if saveset:
            self.save()

    def update(self, **kwargs):
        try:
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.save()
            return True
        except JsonDBException as error:
            _LOGGER.error("Error to update (%s)" % error)
            return False

    def save(self, backup=False, **kwargs) -> bool:
        folder = os.path.abspath(os.path.dirname(self.__path))
        os.makedirs(folder, exist_ok=True)
        fpath = f"{self.__path}.backup" if backup else self.__path
        try:
            with open(fpath, "w") as file:
                obj = self.copy()
                print(obj)
                obj.pop("_JsonDB__path", None)
                json.dump(
                    obj,
                    file,
                    sort_keys=True,
                    indent=4,
                    default=lambda o: o.__dict__,
                    **kwargs,
                )
                file.flush()
                os.fsync(file.fileno())
                file.close()
                return True
        except Exception as error:
            _LOGGER.error("Error to save json (%s)" % error)
            return False

    def backup(self) -> bool:
        return self.save(backup=True)

    def restore(self) -> bool:
        self.__maping(restore=True)
        return self.save()


class JsonDBException(Exception):
    """JsonDB Exception class."""

    pass
