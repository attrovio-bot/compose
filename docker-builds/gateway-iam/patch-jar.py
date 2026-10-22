#!/usr/bin/env python3
"""Patch application-dev.yaml and HomeController.class in the Spring Boot JAR."""

import struct
import shutil
import tempfile
import os
import zipfile
import sys

OLD_DEV = b'https://dev.christiandellisanti.uk'
NEW_DEV = b'http://100.87.231.127:8080'

OLD_AUTH = b'https://auth.christiandellisanti.uk'
NEW_AUTH = b'http://100.87.231.127:8081'

OLD_WWW = b'https://www.christiandellisanti.uk'
NEW_WWW = b'http://100.87.231.127:8080'


def patch_class_file(data):
    """Replace Utf8 strings in a Java class file constant pool."""
    for old_str, new_str in [(OLD_DEV, NEW_DEV), (OLD_WWW, NEW_WWW)]:
        old_len = len(old_str)
        new_len = len(new_str)
        pattern = struct.pack('>BH', 1, old_len) + old_str
        pos = data.find(pattern)
        if pos < 0:
            print(f"  WARNING: Utf8 entry '{old_str.decode()}' not found in class file")
            continue
        replacement = struct.pack('>BH', 1, new_len) + new_str
        data = data[:pos] + replacement + data[pos + len(pattern):]
        print(f"  Patched Utf8 '{old_str.decode()}' -> '{new_str.decode()}' at 0x{pos:x}")
    return data


def patch_jar(jar_path):
    tmp_jar = jar_path + '.tmp'
    with zipfile.ZipFile(jar_path, 'r') as zin:
        with zipfile.ZipFile(tmp_jar, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)

                if item.filename == 'BOOT-INF/classes/application-dev.yaml':
                    # Patch YAML URLs
                    orig = data
                    data = data.replace(OLD_DEV, NEW_DEV)
                    data = data.replace(OLD_AUTH, NEW_AUTH)
                    data = data.replace(OLD_WWW, NEW_WWW)
                    if data != orig:
                        print(f"  Patched {item.filename}")
                    else:
                        print(f"  WARNING: No changes in {item.filename}")

                elif item.filename == 'BOOT-INF/classes/measuremanager/iam_module/HomeController.class':
                    data = patch_class_file(data)
                    print(f"  Patched {item.filename}")

                zout.writestr(item, data)

    shutil.move(tmp_jar, jar_path)
    print(f"  Written patched JAR: {jar_path}")


if __name__ == '__main__':
    jar = sys.argv[1]
    print(f"Patching {jar}...")
    patch_jar(jar)
    print("Done!")
