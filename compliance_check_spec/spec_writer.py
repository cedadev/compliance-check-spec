import os
import glob
import re
from collections import OrderedDict

from jinja2 import Environment, PackageLoader
import yaml
import click

from cc_yaml.yaml_parser import YamlParser

CHECK_LIB_GIT_REPO = "https://github.com/cedadev/compliance-check-lib"

CHECK_ATTRIBUTE_MAP = OrderedDict([
    ("check_id", "Check ID"),
    ("description", "Description"),
    ("check_level", "Level"),
    ("check_responses", "Responses"),
    ("comments", "Comments"),
    ("base_check", "Python check (link to repository)"),
    ("check_unittest", "Python unittest")
])


def get_html_doc(context):
    """
    Render the HTML template
    :param context: dict to use as jinja2 context
    :return:        rendered HTML as a string
    """
    env = Environment(loader=PackageLoader("compliance_check_spec", "templates"))
    return env.get_template("specification_doc.html.tmpl").render(**context)


def _html_tidy_cell_item(item, key):
    """
    Returns HTML-tidied item for putting in table cell.

    :param item: item to be tidied
    :param key: dictionary key (for reference)
    :return: tidied HTML item or string
    """
    if isinstance(item, dict):
        resp = "<br/>\n".join(["{}: {}".format(key, value) for key, value in item.items()])
        resp += "<br/>{}: SUCCESS!".format(int(key) + 1)
        return resp

    return item


def _get_check_url(check_module, check_class_name):
    """
    Returns the URL to the line in GitHub that represents that checker class.

    :param check_module: python module containing check
    :param check_class_name: name of check class
    :return: URL to check [string].
    """
    # Try to grep line number for class
    try:
        loc_of_module = "../compliance-check-lib/{}.py".format(check_module)
        with open(loc_of_module) as reader:
            for n, line in enumerate(reader):
                if line.find("class {}".format(check_class_name)) == 0:
                    line_number = n + 1
                    break
    except Exception as ex:
        click.echo("WARNING: failed to get check URL: {}".format(ex), err=True)
        line_number = ""

    return "{}/blob/master/{}.py#L{}".format(CHECK_LIB_GIT_REPO, check_module, line_number)


def _get_content_for_html_row(check):
    """
    Returns a list of content for each HTML cell in a table for a given check.

    :param check: check dictionary (from YAML)
    :return:      list of HTML for each column
    """
    contents = []

    # Fill in attributes that are computed from the base check rather that
    # from the YAML
    check_cls = YamlParser.get_base_check_cls(check["check_name"])
    check_obj = check_cls(check["parameters"])
    try:
        check["description"] = check_obj.get_description()
    except IndexError as ex:
        raise IndexError("Error getting description for check '{}': {}"
                         .format(check["check_name"], str(ex)))
    check["check_responses"] = dict(enumerate(check_obj.get_messages()))

    for attr in CHECK_ATTRIBUTE_MAP:
        item = _html_tidy_cell_item(check.get(attr, ""), attr)

        # Handle base check specifically
        if attr == "base_check":
            rel_path = check["check_name"].replace(".", "/")
            base, name = os.path.split(rel_path)

            check_url = _get_check_url(base, name)
            item = "<a href='{}'>{}</a>".format(check_url, name)

            if check["parameters"]:
                item += "<br/>Parameters:"
                for key, value in check["parameters"].items():
                    item += "<br/><b>{}:</b> '{}'".format(key, value)
            else:
                item += "<br/>No parameters."

        elif attr == "check_unittest":
            name = check["check_name"].split(".")[-1]
            unittest_module, unittest_url = _get_unittest_details(name)

            if unittest_module:
                item = "<a href='{}'>{}</a>".format(unittest_url, unittest_module)

        elif attr == "check_id":
            item = "<b>{}</b>".format(item)

        contents.append(item)

    return contents


def _get_unittest_details(check_class_name):
    """
    Returns the information about the module in GitHub that contains unit tests for this class.
    Response is a tuple of (unittest_module_name, unittest_url).

    :param check_class_name: name of check class
    :return: Tuple of (unittest_module_name, URL).
    """
    # Grep each module in the unittests folder until we match a function name with
    # the check class name
    candidate_modules = glob.glob("../compliance-check-lib/checklib/test/test_*.py")

    for mod in candidate_modules:

        with open(mod) as reader:
            for line in reader:

                if re.match("^def .*{}".format(check_class_name), line):
                    module_name = os.path.split(mod)[-1]
                    url = "{}/blob/master/checklib/test/{}".format(CHECK_LIB_GIT_REPO, module_name)
                    return module_name, url

    click.echo("[WARNING] Could not locate unit test for: {}".format(check_class_name),
               err=True)
    return "", ""


def validate_metadata(data_dict):
    """
    Validate a project metadata dict has all the required keys
    :param data_dict:   dictionary to validate (parsed from YAML file)
    :raises ValueError: if dict is invalid
    """
    required_keys = (
        "canonicalName",
        "label",
        "description",
        "vocab_authority",
        "vocab_scope",
        "checks_version"
    )
    opt_keys = (
        "url",
    )

    for key in required_keys:
        if key not in data_dict:
            raise ValueError("Required key '{}' not found".format(key))

    for key in data_dict:
        if key not in required_keys and key not in opt_keys:
            click.echo(
                "WARNING: key '{}' not recognised in project metadata".format(key),
                err=True
            )


@click.command()
@click.option("-p", "--project-metadata", help="Project metadata YAML file",
              type=click.File("r"), required=True)
@click.option("-o", "--output", type=click.File("w"), required=True)
@click.argument("yaml_files", nargs=-1, type=click.File("r"))
def main(project_metadata, output, yaml_files):
    """
    Create a HTML specification document from YAML check files
    """
    if not yaml_files:
        click.echo("No YAML files given")
        return

    metadata = yaml.load(project_metadata)
    try:
        validate_metadata(metadata)
    except ValueError as ex:
        raise click.BadParameter(str(ex), param_hint="project_metadata")

    check_dicts = []
    for check_file in yaml_files:
        try:
            check_dict = yaml.load(check_file)
        except yaml.error.YAMLError as ex:
            raise click.BadParameter(
                "Failed to parse file '{}' from YAML: {}".format(check_file.name, str(ex)),
                param_hint="yaml_files"
            )

        YamlParser.resolve_includes(check_dict, os.path.dirname(check_file.name))

        try:
            YamlParser.validate_config(check_dict)
        except (ValueError, TypeError) as ex:
            raise click.BadParameter(
                "Invalid check YAML in file '{}': {}".format(check_file.name, str(ex)),
                param_hint="yaml_files"
            )
        check_dicts.append(check_dict)

    context = {
        "project_metadata": metadata,
        "categories": {d["suite_name"]: d for d in check_dicts},
        "content": {d["suite_name"]: [_get_content_for_html_row(check) for check in d["checks"]]
                    for d in check_dicts},
        "table_headers": CHECK_ATTRIBUTE_MAP.values(),
    }
    output.write(get_html_doc(context))
