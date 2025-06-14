import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Type, Any
import cstruct
from collections import OrderedDict


@dataclass
class StructInfo:
    """Metadata about a C structure"""
    name: str
    fields: OrderedDict
    size: int
    is_bitfield: bool = False


class CStructParser:
    """A parser for C structure definitions using cstruct"""
    
    def __init__(self, path_or_string: str, endian: str = 'little'):
        """
        Initialize CStructParser
        Args:
            path_or_string: Either a path to directory containing header files,
                          or a string containing C struct definitions
            endian: Endianness of the data, either 'little' or 'big'
        """
        if endian not in ('little', 'big'):
            raise ValueError("Endian must be either 'little' or 'big'")
        
        self.endian = endian
        self.structs = {}
        self.struct_info: Dict[str, StructInfo] = {}
        
        # Process input
        if os.path.isfile(path_or_string):
            with open( path_or_string, 'r') as f:
                self.parse_header(f.read())
        else:
            self.parse_header(path_or_string)

    def remove_comments(self, content: str) -> str:
        """Remove C-style comments and includes from the content."""
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove single-line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # Remove includes
        content = re.sub(r'#include\s+[<"].*[>"].*$', '', content, flags=re.MULTILINE)
        return content

    def parse_header(self, content: str) -> None:
        """Parse a header file content string to extract and create structure definitions."""
        cleaned_content = self.remove_comments(content)

        # First pass: collect all struct definitions
        struct_defs = {}
        struct_pattern = r'typedef\s+struct[^{]*{([^}]+)}\s*(\w+)\s*;'
        matches = re.finditer(struct_pattern, cleaned_content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            struct_body, struct_name = match.groups()
            struct_defs[struct_name] = struct_body.strip()

        # Second pass: build content with proper struct references
        build_content = ""
        for struct_name, struct_body in struct_defs.items():
            # Process array fields first
            modified_body = self._process_array_fields(struct_body)
            
            # Check and add 'struct' keyword for references to other structures
            for other_struct in struct_defs.keys():
                # Look for struct references that aren't already marked with 'struct'
                # and aren't part of the type definition ending
                modified_body = re.sub(
                    fr'\b{other_struct}\b(?!\s*}})',
                    f'struct {other_struct}',
                    modified_body
                )
            
            # Normalize the structure body indentation
            normalized_body = self._normalize_struct_body(modified_body)
            
            # Add the modified struct definition to build content
            build_content += f"struct {struct_name} {{\n\t{normalized_body}\n}};\n\n"

        print(build_content)

        # Create new structure class using parse
        self.struct_class = cstruct.CStruct.parse(
            build_content,
            __byte_order__='<' if self.endian == 'little' else '>'
        )

           
    def unpack_data(self, data: bytes, root_struct: str) -> dict:
        """Unpack binary data according to the parsed structure."""
        if root_struct not in self.structs:
            raise ValueError(f"Unknown structure: {root_struct}")
        
        struct_class = self.struct_class.get_type(root_struct)
        struct_class.unpack(data)
        return self._struct_to_dict(struct_class)

    def pack_data(self, data_dict: dict, root_struct: str) -> bytes:
        """Pack dictionary data according to the parsed structure."""
        if root_struct not in self.structs:
            raise ValueError(f"Unknown structure: {root_struct}")
        
        struct_class = self.struct_class.get_type(root_struct)
        self._dict_to_struct(data_dict, struct_class)
        return struct_class.pack()

    def _struct_to_dict(self, struct) -> dict:
        """Convert a cstruct instance to a dictionary."""
        result = {}
        for name, _ in struct._fields_:
            value = getattr(struct, name)
            if isinstance(value, tuple):
                # Handle arrays
                result[name] = list(value)
            elif isinstance(value, cstruct.CStruct):
                # Handle nested structures
                result[name] = self._struct_to_dict(value)
            else:
                result[name] = value
        return result

    def _dict_to_struct(self, data: dict, struct) -> None:
        """Update a cstruct instance from a dictionary."""
        for name, field_type in struct._fields_:
            if name not in data:
                continue
            
            value = data[name]
            if isinstance(value, (list, tuple)):
                # Handle arrays
                setattr(struct, name, tuple(value))
            elif isinstance(value, dict):
                # Handle nested structures
                sub_struct = getattr(struct, name)
                self._dict_to_struct(value, sub_struct)
            else:
                setattr(struct, name, value)

    def print_struct_tree(self, root_struct: str, indent: str = "", is_last: bool = True) -> None:
        """Print the structure tree starting from the given root structure."""
        try:
            print(f"Printing structure tree for: {root_struct}")
            struct_class = self.struct_class.get_type(root_struct)
        except AttributeError:
            raise ValueError(f"Unknown structure: {root_struct}")

        # Get size of the struct
        struct_size = struct_class.size

        # Print current struct with proper branch
        prefix = "└── " if is_last else "├── "
        print(f"{indent}{prefix}{root_struct} ({struct_size} bytes)")

        # Prepare indent for children
        child_indent = indent + ("    " if is_last else "│   ")

        # Get all fields from the struct class
        fields = struct_class._fields_
        total_fields = len(fields)

        # Iterate through fields
        for idx, (field_name, field_type) in enumerate(fields):
            is_last_field = idx == total_fields - 1

            # Check if field is an array
            if hasattr(field_type, '_length_'):
                array_size = field_type._length_
                base_type = field_type._type_.__name__
                print(f"{child_indent}{'└── ' if is_last_field else '├── '}{field_name}[{array_size}]: {base_type}")
                
            # Check if field is a nested struct
            elif hasattr(field_type, '_fields_'):
                struct_name = field_type.__name__
                # Recursively print nested struct
                self.print_struct_tree(struct_name, child_indent, is_last_field)
                
            else:
                # Basic type field
                type_name = field_type.__name__
                print(f"{child_indent}{'└── ' if is_last_field else '├── '}{field_name}: {type_name}")

    def get_struct_size(self, struct_name: str) -> int:
        """Get the total size of a structure in bytes."""
        if struct_name not in self.struct_info:
            raise ValueError(f"Unknown structure: {struct_name}")
        return self.struct_info[struct_name].size

    def _process_array_fields(self, struct_body: str) -> str:
        """Process array field declarations to ensure proper C-style syntax."""
        # No processing needed - we want to keep the original C-style array syntax
        # where brackets come after the field name
        return struct_body

    def _normalize_struct_body(self, struct_body: str) -> str:
        """Normalize structure body by removing extra spaces and adding consistent indentation."""
        # Split into lines and remove extra spaces/tabs
        lines = [line.strip() for line in struct_body.split('\n')]
        # Filter out empty lines
        lines = [line for line in lines if line]
        # Add one tab indentation to each line
        return '\n\t'.join(lines)


if __name__ == "__main__":
    # Example 1: Parse structures from a directory
    print("Example 1: Parsing from directory")
    parser = CStructParser("test/test_general.h", endian='little')

    parser.print_struct_tree("DeviceData")
    print(f"\nTotal size: {parser.get_struct_size('DeviceData')} bytes")
    
    # Create and unpack test data
    test_data = bytes([0] * parser.get_struct_size('DeviceData'))
    result = parser.unpack_data(test_data, 'DeviceData')
    print("\nUnpacked data:")
    print(result)

