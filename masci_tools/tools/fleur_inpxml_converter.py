# -*- coding: utf-8 -*-

from masci_tools.io.parsers.fleur_schema import InputSchemaDict
from masci_tools.io.io_fleurxml import load_inpxml
from masci_tools.util.schema_dict_util import evaluate_attribute
from masci_tools.util.xml.xml_setters_basic import xml_delete_tag, xml_delete_att
from masci_tools.util.xml.xml_setters_xpaths import xml_create_tag_schema_dict
from masci_tools.util.xml.xml_setters_names import set_attrib_value
from masci_tools.util.xml.common_functions import split_off_attrib, split_off_tag, eval_xpath
from masci_tools.cmdline.parameters.slice import IntegerSlice
from masci_tools.cmdline.utils import echo
from collections import UserList
from typing import NamedTuple, Tuple
import tabulate
import json
from lxml import etree

import click
from pathlib import Path

FILE_DIRECTORY = Path(__file__).parent.resolve()


#These are the possible conversions that we can do
class MoveAction(NamedTuple):
    old_name: str
    new_name: str
    old_path: str
    new_path: str
    attrib: bool = False


class AmbiguousAction(NamedTuple):
    name: str
    old_paths: Tuple[str]
    new_paths: Tuple[str]
    attrib: bool


class RemoveAction(NamedTuple):
    name: str
    path: str
    attrib: bool = False


class CreateAction(NamedTuple):
    name: str
    path: str
    attrib: bool = False


def analyse_paths(schema_start, schema_target, path_entries):

    if not isinstance(path_entries, list):
        path_entries = [path_entries]

    paths_start = {}
    paths_target = {}
    for path_entry in path_entries:
        paths_start.update(schema_start[path_entry])
        paths_target.update(schema_target[path_entry])

    removed_keys = paths_start.keys() - paths_target.keys()
    remove = []
    for key in removed_keys:
        paths = paths_start[key]
        if not isinstance(paths, (list, UserList)):
            paths = [paths]
        for path in paths:
            attrib = '@' in path
            if attrib:
                path, name = split_off_attrib(path)
            else:
                _, name = split_off_tag(path)
            remove.append(RemoveAction(name=name, path=path, attrib=attrib))

    new_keys = paths_target.keys() - paths_start.keys()
    create = []
    for key in new_keys:
        paths = paths_target[key]
        if not isinstance(paths, (list, UserList)):
            paths = [paths]
        for path in paths:
            attrib = '@' in path
            if attrib:
                path, name = split_off_attrib(path)
            else:
                _, name = split_off_tag(path)
            create.append(CreateAction(name=name, path=path, attrib=attrib))

    move = []
    ambiguous = []
    possible_change_keys = paths_start.keys() & paths_target.keys()
    for key in possible_change_keys:
        old_paths = paths_start[key]
        new_paths = paths_target[key]

        if old_paths == new_paths:
            continue

        if not isinstance(old_paths, (list, UserList)):
            old_paths = [old_paths]

        if not isinstance(new_paths, (list, UserList)):
            new_paths = [new_paths]

        old_paths = set(old_paths)
        new_paths = set(new_paths)

        different_paths = old_paths.symmetric_difference(new_paths)
        if len(different_paths) == 1:
            path = different_paths.pop()
            if path in old_paths:
                attrib = '@' in path
                if attrib:
                    path, name = split_off_attrib(path)
                else:
                    _, name = split_off_tag(path)
                remove.append(RemoveAction(name=name, path=path, attrib=attrib))
            else:
                attrib = '@' in path
                if attrib:
                    path, name = split_off_attrib(path)
                else:
                    _, name = split_off_tag(path)
                create.append(CreateAction(name=name, path=path, attrib=attrib))
        elif len(different_paths) == 2:
            if all(path in old_paths for path in different_paths):
                for path in different_paths:
                    attrib = '@' in path
                    if attrib:
                        path, name = split_off_attrib(path)
                    else:
                        _, name = split_off_tag(path)
                    remove.append(RemoveAction(name=name, path=path, attrib=attrib))
                continue
            if all(path in new_paths for path in different_paths):
                for path in different_paths:
                    attrib = '@' in path
                    if attrib:
                        path, name = split_off_attrib(path)
                    else:
                        _, name = split_off_tag(path)
                    create.append(CreateAction(name=name, path=path, attrib=attrib))
                continue
            first_path = different_paths.pop()
            attrib = '@' in first_path
            if attrib:
                first_path, first_name = split_off_attrib(first_path)
            else:
                _, first_name = split_off_tag(first_path)

            second_path = different_paths.pop()
            if attrib:
                second_path, second_name = split_off_attrib(second_path)
            else:
                _, second_name = split_off_tag(second_path)

            if first_path in old_paths:
                move.append(
                    MoveAction(old_name=first_name, old_path=first_path, new_name=second_name, new_path=second_path))
            else:
                move.append(
                    MoveAction(old_name=second_name, old_path=second_path, new_name=first_name, new_path=first_path))
        else:
            path = list(old_paths)[0]
            attrib = '@' in path
            if attrib:
                path, name = split_off_attrib(path)
            else:
                _, name = split_off_tag(path)
            ambiguous.append(
                AmbiguousAction(name=name, old_paths=tuple(old_paths), new_paths=tuple(new_paths), attrib=attrib))

    return remove, create, move, ambiguous


