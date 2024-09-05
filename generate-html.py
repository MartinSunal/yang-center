#!/usr/bin/env python
import os
import subprocess
from bs4 import BeautifulSoup
import glob


def run_pyang_command(pyang_command: str, yang_path: str):
    # Check if the path is a directory
    if os.path.isdir(yang_path):
        # Expand the wildcard pattern to get all YANG files
        yang_files = glob.glob(os.path.join(yang_path, "*.yang"))
    else:
        yang_files = [yang_path]
    try:
        # Split the pyang_command string into an array of strings using space as the delimiter and add the YANG files
        command = pyang_command.split(" ") + yang_files
        # Run the pyang command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing pyang: {e}")
        print(f"stderr: {e.stderr}")
        raise e

    return result.stdout


def generate_html_from_yang(yang_path):
    result = run_pyang_command("pyang -f jstree", yang_path)
    return BeautifulSoup(result, "html.parser")


def generate_revision_by_module_name_from_yang(yang_path) -> dict[str, str]:
    result = run_pyang_command("pyang -f name --name-print-revision", yang_path)
    result_dict = {}
    for line in result.splitlines():
        key, value = line.split("@")
        result_dict[key.strip()] = value.strip()
    return result_dict


def make_changes_to_html(
    html: BeautifulSoup, revision_by_name: dict[str, str], title: str
):
    # Find and remove logo
    element = html.find("a", href="http://www.tail-f.com")
    if element:
        font = html.new_tag("font")
        font["color"] = "blue"
        font["size"] = "8"
        font.string = title
        h1 = html.new_tag("h1")
        h1.insert(0, font)
        element.replace_with(h1)

    # Find and update h1 elements containing module names to include the revision
    h1_elements = html.find_all("h1")
    for module_name, revision in revision_by_name.items():
        for h1_element in h1_elements:
            if f"Module: {module_name}," in h1_element.text:
                # Add the revision to the h1 element
                font = html.new_tag("font")
                font["color"] = "blue"
                font.string = revision
                h1_element.append(f", Revision: ")
                h1_element.append(font)
                break
    return html


def generate(yang_path):
    html = generate_html_from_yang(yang_path)
    revision_by_name = generate_revision_by_module_name_from_yang(yang_path)
    make_changes_to_html(html, revision_by_name, yang_path)
    # Save the modified HTML content
    with open(f"{yang_path}/index.html", "w", encoding="utf-8") as file:
        file.write(html.decode(formatter="html", eventual_encoding="utf-8"))


def main():
    generate("ONF_TR-532_v2.0")


if __name__ == "__main__":
    main()
