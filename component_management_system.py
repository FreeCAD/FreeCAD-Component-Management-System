#!.venv/bin/python

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


from dotenv import load_dotenv

from src import create_app

if __name__ == "__main__":
    load_dotenv(override=True)
    app = create_app()
    app.run(host="127.0.0.1", port=5000)