def resolve_ambiguouities(ambiguous,
                          remove,
                          create,
                          move,
                          remove_create=False,
                          remove_move=False,
                          tag_create=None,
                          tag_remove=None,
                          tag_move=None):

    for action in ambiguous.copy():

        ambiguous.remove(action)

        old_paths = set(action.old_paths)
        new_paths = set(action.new_paths)

        if tag_remove is None:
            tag_remove = remove
        for old_path in old_paths.copy():
            for action2 in tag_remove:
                if action2.path in old_path:
                    old_paths.discard(old_path)

        if remove_create:
            if tag_create is None:
                tag_create = create
            for new_path in new_paths.copy():
                for action2 in tag_create:
                    if action2.path in new_path:
                        new_paths.discard(new_path)

        if remove_move:
            if tag_move is None:
                tag_move = move
            for old_path in old_paths.copy():
                for action2 in tag_move:
                    if action2.old_path in old_path:
                        old_paths.discard(old_path)
            for new_path in new_paths.copy():
                for action2 in tag_move:
                    if action2.new_path in new_path:
                        new_paths.discard(new_path)

        if old_paths == new_paths:
            continue

        if not old_paths and new_paths:
            for path in new_paths:
                attrib = '@' in path
                if attrib:
                    path, name = split_off_attrib(path)
                else:
                    _, name = split_off_tag(path)
                create.append(CreateAction(name=name, path=path, attrib=attrib))
            continue

        if old_paths and not new_paths:
            for path in new_paths:
                attrib = '@' in path
                if attrib:
                    path, name = split_off_attrib(path)
                else:
                    _, name = split_off_tag(path)
                remove.append(RemoveAction(name=name, path=path, attrib=attrib))
            continue

        different_paths = old_paths.symmetric_difference(new_paths)
        print(different_paths)
        if len(different_paths) == 1:
            path = different_paths.pop()
            if path in old_paths:
                attrib = '@' in path
                if attrib:
                    path, name = split_off_attrib(path)
                else:
                    _, name = split_off_tag(path)
                remove.append(RemoveAction(name=name, path=path, attrib=attrib))
            else:
                attrib = '@' in path
                if attrib:
                    path, name = split_off_attrib(path)
                else:
                    _, name = split_off_tag(path)
                create.append(CreateAction(name=name, path=path, attrib=attrib))
        elif len(different_paths) == 2:
            if all(path in old_paths for path in different_paths):
                for path in different_paths:
                    attrib = '@' in path
                    if attrib:
                        path, name = split_off_attrib(path)
                    else:
                        _, name = split_off_tag(path)
                    remove.append(RemoveAction(name=name, path=path, attrib=attrib))
                continue
            if all(path in new_paths for path in different_paths):
                for path in different_paths:
                    attrib = '@' in path
                    if attrib:
                        path, name = split_off_attrib(path)
                    else:
                        _, name = split_off_tag(path)
                    create.append(CreateAction(name=name, path=path, attrib=attrib))
                continue
            first_path = different_paths.pop()
            attrib = '@' in first_path
            if attrib:
                first_path, first_name = split_off_attrib(first_path)
            else:
                _, first_name = split_off_tag(first_path)

            second_path = different_paths.pop()
            if attrib:
                second_path, second_name = split_off_attrib(second_path)
            else:
                _, second_name = split_off_tag(second_path)
            if first_path in old_paths:
                move.append(
                    MoveAction(old_name=first_name, old_path=first_path, new_name=second_name, new_path=second_path))
            else:
                move.append(
                    MoveAction(old_name=second_name, old_path=second_path, new_name=first_name, new_path=first_path))
        else:
            ambiguous.append(
                AmbiguousAction(name=action.name,
                                old_paths=tuple(old_paths),
                                new_paths=tuple(new_paths),
                                attrib=action.attrib))


