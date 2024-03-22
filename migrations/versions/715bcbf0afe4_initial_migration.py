"""Initial migration.

Revision ID: 715bcbf0afe4
Revises: 
Create Date: 2024-02-24 15:46:29.109800

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "715bcbf0afe4"
down_revision = None
branch_labels = None
depends_on = None


def seed_data():
    presets = sa.sql.table(
        "presets",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("mode", sa.String),
        sa.sql.column("name", sa.String),
        sa.sql.column("width", sa.Integer),
        sa.sql.column("height", sa.Integer),
        sa.Column("fps", sa.Integer),
        sa.sql.column("i_width", sa.Integer),
        sa.sql.column("i_height", sa.Integer),
        sa.sql.column("i_rate", sa.Integer),
    )
    op.bulk_insert(
        presets,
        [
            {
                "id": 1,
                "mode": "v2",
                "name": "Full HD 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 2,
                "mode": "v2",
                "name": "Full HD 720p 16:9",
                "width": 1280,
                "height": 720,
                "fps": 30,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 3,
                "mode": "v2",
                "name": "Max View 972p 4:3",
                "width": 1296,
                "height": 972,
                "fps": 30,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 4,
                "mode": "v2",
                "name": "SD TV 576p 4:3",
                "width": 768,
                "height": 576,
                "fps": 30,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 5,
                "mode": "v2",
                "name": "Full HD Timelapse (x30) 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 1,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 6,
                "mode": "P-OV5647",
                "name": "Full HD 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 25,
                "i_rate": 25,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 7,
                "mode": "P-OV5647",
                "name": "Full Chip 2959 X 1944 4:3",
                "width": 2592,
                "height": 1944,
                "fps": 15,
                "i_rate": 15,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 8,
                "mode": "P-OV5647",
                "name": "Max View 1296 X 972 4:3",
                "width": 1296,
                "height": 972,
                "fps": 42,
                "i_rate": 42,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 9,
                "mode": "P-OV5647",
                "name": "Max View 1296 X 730 16:9",
                "width": 1296,
                "height": 730,
                "fps": 49,
                "i_rate": 49,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 10,
                "mode": "P-OV5647",
                "name": "SD TV 640 X 480 4:3",
                "width": 640,
                "height": 480,
                "fps": 90,
                "i_rate": 90,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 11,
                "mode": "P-OV5647",
                "name": "Full HD Timelapse (x30) 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 1,
                "i_rate": 30,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 12,
                "mode": "P-IMX219",
                "name": "Full HD 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 25,
                "i_rate": 25,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 13,
                "mode": "P-IMX219",
                "name": "Full Chip 2959 X 1944 4:3",
                "width": 3280,
                "height": 2464,
                "fps": 15,
                "i_rate": 15,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 14,
                "mode": "P-IMX219",
                "name": "Max View 1640 X 1232 4:3",
                "width": 1640,
                "height": 1232,
                "fps": 40,
                "i_rate": 40,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 15,
                "mode": "P-IMX219",
                "name": "Max View 1640 X 922 16:9",
                "width": 1640,
                "height": 922,
                "fps": 40,
                "i_rate": 40,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 16,
                "mode": "P-IMX219",
                "name": "HD 720p 16:9",
                "width": 1280,
                "height": 720,
                "fps": 90,
                "i_rate": 90,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 17,
                "mode": "P-IMX219",
                "name": "SD TV 640p 4:3",
                "width": 640,
                "height": 480,
                "fps": 90,
                "i_rate": 90,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 18,
                "mode": "P-IMX219",
                "name": "Full HD Timelapse (x30) 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 1,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 19,
                "mode": "N-OV5647",
                "name": "Full HD 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "i_rate": 30,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 20,
                "mode": "N-OV5647",
                "name": "Full Chip 2959 X 1944 4:3",
                "width": 2592,
                "height": 1944,
                "fps": 15,
                "i_rate": 15,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 21,
                "mode": "N-OV5647",
                "name": "Max View 1296 X 972 4:3",
                "width": 1296,
                "height": 972,
                "fps": 42,
                "i_rate": 42,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 22,
                "mode": "N-OV5647",
                "name": "Max View 1296 X 730 16:9",
                "width": 1296,
                "height": 730,
                "fps": 49,
                "i_rate": 49,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 23,
                "mode": "N-OV5647",
                "name": "SD TV 640 X 480 4:3",
                "width": 640,
                "height": 480,
                "fps": 90,
                "i_rate": 90,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 24,
                "mode": "N-OV5647",
                "name": "Full HD Timelapse (x30) 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 1,
                "i_rate": 30,
                "i_width": 2592,
                "i_height": 1944,
            },
            {
                "id": 25,
                "mode": "N-IMX219",
                "name": "Full HD 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 30,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 26,
                "mode": "N-IMX219",
                "name": "Full Chip 2959 X 1944 4:3",
                "width": 3280,
                "height": 2464,
                "fps": 15,
                "i_rate": 15,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 27,
                "mode": "N-IMX219",
                "name": "Max View 1640 X 1232 4:3",
                "width": 1640,
                "height": 1232,
                "fps": 40,
                "i_rate": 40,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 28,
                "mode": "N-IMX219",
                "name": "Max View 1640 X 922 16:9",
                "width": 1640,
                "height": 922,
                "fps": 40,
                "i_rate": 40,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 29,
                "mode": "N-IMX219",
                "name": "HD 720p 16:9",
                "width": 1280,
                "height": 720,
                "fps": 90,
                "i_rate": 90,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 30,
                "mode": "N-IMX219",
                "name": "SD TV 640p 4:3",
                "width": 640,
                "height": 480,
                "fps": 90,
                "i_rate": 90,
                "i_width": 3280,
                "i_height": 2464,
            },
            {
                "id": 31,
                "mode": "N-IMX219",
                "name": "Full HD Timelapse (x30) 1080p 16:9",
                "width": 1920,
                "height": 1080,
                "fps": 1,
                "i_rate": 30,
                "i_width": 3280,
                "i_height": 2464,
            },
        ],
    )

    roles = sa.sql.table(
        "roles",
        sa.sql.column("name", sa.String),
        sa.sql.column("level", sa.Integer),
    )
    op.bulk_insert(
        roles,
        [
            {"name": "min", "level": 1},
            {"name": "preview", "level": 2},
            {"name": "medium", "level": 4},
            {"name": "max", "level": 8},
        ],
    )

    daysmode = sa.sql.table(
        "daysmode",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("name", sa.String),
    )
    op.bulk_insert(
        daysmode,
        [
            {"id": 0, "name": "Sun based"},
            {"id": 1, "name": "All Day"},
            {"id": 2, "name": "Fixed Times"},
        ],
    )

    calendar = sa.sql.table(
        "calendar",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("name", sa.String),
    )
    op.bulk_insert(
        calendar,
        [
            {"id": 0, "name": "Mon"},
            {"id": 1, "name": "Tue"},
            {"id": 2, "name": "Wed"},
            {"id": 3, "name": "Thu"},
            {"id": 4, "name": "Fri"},
            {"id": 5, "name": "Sat"},
            {"id": 6, "name": "Sun"},
        ],
    )

    scheduler = sa.sql.table(
        "scheduler",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("command_on", sa.String),
        sa.sql.column("command_off", sa.String),
        sa.sql.column("mode", sa.String),
        sa.sql.column("period", sa.String),
        sa.sql.column("daysmode_id", sa.Integer),
        sa.sql.column("enabled", sa.Boolean),
    )
    all_day = [
        {
            "id": 0,
            "command_on": "ca 1",
            "command_off": "ca 0",
            "period": "allday",
            "mode": "md 1;em auto;",
            "daysmode_id": 1,
            "enabled": True,
        }
    ]
    sun_bases = [
        {
            "id": 1,
            "daysmode_id": 0,
            "command_on": "ca 1",
            "command_off": "ca 0",
            "period": "night",
            "mode": "md1;em night;",
            "enabled": True,
        },
        {
            "id": 2,
            "daysmode_id": 0,
            "command_on": "ca 1",
            "command_off": "ca 0",
            "period": "dawn",
            "mode": "md1;em night;",
            "enabled": True,
        },
        {
            "id": 3,
            "daysmode_id": 0,
            "command_on": "ca 1",
            "command_off": "ca 0",
            "period": "day",
            "mode": "md 1;em auto;",
            "enabled": True,
        },
        {
            "id": 4,
            "daysmode_id": 0,
            "command_on": "ca 1",
            "command_off": "ca 0",
            "period": "dusk",
            "mode": "md 1;em auto;",
            "enabled": True,
        },
    ]
    fixed_times = [
        {
            "id": i,
            "daysmode_id": 2,
            "command_on": "ca 1",
            "command_off": "ca 0",
            "period": f"{i-5}:00",
            "mode": "md 1;em auto;",
            "enabled": True,
        }
        for i in range(5, 29)
    ]
    op.bulk_insert(scheduler, all_day + sun_bases + fixed_times)

    scheduler_calendar = sa.sql.table(
        "scheduler_calendar",
        sa.sql.column("scheduler_id", sa.Integer),
        sa.sql.column("calendar_id", sa.Integer),
    )
    calendar = []
    for i in range(0, 29):
        for j in range(0, 7):
            calendar.append({"scheduler_id": i, "calendar_id": j})
    op.bulk_insert(scheduler_calendar, calendar)

    users = sa.sql.table(
        "users",
        sa.sql.column("id", sa.Integer),
        sa.sql.column("alternative_id", sa.String),
        sa.sql.column("enabled", sa.Boolean),
        sa.sql.column("name", sa.String),
        sa.sql.column("right", sa.Integer),
    )
    op.bulk_insert(
        users,
        [
            {
                "id": 0,
                "alternative_id": 0,
                "enabled": False,
                "name": "system",
                "right": 8,
            }
        ],
    )

    settings = sa.sql.table(
        "settings",
        sa.sql.column("data", sa.JSON),
    )
    op.bulk_insert(
        settings,
        [
            {
                "data": {
                    "daymode": 1,
                    "cmd_poll": 0.03,
                    "gmt_offset": "Etc/UTC",
                    "loglevel": "INFO",
                    "latitude": 52.0,
                    "longitude": 0.0,
                    "management_interval": 3600,
                    "mode_poll": 10,
                    "upreset": "v2",
                    "duskend_minutes": 180,
                    "dawnstart_minutes": -180,
                    "autocamera_interval": 0,
                    "autocapture_interval": 0,
                    "dayend_minutes": 0,
                    "daystart_minutes": 0,
                    "max_capture": 0,
                    "purgeimage_hours": 0,
                    "purgelapse_hours": 0,
                    "purgespace_level": 10,
                    "purgespace_modeex": 10,
                    "purgevideo_hours": 0,
                    "pipan": False,
                    "servo": False,
                    "pilight": False,
                }
            }
        ],
    )


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "multiviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("delay", sa.Integer()),
        sa.Column("state", sa.Integer()),
        sa.Column("url", sa.String()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "presets",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("mode", sa.String(), nullable=False),
        sa.Column("name", sa.String()),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("fps", sa.Integer()),
        sa.Column("i_width", sa.Integer()),
        sa.Column("i_height", sa.Integer()),
        sa.Column("i_rate", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "roles",
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("level"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("alternative_id", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean),
        sa.Column("locale", sa.String(length=2)),
        sa.Column("name", sa.String()),
        sa.Column("secret", sa.String()),
        sa.Column("otp_secret", sa.String()),
        sa.Column("otp_confirmed", sa.Boolean()),
        sa.Column("api_token", sa.String()),
        sa.Column("cam_token", sa.String()),
        sa.Column("right", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKey("right", "roles.id"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("alternative_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "lock_files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "ubuttons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("macro", sa.String(), nullable=False),
        sa.Column("css_class", sa.String()),
        sa.Column("style", sa.String()),
        sa.Column("other", sa.String()),
        sa.Column("display", sa.Boolean()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "scheduler",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("command_on", sa.String()),
        sa.Column("command_off", sa.String()),
        sa.Column("period", sa.String()),
        sa.Column("mode", sa.String()),
        sa.Column("enabled", sa.Boolean()),
        sa.Column("daysmode_id", sa.Integer()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKey("daysmode_id", "daysmode.id"),
    )
    op.create_table(
        "daysmode",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "calendar",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scheduler_calendar",
        sa.Column("scheduler_id", sa.Integer(), nullable=False),
        sa.Column("calendar_id", sa.Integer(), nullable=False),
        sa.ForeignKey("scheduler_id", "scheduler.id"),
        sa.ForeignKey("calendar_id", "calendar.id"),
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_foreign_key("None", "roles", ["id"], ["right"])

    with op.batch_alter_table("scheduler", schema=None) as batch_op:
        batch_op.create_foreign_key("None", "daysmode", ["id"], ["daysmode_id"])

    with op.batch_alter_table("scheduler_calendar", schema=None) as batch_op:
        batch_op.create_foreign_key("None", "calendar", ["id"], ["calendar_id"])
        batch_op.create_foreign_key("None", "scheduler", ["id"], ["scheduler_id"])

    # ### end Alembic commands ###

    # Insert default values to the database
    seed_data()


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("multiviews")
    op.drop_table("presets")
    op.drop_table("settings")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("ubuttons")
    op.drop_table("scheduler")
    op.drop_table("daysmode")
    op.drop_table("calendar")
    op.drop_table("scheduler_calendar")
    # ### end Alembic commands ###
