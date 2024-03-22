from lxml import etree
from pathlib import Path

from json_schema_handler import JsonSchemaHandler


class XmlSbeSchemaHandler:
    def __init__(self, schema_name, suffix_name="_sbe_xml_schema"):
        self.file_name = f"{schema_name.lower()}{suffix_name.lower()}.xml"
        self.file_path = Path(self.file_name)
        self.namespaces = {}
        self.json_handler = JsonSchemaHandler(schema_name)
        self.generate_sbe_xml_header(schema_name)

    def save_xml_document(self):
        tree = etree.ElementTree(self.sbe_message_schema_tag)
        tree.write(str(self.file_path), pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def append_to_sbe_types_section(self, new_element_xml):
        self.types_tag.append(new_element_xml)
        self.save_xml_document()

    def append_to_sbe_schema_root(self, new_element_xml):
        self.sbe_message_schema_tag.append(new_element_xml)
        self.save_xml_document()

    def generate_sbe_xml_header(self, json_schema_name):
        json_handler = JsonSchemaHandler(json_schema_name)

        if not self.namespaces:
            self.namespaces = {
                'sbe': json_handler.get_json_schema_field("namespace_sbe"),
                'enx': json_handler.get_json_schema_field("namespace_enx"),
                'str': json_handler.get_json_schema_field("namespace_str"),
                'ext': json_handler.get_json_schema_field("namespace_ext")
            }

        messageSchema = etree.Element("{%s}messageSchema" % self.namespaces['sbe'], nsmap=self.namespaces, attrib={
            'package': json_handler.get_json_schema_field("package"),
            'id': json_handler.get_json_schema_field("schema_id"),
            'version': json_handler.get_json_schema_field("version"),
            'semanticVersion': json_handler.get_json_schema_field("semantic_version"),
            'description': json_handler.get_json_schema_field("description"),
            'byteOrder': json_handler.get_json_schema_field("byte_order")
        })

        tree = etree.ElementTree(messageSchema)
        self.sbe_message_schema_tag = tree.getroot()
        self.types_tag = etree.SubElement(
            self.sbe_message_schema_tag,
            "types"
        )
        self.append_to_sbe_schema_root(self.types_tag)
        return etree.tostring(self.sbe_message_schema_tag, xml_declaration=True, encoding="UTF-8",
                              pretty_print=True).decode("UTF-8")

    def generate_sbe_enum_definition(self, encoding_type, name_enum, enum_structure):

        enum_element = etree.SubElement(
            self.types_tag,
            'enum',
            encodingType=encoding_type,
            name=name_enum
        )

        for name, value in enum_structure.items():
            valid_value_element = etree.SubElement(
                enum_element,
                'validValue',
                name=name
            )
            valid_value_element.text = str(value)

        self.append_to_sbe_types_section(enum_element)
        return etree.tostring(enum_element, pretty_print=True).decode()

    def generate_sbe_set_definition(self, encoding_type, name_set, set_structure):

        set_element = etree.SubElement(
            self.types_tag,
            'set',
            encodingType=encoding_type,
            name=name_set
        )

        for name, value in set_structure.items():
            valid_value_element = etree.SubElement(
                set_element,
                'choice',
                name=name
            )
            valid_value_element.text = str(value)

        self.append_to_sbe_types_section(set_element)
        return etree.tostring(set_element, pretty_print=True).decode()

    def generate_sbe_number_definition(self, name_type, primitive_type, presence):

        type_values = {
            "int8": ("-128", "-127", "127"),
            "uint8": ("255", "0", "254"),
            "int16": ("-32768", "-32767", "32767"),
            "uint16": ("65535", "0", "65534"),
            "int32": ("-2147483648", "-2147483647", "2147483647"),
            "uint32": ("4294967295", "0", "4294967294"),
            "int64": ("-9223372036854775808", "-9223372036854775807", "9223372036854775807"),
            "uint64": ("18446744073709551615", "0", "18446744073709551614"),
        }

        if primitive_type not in type_values:
            raise ValueError(f"Unsupported primitive type: {primitive_type}")

        null_value, min_value, max_value = type_values[primitive_type]

        type_element = etree.Element(
            'type',
            name=name_type,
            primitiveType=primitive_type,
            nullValue=null_value,
            presence=presence,
            minValue=min_value,
            maxValue=max_value
        )

        self.append_to_sbe_types_section(type_element)
        return etree.tostring(type_element, pretty_print=True).decode()

    def generate_sbe_string_definition(self, name_type, primitive_type, length, presence):

        type_element = etree.SubElement(
            self.types_tag,
            'type',
            name=name_type,
            length=str(length),
            primitiveType=primitive_type
        )

        if presence == "optional":
            type_element.set('presence', presence)

        self.append_to_sbe_types_section(type_element)
        return etree.tostring(type_element, pretty_print=True).decode()

    def generate_sbe_composite(self, composite):

        composite_element = etree.SubElement(
            self.types_tag,
            "composite",
            name=composite["name"],
            description=composite["description"]
        )

        for element in composite["elements"]:
            type = etree.SubElement(
                composite_element,
                "type"
            )
            for key, value in element.items():
                type.set(key, value)

        self.append_to_sbe_types_section(composite_element)
        return etree.tostring(composite_element, pretty_print=True, encoding="UTF-8").decode("utf-8")

    def generate_sbe_default_composites(self):

        composites = [
            {
                "name": "messageHeader",
                "description": "Message identifiers and length of message root",
                "elements": [
                    {"name": "blockLength", "primitiveType": "uint16"},
                    {"name": "templateId", "primitiveType": "uint16"},
                    {"name": "schemaId", "primitiveType": "uint16"},
                    {"name": "version", "primitiveType": "uint16"},
                ]
            },
            {
                "name": "groupSizeEncoding",
                "description": "Repeating group dimensions",
                "elements": [
                    {"name": "blockLength", "primitiveType": "uint8"},
                    {"name": "numInGroup", "primitiveType": "uint8", "semanticType": "NumInGroup"},
                ]
            },
            {
                "name": "groupSizeEncoding16",
                "description": "Repeating group dimensions",
                "elements": [
                    {"name": "blockLength", "primitiveType": "uint16"},
                    {"name": "numInGroup", "primitiveType": "uint8", "semanticType": "NumInGroup"},
                ]
            },
        ]

        for composite in composites:
            self.generate_sbe_composite(composite)

    def generate_sbe_message_xml(self, message_name, template_id, iterator_sbe_fields,
                                 iterator_sbe_repeating_groups):
        if not self.namespaces:
            raise ValueError("Namespaces must be registered before generating XML.")

        nsmap = {'sbe': self.namespaces['sbe']}
        message_element = etree.SubElement(
            self.sbe_message_schema_tag,
            "{%s}message" % self.namespaces['sbe'],
            name=message_name,
            id=str(template_id),
            nsmap=nsmap
        )

        etree.SubElement(
            message_element,
            'field',
            id=str(20007),
            name="FixHeader",
            type="fixHeader"
        )

        for sbe_field in iterator_sbe_fields:
            field = etree.SubElement(
                message_element,
                'field',
                id=str(sbe_field["field_id"]),
                name=sbe_field["field_name"],
                type=sbe_field.get("custom_type", sbe_field["data_type"])
            )

            if sbe_field["presence"] == "optional":
                field.set('presence', sbe_field["presence"])

        for sbe_repeating_group in iterator_sbe_repeating_groups:
            group = etree.SubElement(
                message_element,
                "group",
                dimensionType="groupSizeEncoding",
                name=sbe_repeating_group["group_name"],
                id=sbe_repeating_group["group_id"]
            )

            for field_info in iter(sbe_repeating_group.get("items", [])):
                etree.SubElement(
                    group,
                    "field",
                    name=field_info["field_name"],
                    id=str(field_info["field_id"]),
                    type=field_info.get("custom_type", field_info["data_type"])
                )

        self.append_to_sbe_schema_root(message_element)
        return etree.tostring(message_element, pretty_print=True, encoding='UTF-8').decode()