def trim_paths(paths):

    path_copy = paths.copy()
    for action in path_copy:
        for action2 in path_copy:
            if action == action2:
                continue
            if action.path in action2.path:
                if action2 in paths:
                    paths.remove(action2)

    return paths


def trim_attrib_paths(paths, tag_paths):

    path_copy = paths.copy()
    for tag_action in tag_paths:
        for attrib_action in path_copy:
            if tag_action.path in attrib_action.path:
                if attrib_action in paths:
                    paths.remove(attrib_action)

    return paths


def trim_move_paths(paths):

    path_copy = paths.copy()
    for action in path_copy:
        for action2 in path_copy:
            if action == action2:
                continue
            if action.old_path in action2.old_path:
                if action2 in paths:
                    paths.remove(action2)

    return paths


def trim_attrib_move_paths(paths, tag_paths):

    path_copy = paths.copy()
    for action in tag_paths:
        for action2 in path_copy:
            if action.old_path in action2.old_path:
                print(action.old_path)
                if action2 in paths:
                    paths.remove(action2)

    return paths


def remove_action(paths, name):

    matching = []
    for action in paths.copy():
        if action.name == name:
            paths.remove(action)
            matching.append(action)

    if not matching:
        raise ValueError(f'Action {name} not found')

    return matching


def load_conversion(from_version, to_version):
    """
    """
    filepath = FILE_DIRECTORY / f"conversion_{from_version.replace('.','')}_to_{to_version.replace('.','')}.json"

    with open(filepath, 'r', encoding='utf-8') as f:
        conversion = json.load(f)

    return conversion


@click.group('inpxml')
def inpxml():
    """
    """
    pass


