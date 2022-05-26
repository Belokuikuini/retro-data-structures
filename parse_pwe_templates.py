import dataclasses
import logging
import re
import typing
from pathlib import Path
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import inflection

_game_id_to_file = {
    "Prime": "prime",
    "Echoes": "echoes",
    "Corruption": "corruption",
    "DKCReturns": "dkc_returns",
}


@dataclasses.dataclass(frozen=True)
class EnumDefinition:
    name: str
    values: typing.Dict[str, typing.Any]
    enum_base: str = "Enum"


_enums_by_game: typing.Dict[str, typing.List[EnumDefinition]] = {}


def _scrub_enum(string: str):
    s = re.sub(r'\W', '', string)  # remove non-word characters
    s = re.sub(r'^(?=\d)', '_', s)  # add leading underscore to strings starting with a number
    s = re.sub(r'^None$', '_None', s)  # add leading underscore to None
    s = s or "_EMPTY"  # add name for empty string keys
    return s


def create_enums_file(enums: typing.List[EnumDefinition]):
    code = '"""\nGenerated file.\n"""\nimport enum\n'

    for e in enums:
        code += f"\n\nclass {_scrub_enum(e.name)}(enum.{e.enum_base}):\n"
        for name, value in e.values.items():
            code += f"    {_scrub_enum(name)} = {value}\n"

    return code


def _prop_default_value(element: Element, game_id: str, path: Path) -> dict:
    default_value_types = {
        "Int": lambda el: int(el.text, 10) & 0xFFFFFFFF,
        "Float": lambda el: float(el.text),
        "Bool": lambda el: el.text == "true",
        "Short": lambda el: int(el.text, 10) & 0xFFFF,
        "Color": lambda el: {e.tag: float(e.text) for e in el},
        "Vector": lambda el: {e.tag: float(e.text) for e in el},
        "Flags": lambda el: int(el.text, 10) & 0xFFFFFFFF,
        "Choice": lambda el: int(el.text, 10) & 0xFFFFFFFF,
        "Enum": lambda el: int(el.text, 16) & 0xFFFFFFFF,
        "Sound": lambda el: int(el.text, 10) & 0xFFFFFFFF,
    }

    default_value = None
    has_default = False
    if (default_value_element := element.find("DefaultValue")) is not None:
        default_value = default_value_types.get(element.attrib["Type"], lambda el: el.text)(default_value_element)
        has_default = True
    return {"has_default": has_default, "default_value": default_value}


def _prop_struct(element: Element, game_id: str, path: Path) -> dict:
    return {
        "archetype": element.attrib.get("Archetype"),
        "properties": _parse_properties(element, game_id, path)["properties"]
    }


def _prop_asset(element: Element, game_id: str, path: Path) -> dict:
    type_filter = []
    if element.find("TypeFilter"):
        type_filter = [t.text for t in element.find("TypeFilter")]
    return {"type_filter": type_filter}


def _prop_array(element: Element, game_id: str, path: Path) -> dict:
    # print(ElementTree.tostring(element, encoding='utf8', method='xml'))
    item_archetype = None
    if (item_archetype_element := element.find("ItemArchetype")) is not None:
        item_archetype = _parse_single_property(item_archetype_element, game_id, path, include_id=False)
    # print(item_archetype)
    return {"item_archetype": item_archetype}


def _prop_choice(element: Element, game_id: str, path: Path) -> dict:
    _parse_choice(element, game_id, path)
    extras = {"archetype": element.attrib.get("Archetype")}
    extras.update(_prop_default_value(element, game_id, path))
    return extras


def _prop_flags(element: Element, game_id: str, path: Path) -> dict:
    extras = _prop_default_value(element, game_id, path)
    if (flags_element := element.find("Flags")) is not None:
        extras["flags"] = {
            element.attrib["Name"]: int(element.attrib["Mask"], 16)
            for element in flags_element.findall("Element")
        }

        name = None
        if element.find("Name") is not None:
            name = element.find("Name").text
        elif element.attrib.get("ID"):
            name = property_names.get(int(element.attrib.get("ID"), 16))

        _enums_by_game[game_id].append(EnumDefinition(name, extras["flags"], enum_base="IntFlag"))
        extras["flagset_name"] = name

    return extras


