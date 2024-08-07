"""Helper for database."""

from flask import current_app as ca

from ..helpers.filer import (
    data_file_name,
    get_file_id,
    get_file_info,
    is_existing,
    is_thumbnail,
    list_folder_files,
)
from ..helpers.utils import write_log
from ..models import Files as files_db
from ..models import db


def update_img_db() -> None:
    """Add thumb to database."""
    media_path = ca.raspiconfig.media_path
    files = db.session.execute(db.Select(files_db.id)).scalars().all()
    for thumb in list_folder_files(media_path):
        if (
            is_thumbnail(thumb)
            and (get_file_id(thumb) not in files)
            and is_existing(data_file_name(thumb))
        ):
            info = get_file_info(thumb)
            file = files_db(**info)
            files.append(file.id)
            db.session.add(file)
            db.session.commit()
            write_log(f"Add {file.id} to database")