@inpxml.command('convert')
@click.argument('xml-file', type=click.Path(exists=True))
@click.argument('to_version', type=str)
@click.pass_context
def convert_inpxml(ctx, xml_file, to_version):
    """
    """

    xmltree, schema_dict = load_inpxml(xml_file)
    schema_dict_target = InputSchemaDict.fromVersion(to_version)

    from_version = evaluate_attribute(xmltree, schema_dict, 'fleurInputVersion')

    try:
        conversion = load_conversion(from_version, to_version)
    except FileNotFoundError:
        echo.echo_warning(f'No conversion available between versions {from_version} to {to_version}')
        if click.confirm('Do you want to generate this conversion now'):
            conversion = ctx.invoke(generate_inp_conversion, from_version=from_version, to_version=to_version)
        else:
            echo.echo_critical('Cannot convert')

    set_attrib_value(xmltree, schema_dict_target, 'fleurInputVersion', to_version)
    for action in conversion['tag']['remove']:
        action = RemoveAction(*action)
        xml_delete_tag(xmltree, action.path)

    for action in conversion['attrib']['remove']:
        action = RemoveAction(*action)
        xml_delete_att(xmltree, action.path, action.name)

    for action in conversion['tag']['move']:
        action = MoveAction(*action)

        nodes = eval_xpath(xmltree, action.old_path, list_return=True)
        print(action)
        for node in nodes:
            path, _ = split_off_tag(action.new_path)
            print(path)
            print(etree.tostring(xmltree, encoding='unicode', pretty_print=True))
            xml_create_tag_schema_dict(xmltree, schema_dict_target, path, path, node, create_parents=True)