def _parse_single_property(element: Element, game_id: str, path: Path, include_id: bool = True) -> dict:
    parsed = {}
    if include_id:
        parsed.update({"id": int(element.attrib["ID"], 16)})
    name = element.find("Name")
    cook = element.find("CookPreference")
    parsed.update({
        "type": element.attrib["Type"],
        "name": name.text if name is not None and name.text is not None else "",
        "cook_preference": cook.text if cook is not None and cook.text is not None else "Always"
    })

    property_type_extras = {
        "Struct": _prop_struct,
        "Asset": _prop_asset,
        "Array": _prop_array,
        "Enum": _prop_choice,
        "Choice": _prop_choice,
        "Flags": _prop_flags,
    }

    parsed.update(property_type_extras.get(element.attrib["Type"], _prop_default_value)(element, game_id, path))

    return parsed


def _parse_properties(properties: Element, game_id: str, path: Path) -> dict:
    elements = []
    if (sub_properties := properties.find("SubProperties")) is not None:
        for element in sub_properties:
            element = typing.cast(Element, element)

            elements.append(_parse_single_property(element, game_id, path))

    return {
        "type": "Struct",
        "name": properties.find("Name").text if properties.find("Name") is not None else "",
        "atomic": properties.find("Atomic") is not None,
        "properties": elements,
    }


def _parse_choice(properties: Element, game_id: str, path: Path) -> dict:
    _type = properties.attrib.get("Type", "Choice")
    choices = {}

    if (values := properties.find("Values")) is not None:
        for element in values:
            element = typing.cast(Element, element)
            choices[element.attrib["Name"]] = int(element.attrib["ID"], 16)

        name = ""
        if properties.find("Name") is not None:
            name = properties.find("Name").text
        elif properties.attrib.get("ID"):
            name = property_names.get(int(properties.attrib.get("ID"), 16), path.stem + properties.attrib.get("ID"))
        else:
            return {
                "type": _type,
                "choices": choices,
            }

        _enums_by_game[game_id].append(EnumDefinition(name, choices))

    return {
        "type": _type,
    }


_parse_choice.unknowns = {}


def parse_script_object_file(path: Path, game_id: str) -> dict:
    t = ElementTree.parse(path)
    root = t.getroot()
    return _parse_properties(root.find("Properties"), game_id, path)


def parse_property_archetypes(path: Path, game_id: str) -> dict:
    t = ElementTree.parse(path)
    root = t.getroot()
    archetype = root.find("PropertyArchetype")
    _type = archetype.attrib["Type"]
    if _type == "Struct":
        return _parse_properties(archetype, game_id, path)
    elif _type == "Choice" or _type == "Enum":
        return _parse_choice(archetype, game_id, path)
    else:
        raise ValueError(f"Unknown Archetype format: {_type}")


property_names: typing.Dict[int, str] = {}


def read_property_names(map_path: Path):
    global property_names

    t = ElementTree.parse(map_path)
    root = t.getroot()
    m = root.find("PropertyMap")

    property_names = {
        int(item.find("Key").attrib["ID"], 16): item.find("Value").attrib["Name"]
        for item in typing.cast(typing.Iterable[Element], m)
    }

    return property_names


def get_paths(elements: typing.Iterable[Element]) -> typing.Dict[str, str]:
    return {
        item.find("Key").text: item.find("Value").attrib["Path"]
        for item in elements
    }


def get_key_map(elements: typing.Iterable[Element]) -> typing.Dict[str, str]:
    return {
        item.find("Key").text: item.find("Value").text
        for item in elements
    }


_to_snake_case_re = re.compile(r'(?<!^)(?=[A-Z])')
_invalid_chars_table = str.maketrans("", "", "()?")


def _filter_property_name(n: str) -> str:
    return inflection.underscore(n.replace(" ", "_").replace("#", "Number")).translate(_invalid_chars_table).lower()


