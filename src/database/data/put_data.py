# SPDX-License-Identifier: MIT
# --------------------------------------------------------------
# |																|
# |             Copyright 2023 - 2023, Amulya Paritosh			|
# |																|
# |  This file is part of Component Library Plugin for FreeCAD.	|
# |																|
# |               This file was created as a part of				|
# |              Google Summer Of Code Program - 2023			|
# |																|
# --------------------------------------------------------------

import contextlib
import csv
import json
import random
from sqlite3 import IntegrityError

from werkzeug.exceptions import NotAcceptable

from ...models.files.operations import create as create_file
from ...models.licenses.models import SPDX
from ...models.licenses.operations import create as create_license
from ...models.metadatas.models import Metadata
from ...models.metadatas.operations import add_tags
from ...models.metadatas.operations import create as create_meatdata
from ...models.tags.operations import create as create_tag


def db_license_entry(license_csv_path):
    with open(license_csv_path, encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                if SPDX.query.filter(SPDX.fullname == row[0]).one_or_none() is not None:
                    continue

                data = {
                    "fullname": row[0],
                    "identifier": row[1].lower(),
                    "fsf_free": row[2] == "Y",
                    "osi_approved": row[3] == "Y",
                    "license_page": row[4],
                }

                with contextlib.suppress(NotAcceptable):
                    create_license(data)


def db_tags_entry(tags_file_path):
    with open(tags_file_path, "r", encoding="utf-8") as file:
        tags = file.readlines()

    tags = [t.replace("\n", "").lower() for t in tags]

    for tag in tags:
        tag.strip()
        with contextlib.suppress(NotAcceptable):
            create_tag({"label": tag})


def _get_tags(files: dict) -> list[str]:
    any_key = list(files.keys())[0]
    url = files[any_key]["url"]
    *_, file_path = url.split("/", 6)
    file_path = file_path.replace("%20", " ").lower()
    return file_path.split("/")[:-1]


def _make_metadata(component, data):
    metadata_data = {
        "name": component.lower(),
        "version": "1",
        "maintainer": "FreeCAD@gmail.com",
        "author": "FreeCAD@gmail.com",
        "thumbnail": data["images"][0] if len(data["images"]) != 0 else None,
        "description": None,
        "rating": random.randint(1, 5),
        "license_id": str(
            SPDX.query.filter(SPDX.identifier == "apache-1.0").one_or_none().id
        ),
    }

    with contextlib.suppress(NotAcceptable, ValueError):
        new_metadata, _ = create_meatdata(metadata_data)
        tags = _get_tags(data["components"])
        add_tags(new_metadata["id"], tags)


def _make_file(comp_name, data):
    for type_, info in data["components"].items():
        comp_name = comp_name.replace("%20", " ").lower()
        metadata: Metadata = Metadata.query.filter(
            Metadata.name == comp_name
        ).one_or_none()

        comp_data = {
            "url": info["url"],
            "type": type_.lower(),
            "size": info["size"],
            "metadata_id": str(metadata.id),
        }

        try:
            new_comp, _ = create_file(comp_data, str(metadata.id))

        except NotAcceptable:
            pass

        except IntegrityError:
            raise


def _traverse(_dict: dict, traversed_names: set, funcs):
    for key, value in _dict.items():
        if key != "files":
            _traverse(value, traversed_names, funcs)

        else:
            for component, data in value.items():
                if component == "files":
                    continue

                if component in traversed_names:
                    continue

                if len(data["components"].keys()) == 0:
                    traversed_names.add(component)
                    continue

                traversed_names.add(component)
                for func in funcs:
                    func(component, data)


def db_metadata_entry(metadata_file_oath):
    with open(metadata_file_oath, "r", encoding="utf-8") as file:
        data = json.load(file)

    traversed_names = set()
    _traverse(data, traversed_names, [_make_metadata])


def db_file_entry(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    traversed_names = set()
    _traverse(data, traversed_names, [_make_file])


def db_metadata_file_entry(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    traversed_names = set()
    _traverse(data, traversed_names, (_make_metadata, _make_file))