@inpxml.command('generate-conversion')
@click.argument('from_version', type=str)
@click.argument('to_version', type=str)
def generate_inp_conversion(from_version, to_version):
    """
    """
    TAG_ENTRY = 'tag_paths'
    ATTRIB_ENTRIES = ['unique_attribs', 'unique_path_attribs', 'other_attribs']

    from_schema = InputSchemaDict.fromVersion(from_version)
    to_schema = InputSchemaDict.fromVersion(to_version)

    remove_tags, create_tags, move_tags, ambiguous_tags = analyse_paths(from_schema, to_schema, TAG_ENTRY)

    remove_tags = trim_paths(remove_tags)
    create_tags = trim_paths(create_tags)
    move_tags = trim_move_paths(move_tags)

    rename = True
    while remove_tags and create_tags and rename:
        click.echo('The following tags are not found in the target version:')
        click.echo(tabulate.tabulate(remove_tags, showindex=True))
        click.echo('The following tags are not found in the start version:')
        click.echo(tabulate.tabulate(create_tags, showindex=True))

        rename = click.confirm('Are there tags that were renamed?')

        if rename:
            old_name = click.prompt(f'Name in version {from_version}')
            new_name = click.prompt(f'Name in version {to_version}')

            remove = remove_action(remove_tags, old_name)
            create = remove_action(create_tags, new_name)

            if len(remove) != len(create):
                raise ValueError('Not supported')

            for old, new in zip(remove, create):
                move_tags.append(MoveAction(old_name=old.name, old_path=old.path, new_name=new.name, new_path=new.path))
            move_tags = trim_move_paths(move_tags)

    #Check again if we can now resolve ambiguouities
    resolve_ambiguouities(ambiguous_tags, remove_tags, create_tags, move_tags)

    click.echo('The following tags will be moved:')
    click.echo(tabulate.tabulate(move_tags, showindex=True))

    while ambiguous_tags:
        click.echo('The following tags could not be resolved automatically:')
        click.echo(tabulate.tabulate(ambiguous_tags, showindex=True))

        row = click.prompt('Enter the row you want to clarify')

    remove_attrib, create_attrib, move_attrib, ambiguous_attrib = analyse_paths(from_schema, to_schema, ATTRIB_ENTRIES)

    remove_attrib = trim_attrib_paths(remove_attrib, remove_tags)
    create_attrib = trim_attrib_paths(create_attrib, create_tags)
    move_attrib = trim_attrib_move_paths(move_attrib, move_tags)

    rename = True
    while remove_attrib and create_attrib and rename:
        click.echo('The following attribs are not found in the target version:')
        click.echo(tabulate.tabulate(remove_attrib, showindex=True))
        click.echo('The following attribs are not found in the start version:')
        click.echo(tabulate.tabulate(create_attrib, showindex=True))

        rename = click.confirm('Are there attribs that were renamed?')

        if rename:
            old_name = click.prompt(f'Name in version {from_version}')
            new_name = click.prompt(f'Name in version {to_version}')

            remove = remove_action(remove_attrib, old_name)
            create = remove_action(create_attrib, new_name)

            if len(remove) != len(create):
                raise ValueError('Not supported')

            for old, new in zip(remove, create):
                move_tags.append(MoveAction(old_name=old.name, old_path=old.path, new_name=new.name, new_path=new.path))
            move_attrib = trim_move_paths(move_attrib)

    #Check again if we can now resolve ambiguouities
    resolve_ambiguouities(ambiguous_attrib,
                          remove_attrib,
                          create_attrib,
                          move_attrib,
                          remove_create=True,
                          remove_move=True,
                          tag_create=create_tags,
                          tag_remove=remove_tags,
                          tag_move=move_tags)

    click.echo('The following attribs will be moved:')
    click.echo(tabulate.tabulate(move_attrib, showindex=True))

    while ambiguous_attrib:
        click.echo('The following attribs could not be resolved automatically:')
        click.echo(tabulate.tabulate(ambiguous_attrib, showindex=True))

        row = click.prompt('Enter the row you want to clarify', type=int)

        entry = ambiguous_attrib[row]

        click.echo(f'Entry {entry.name}:')

        old_paths = sorted(entry.old_paths)
        new_paths = sorted(entry.new_paths)

        while (new_paths or old_paths) and new_paths != old_paths:
            old_paths_display, new_paths_display = old_paths.copy(), new_paths.copy()
            if len(old_paths) < len(new_paths):
                old_paths_display += [None] * (len(new_paths) - len(old_paths))
            elif len(new_paths) < len(old_paths):
                new_paths_display += [None] * (len(old_paths) - len(new_paths))

            click.echo(tabulate.tabulate(list(zip(old_paths_display, new_paths_display)), showindex=True))

            action = click.prompt('Which action should be performed', type=click.Choice(['create', 'remove', 'rename']))

            if action == 'remove':
                path_row = click.prompt('Enter the row you want to remove from the old paths', type=int)
                path = old_paths.pop(path_row)
                remove_attrib.append(RemoveAction(name=entry.name, path=path, attrib=entry.attrib))
            elif action == 'create':
                path_row = click.prompt('Enter the row you want to create from the new paths', type=IntegerSlice())
                paths = new_paths[path_row]
                if not isinstance(paths, list):
                    paths = [paths]
                for path in paths:
                    new_paths.remove(path)
                    create_attrib.append(CreateAction(name=entry.name, path=path, attrib=entry.attrib))
            elif action == 'move':
                old_path_row = click.prompt('Enter the row you want to remove from the old paths', type=int)
                new_path_row = click.prompt('Enter the row you want to remove from the new paths', type=int)
                old_path = old_paths.pop(old_path_row)
                new_path = new_paths.pop(new_path_row)
                move_attrib.append(
                    MoveAction(old_name=entry.name,
                               old_path=old_path,
                               new_name=entry.name,
                               new_path=new_path,
                               attrib=entry.attrib))

        click.echo('Ambiguouity successfully resolved')
        ambiguous_attrib.remove(entry)

    conversion = {
        'from': from_version,
        'to': to_version,
        'tag': {
            'remove': remove_tags,
            'create': create_tags,
            'move': move_tags
        },
        'attrib': {
            'remove': remove_attrib,
            'create': create_attrib,
            'move': move_attrib
        }
    }

    filepath = FILE_DIRECTORY / f"conversion_{from_version.replace('.','')}_to_{to_version.replace('.','')}.json"

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(conversion, f, indent=2)
    return conversion


@inpxml.command('show-conversion')
@click.argument('from_version', type=str)
@click.argument('to_version', type=str)
def show_inp_conversion(from_version, to_version):
    """
    """
    try:
        conversion = load_conversion(from_version, to_version)
    except FileNotFoundError:
        echo.echo_critical(f'No conversion available between versions {from_version} to {to_version}')

    echo.echo_dictionary(conversion)