def parse_game(templates_path: Path, game_xml: Path, game_id: str) -> dict:
    logging.info("Parsing templates for game %s: %s", game_id, game_xml)

    base_path = templates_path / game_xml.parent

    t = ElementTree.parse(templates_path / game_xml)
    root = t.getroot()

    states = get_key_map(root.find("States"))
    messages = get_key_map(root.find("Messages"))

    _enums_by_game[game_id] = [
        EnumDefinition(
            "States",
            {
                value: repr(key)
                for key, value in states.items()
            }
        ),
        EnumDefinition(
            "Messages",
            {
                value: repr(key)
                for key, value in messages.items()
            }
        ),
    ]

    script_objects_paths = {
        four_cc: path
        for four_cc, path in get_paths(root.find("ScriptObjects")).items()
    }
    script_objects = {
        four_cc: parse_script_object_file(base_path / path, game_id)
        for four_cc, path in script_objects_paths.items()
    }
    property_archetypes = {
        name: parse_property_archetypes(base_path / path, game_id)
        for name, path in get_paths(root.find("PropertyArchetypes")).items()
    }

    code_path = Path(__file__).parent.joinpath("retro_data_structures", "properties", game_id.lower())
    import_base = f"retro_data_structures.properties.{game_id.lower()}"

    def use_as_literal(k):
        return "default", repr(k)

    def convert_color(k):
        value = {"A": 0.0, **k}
        return "default_factory", "lambda: Color(r={R}, g={G}, b={B}, a={A})".format(**value)

    def convert_vector(k):
        return "default_factory", "lambda: Vector(x={X}, y={Y}, z={Z})".format(**k)

    _prop_type_to_python_type = {
        "Int": ("int", None, use_as_literal, None),
        "Float": ("float", None, use_as_literal, None),
        "Bool": ("bool", None, use_as_literal, None),
        "String": ("str", None, use_as_literal, ("default", repr(""))),
        "Color": ("Color", "core.Color", convert_color, None),
        "Vector": ("Vector", "core.Vector", convert_vector, None),
        "Short": ("int", None, use_as_literal, None),
        "Sound": ("AssetId", "core.AssetId", use_as_literal, None),
        "AnimationSet": ("AnimationParameters", "core.AnimationParameters", use_as_literal,
                         ("default_factory", "AnimationParameters")),
        "Spline": ("Spline", "core.Spline", use_as_literal, ("default_factory", "Spline")),
    }

    core_path = code_path.joinpath("core")
    core_path.mkdir(parents=True, exist_ok=True)

    core_path.joinpath("Color.py").write_text("""# Generated file
import dataclasses


@dataclasses.dataclass()
class Color:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 0.0
""")
    core_path.joinpath("Vector.py").write_text("""# Generated file
import dataclasses


@dataclasses.dataclass()
class Vector:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
""")
    core_path.joinpath("AssetId.py").write_text("AssetId = int\n")
    core_path.joinpath("AnimationParameters.py").write_text("""from .AssetId import AssetId


class AnimationParameters:
    ancs: AssetId
    character_index: int
    initial_anim: int
""")
    core_path.joinpath("Spline.py").write_text("""class Spline:
    data: bytes
""")

    known_enums: dict[str, EnumDefinition] = {_scrub_enum(e.name): e for e in _enums_by_game[game_id]}

    def get_prop_details(prop, meta: dict, needed_imports: dict[str, str]) -> tuple[str, bool, typing.Optional[str]]:
        prop_type = None
        need_enums = False
        comment = None

        if prop["type"] == "Struct":
            archetype_path: str = prop["archetype"].replace("_", ".")
            prop_type = archetype_path.split(".")[-1]
            needed_imports[f"{import_base}.archetypes.{archetype_path}"] = prop_type
            meta["default_factory"] = prop_type

        elif prop['type'] == 'Choice':
            default_value = prop["default_value"] if prop['has_default'] else 0
            enum_name = _scrub_enum(prop["archetype"] or property_names.get(prop["id"]) or "")
            if enum_name in known_enums:
                prop_type = f"enums.{enum_name}"
                need_enums = True

                for key, value in known_enums[enum_name].values.items():
                    if value == default_value:
                        meta["default"] = f"enums.{enum_name}.{_scrub_enum(key)}"
            else:
                comment = "Choice"
                prop_type = "int"
                meta["default"] = repr(default_value)

        elif prop["type"] == "Asset":
            prop_type = "AssetId"
            needed_imports[f"{import_base}.core.AssetId"] = "AssetId"
            meta["metadata"] = repr({"asset_types": prop["type_filter"]})
            meta["default"] = "0xFFFFFFFF"

        elif prop["type"] == "Flags":
            default_value = repr(prop["default_value"] if prop['has_default'] else 0)
            if "flagset_name" in prop:
                prop_type = "enums." + prop["flagset_name"]
                need_enums = True
                meta["default"] = f"{prop_type}({default_value})"
            else:
                prop_type = "int"
                comment = "Flagset"
                meta["default"] = default_value

        elif prop["type"] == "Array":
            inner_prop_type, need_enums, comment = get_prop_details(prop["item_archetype"], {}, needed_imports)
            prop_type = f"list[{inner_prop_type}]"
            meta["default_factory"] = "list"

        elif prop['type'] in _prop_type_to_python_type:
            prop_type, import_name, default_converter, default_default = _prop_type_to_python_type[prop['type']]
            if import_name is not None:
                needed_imports[f"{import_base}.{import_name}"] = prop_type

            if prop['has_default']:
                meta_key, meta_value = default_converter(prop["default_value"])
            else:
                meta_key, meta_value = default_default
            meta[meta_key] = meta_value

        return prop_type, need_enums, comment

    def parse_struct(name: str, struct, output_path: Path):
        if struct["type"] != "Struct":
            print("Ignoring {}. Is a {}".format(name, struct["type"]))
            return

        all_names = [
            _filter_property_name(prop["name"] or property_names.get(prop["id"]) or "unnamed")
            for prop in struct["properties"]
        ]

        needed_imports = {}
        need_enums = False

        class_name = name.split("_")[-1]
        class_path = name.replace("_", "/")

        class_code = f"@dataclasses.dataclass()\nclass {class_name}:\n"
        for prop, prop_name in zip(struct["properties"], all_names):
            if all_names.count(prop_name) > 1:
                prop_name += "_0x{:08x}".format(prop["id"])

            meta = {}
            prop_type, set_need_enums, comment = get_prop_details(prop, meta, needed_imports)
            need_enums = need_enums or set_need_enums

            if prop_type is None:
                prop_type = "object"
                extra_comment = f"{prop['type']} ; {prop['name']} ; {property_names.get(prop['id'])}"
                if comment is None:
                    comment = extra_comment
                else:
                    comment = f"{comment} ; {extra_comment}"
                print(comment)

            class_code += f"    {prop_name}: {prop_type}"
            if meta:
                class_code += " = dataclasses.field({})".format(
                    ", ".join(
                        f"{key}={value}"
                        for key, value in meta.items()
                    )
                )

            if comment is not None:
                class_code += f"  # {comment}"
            class_code += "\n"

        code_code = "# Generated File\n"
        code_code += "import dataclasses\n"
        if need_enums or needed_imports:
            code_code += "\n"

        if need_enums:
            code_code += f"import retro_data_structures.enums.{game_id.lower()} as enums\n"

        for import_path, code_import in sorted(needed_imports.items()):
            code_code += f"from {import_path} import {code_import}\n"

        code_code += "\n\n"
        code_code += class_code
        final_path = output_path.joinpath(class_path).with_suffix(".py")
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.write_text(code_code)

    getter_func = "def get_object(four_cc: str):\n"
    path = code_path.joinpath("objects")
    path.mkdir(parents=True, exist_ok=True)
    for object_fourcc, script_object in script_objects.items():
        stem = Path(script_objects_paths[object_fourcc]).stem
        parse_struct(stem, script_object, path)
        getter_func += f"    if four_cc == {repr(object_fourcc)}:\n"
        getter_func += f"        from .{stem} import {stem}\n"
        getter_func += f"        return {stem}\n"
    getter_func += '    raise ValueError(f"Unknown four_cc: {four_cc}")\n'
    path.joinpath("__init__.py").write_text(getter_func)

    print("> Creating archetypes")
    path = code_path.joinpath("archetypes")
    path.mkdir(parents=True, exist_ok=True)
    for archetype_name, archetype in property_archetypes.items():
        parse_struct(archetype_name, archetype, path)
    print("> Done.")

    return {
        "script_objects": script_objects,
        "property_archetypes": property_archetypes
    }


