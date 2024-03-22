import json
from pathlib import Path


class JsonSchemaHandler:
    def __init__(self, json_schema_name, namespace_sbe=None, namespace_enx=None, namespace_str=None, namespace_ext=None,
                 package=None, schema_id=None, version=None, semantic_version=None, description=None, byte_order=None,
                 suffix_name="_json_schema"):
        self.json_schema_name = json_schema_name.lower()
        self.file_name = f"{self.json_schema_name}{suffix_name.lower()}.json"
        self.file_path = Path(self.file_name)
        if namespace_sbe and namespace_enx and namespace_str and namespace_ext and package and schema_id and version and semantic_version and description and byte_order:
            self.create_new_file_json_schema(namespace_sbe, namespace_enx, namespace_str,
                                             namespace_ext, package, schema_id, version, semantic_version, description,
                                             byte_order)
        self.schema = self.load_schema()

    def load_schema(self):
        try:
            return json.loads(self.file_path.read_text(encoding='utf-8'))
        except FileNotFoundError:
            raise KeyError(f"JSON schema file '{self.file_path}' not found.")

    def create_new_file_json_schema(self, namespace_sbe, namespace_enx, namespace_str, namespace_ext,
                                    package, schema_id, version, semantic_version, description, byte_order,
                                    suffix_name="_json_schema"):
        file_name = f"{self.json_schema_name}{suffix_name.lower()}.json"
        file_path = Path(file_name)
        file_content = {
            self.json_schema_name: {
                "namespace_sbe": namespace_sbe,
                "namespace_enx": namespace_enx,
                "namespace_str": namespace_str,
                "namespace_ext": namespace_ext,
                "package": package,
                "schema_id": schema_id,
                "version": version,
                "semantic_version": semantic_version,
                "description": description,
                "byte_order": byte_order,
                "array_number_data_types": [],
                "array_string_data_types": [],
                "array_enum_data_types": [],
                "array_set_data_types": [],
                "array_composite_data_types": [],
                "array_document_messages": []
            }
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_content, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"An error occurred while writing to {file_path}: {e}")

    def add_document_message(self, message_name, template_id):
        if self.json_schema_name not in self.schema:
            raise KeyError(f"JSON schema '{self.json_schema_name}' not found.")
        if message_name in self.schema[self.json_schema_name]['array_document_messages']:
            print(f"Message \'{message_name}\' already exists in the JSON schema \'{self.json_schema_name}\'")
            return

        new_document_message = {
            "message_name": message_name,
            "template_id": template_id,
            "array_document_columns": [],
            "array_document_fields": [],
            "array_sbe_fields": [],
            "array_sbe_repeating_groups": []
        }

        self.schema[self.json_schema_name]['array_document_messages'].append(new_document_message)
        self.save_schema()

    def get_json_schema_field(self, name_field):
        if self.json_schema_name not in self.schema:
            raise KeyError(f"JSON schema '{self.json_schema_name}' not found.")

        return self.schema[self.json_schema_name][name_field]

    def get_schema_array_iterator(self, array_schema):
        if self.json_schema_name not in self.schema:
            raise KeyError(f"JSON schema '{self.json_schema_name}' not found.")

        return iter(self.schema[self.json_schema_name][array_schema])

    def find_document_message_in_json_schema(self, message_key):
        for message in self.get_schema_array_iterator('array_document_messages'):
            if message.get("message_name") == message_key:
                return message

        return None

    def add_document_column_to_message(self, message_key, column_name):
        message = self.find_document_message_in_json_schema(message_key)
        if message is None:
            raise KeyError(f"Message '{message_key}' not found in schema.")
        if column_name in message.get('array_document_columns', []):
            print(
                f"Document Column '{column_name}' already exists in the message '{message_key}' of the JSON schema '{self.json_schema_name}'")
            return
        message['array_document_columns'].append(column_name)
        self.save_schema()

    def get_message_array_iterator(self, message_key, array_in_document_message):
        message = self.find_document_message_in_json_schema(message_key)
        if message is None:
            raise KeyError(f"Message '{message_key}' not found in schema.")
        return iter(message.get(array_in_document_message, []))

    def add_document_field_to_message(self, message_key, json_document_field):
        message = self.find_document_message_in_json_schema(message_key)
        if message is None:
            raise KeyError(f"Message '{message_key}' not found in schema.")
        if json_document_field in message["array_document_fields"]:
            print(
                f"Document Field already exists in the message '{message_key}' of the JSON schema '{self.json_schema_name}'")
            return
        message['array_document_fields'].append(json_document_field)
        self.save_schema()

    def iterate_document_fields_of_document_messages(self, process_field_function):
        document_messages = self.get_schema_array_iterator("array_document_messages")
        for document_message in document_messages:
            document_fields = self.get_message_array_iterator(document_message["message_name"], "array_document_fields")
            for document_field in document_fields:
                process_field_function(document_message, document_field)

    def add_sbe_field_to_message(self, message_key, json_sbe_field):
        message = self.find_document_message_in_json_schema(message_key)
        if message is None:
            raise KeyError(f"Message '{message_key}' not found in schema.")
        if json_sbe_field in self.get_message_array_iterator('array_sbe_fields'):
            print(
                f"SBE Field already exists in the message '{message_key}' of the JSON schema '{self.json_schema_name}'")
            return
        message['array_sbe_fields'].append(json_sbe_field)
        self.save_schema()

    def iterate_sbe_fields_of_document_messages(self, process_field_function):
        document_messages = self.get_schema_array_iterator("array_document_messages")
        for document_message in document_messages:
            sbe_fields = self.get_message_array_iterator(document_message["message_name"], "array_sbe_fields")
            for sbe_field in sbe_fields:
                process_field_function(sbe_field)
            repeating_groups = self.get_message_array_iterator(document_message["message_name"],
                                                               "array_sbe_repeating_groups")
            for repeating_group in repeating_groups:
                sbe_fields = iter(repeating_group.get("items", []))
                for sbe_field in sbe_fields:
                    process_field_function(sbe_field)

    def add_repeating_group_to_message(self, message_key, group_name, group_id):
        message = self.find_document_message_in_json_schema(message_key)
        if message is None:
            raise KeyError(f"Message '{message_key}' not found in schema.")
        for repeating_group in self.get_message_array_iterator(message_key, "array_sbe_repeating_groups"):
            if repeating_group["group_id"] == group_id:
                print(
                    f"Repeating Group {group_id} already exists in the message '{message_key}' of the JSON schema '{self.json_schema_name}'")
                return

        new_repeating_group = {
            "group_id": group_id,
            "group_name": group_name,
            "items": []
        }

        message["array_sbe_repeating_groups"].append(new_repeating_group)
        self.save_schema()

    def add_composite_to_schema(self, name_composite, description_composite):

        for composite in self.get_schema_array_iterator("array_composite_data_types"):
            if composite["composite_name"] == name_composite:
                print(
                    f"Composite {name_composite} already exists in the JSON schema '{self.json_schema_name}'")
                return

        new_composite = {
            "name_composite": name_composite,
            "description_composite": description_composite,
            "items": []
        }

        self.schema[self.json_schema_name]["array_composite_data_types"].append(new_composite)
        self.save_schema()

    def add_sbe_field_to_repeating_group(self, message_key, id_num_in_group_field, json_sbe_field):
        message = self.find_document_message_in_json_schema(message_key)
        if message is None:
            raise KeyError(f"Message '{message_key}' not found in schema.")
        for repeating_group in self.get_message_array_iterator(message_key, "array_sbe_repeating_groups"):
            if repeating_group["group_id"] == id_num_in_group_field:
                repeating_group["items"].append(json_sbe_field)
                self.save_schema()
                break
        else:
            print(f"Repeating group {id_num_in_group_field} not found.")

    def add_sbe_field_to_composite(self, name_composite, json_sbe_field):
        for composite in self.get_schema_array_iterator("array_composite_data_types"):
            if composite["name_composite"] == name_composite:
                composite["items"].append(json_sbe_field)
                self.save_schema()
                break
        else:
            print(f"Composite {name_composite} not found.")

    def add_primitive_data_type(self, array_primitive_data_type, sbe_field):
        sbe_field["custom_type"] = ""
        if array_primitive_data_type == "array_string_data_types":
            if sbe_field["presence"] == "optional":
                sbe_field["custom_type"] = f"{sbe_field['data_type']}{sbe_field['length']}_{sbe_field['presence']}"
            else:
                sbe_field["custom_type"] = f"{sbe_field['data_type']}{sbe_field['length']}"
        elif array_primitive_data_type == "array_number_data_types":
            sbe_field["custom_type"] = f"{sbe_field['data_type']}_t"

        if self.is_primitive_data_type_exists_in_json_schema(array_primitive_data_type, sbe_field["data_type"],
                                                             sbe_field["length"]):
            print(
                f"Data Type \'{sbe_field['data_type']}\' already exists in the JSON schema \'{self.json_schema_name}\'")
            return

        new_primitive_data_type = {
            "name_type": sbe_field["custom_type"],
            "data_type": sbe_field["data_type"],
            "length": sbe_field["length"],
            "presence": sbe_field["presence"]
        }

        self.schema[self.json_schema_name][array_primitive_data_type].append(new_primitive_data_type)
        self.save_schema()

    def get_primitive_data_type_iterator(self, array_primitive_data_type):
        return self.get_schema_array_iterator(array_primitive_data_type)

    def is_primitive_data_type_exists_in_json_schema(self, array_primitive_data_type, data_type_to_find, length):
        for data_type in self.get_schema_array_iterator(array_primitive_data_type):
            if data_type.get("data_type") == data_type_to_find and data_type.get("length") == length:
                return True

        return False

    def add_custom_data_type(self, array_custom_data_type, encoding_type, data_type, structure):
        if self.is_custom_data_type_exists_in_json_schema(array_custom_data_type, data_type, structure):
            print(f"Data Type \'{data_type}\' already exists in the JSON schema \'{self.json_schema_name}\'")
            return

        new_custom_data_type = {
            "encoding_type": encoding_type,
            "data_type": data_type,
            "structure": structure
        }

        self.schema[self.json_schema_name][array_custom_data_type].append(new_custom_data_type)
        self.save_schema()

    def get_custom_data_type_iterator(self, array_custom_data_type):
        return self.get_schema_array_iterator(array_custom_data_type)

    def is_custom_data_type_exists_in_json_schema(self, array_custom_data_type, data_type_to_find, structure):
        for data_type in self.get_schema_array_iterator(array_custom_data_type):
            if data_type.get("data_type") == data_type_to_find:
                data_type["structure"] = {**structure, **data_type["structure"]}
                return True

        return False

    def save_schema(self):
        self.file_path.write_text(json.dumps(self.schema, indent=4, ensure_ascii=False), encoding='utf-8')