def parse_game_list(templates_path: Path) -> dict:
    t = ElementTree.parse(templates_path / "GameList.xml")
    root = t.getroot()
    return {
        game.attrib["ID"]: Path(game.find("GameTemplate").text)
        for game in root
    }


def parse(game_ids: typing.Optional[typing.Iterable[str]] = None) -> dict:
    base_dir = Path(__file__).parent
    templates_path = base_dir.joinpath("PrimeWorldEditor/templates")
    read_property_names(templates_path / "PropertyMap.xml")

    game_list = parse_game_list(templates_path)
    _parse_choice.unknowns = {game: 0 for game in game_list.keys()}

    return {
        _id: parse_game(templates_path, game_path, _id)
        for _id, game_path in game_list.items()
        if game_ids is None or _id in game_ids
    }


def persist_data(parse_result):
    logging.info("Persisting the parsed properties")
    base_dir = Path(__file__).parent

    # First write the enums
    for game_id in parse_result.keys():
        if game_id in _game_id_to_file:
            base_dir.joinpath(f"retro_data_structures/enums/{_game_id_to_file[game_id]}.py").write_text(
                create_enums_file(_enums_by_game[game_id])
            )

    # Now import these files, since they depend on the generated enum files
    from retro_data_structures.property_template import PropertyNames, GameTemplate

    encoded = PropertyNames.build(property_names)
    base_dir.joinpath(f"retro_data_structures/properties/property_names.pname").write_bytes(encoded)

    for game_id, template in parse_result.items():
        if game_id in _game_id_to_file:
            encoded = GameTemplate.build(template)
            base_dir.joinpath(f"retro_data_structures/properties/{game_id}.prop").write_bytes(encoded)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    persist_data(parse(["Echoes"]))
