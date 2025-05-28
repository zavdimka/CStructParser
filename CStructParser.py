from dataclasses import dataclass
from typing import Dict, List, Optional
import re
import os
import struct


@dataclass
class StructField:
    name: str
    type_name: str  # Store original type name
    format: Optional[str]
    size: Optional[int]
    is_struct: bool
    subfields: Dict[str, 'StructField'] = None


class CStructParser:
    def __init__(self, path_to_sources_dir: str):
        self.struct_formats = {
            # Standard C types
            'char': ('c', 1),
            'signed char': ('b', 1),
            'unsigned char': ('B', 1),
            'short': ('h', 2),
            'unsigned short': ('H', 2),
            'int': ('i', 4),
            'unsigned int': ('I', 4),
            'long': ('l', 4),
            'unsigned long': ('L', 4),
            'long long': ('q', 8),
            'unsigned long long': ('Q', 8),
            'float': ('f', 4),
            'double': ('d', 8),
            'long double': ('d', 8),  # Python doesn't have a specific format for long double
            
            # stdint.h fixed-width types
            'int8_t': ('b', 1),
            'uint8_t': ('B', 1),
            'int16_t': ('h', 2),
            'uint16_t': ('H', 2),
            'int32_t': ('i', 4),
            'uint32_t': ('I', 4),
            'int64_t': ('q', 8),
            'uint64_t': ('Q', 8),
            
            # stdint.h minimum-width types
            'int_least8_t': ('b', 1),
            'uint_least8_t': ('B', 1),
            'int_least16_t': ('h', 2),
            'uint_least16_t': ('H', 2),
            'int_least32_t': ('i', 4),
            'uint_least32_t': ('I', 4),
            'int_least64_t': ('q', 8),
            'uint_least64_t': ('Q', 8),
            
            # stdint.h fast types
            'int_fast8_t': ('b', 1),
            'uint_fast8_t': ('B', 1),
            'int_fast16_t': ('h', 2),
            'uint_fast16_t': ('H', 2),
            'int_fast32_t': ('i', 4),
            'uint_fast32_t': ('I', 4),
            'int_fast64_t': ('q', 8),
            'uint_fast64_t': ('Q', 8),
            
            # stdint.h pointer types
            'intptr_t': ('q', 8),    # Assumes 64-bit system
            'uintptr_t': ('Q', 8),   # Assumes 64-bit system
            
            # stdint.h maximum-width types
            'intmax_t': ('q', 8),
            'uintmax_t': ('Q', 8)
        }
        self.struct_sizes = {}
        self.struct_fields = {}
        self.parsed_files = set()

        # First phase: parse all files
        for file in os.listdir(path_to_sources_dir):
            if file.endswith('.h'):
                filepath = os.path.join(path_to_sources_dir, file)
                self.parse_header_file(filepath)
            # Second phase: calculate all sizes
            try:
                self.calculate_sizes()
            except RuntimeError as e:
                print(f"Error calculating sizes: {e}")
                raise
        

    def parse_header_file(self, filepath: str):
        if filepath in self.parsed_files:
            return
        self.parsed_files.add(filepath)

        with open(filepath, 'r') as f:
            content = f.read()

        # Find and process includes first
        include_pattern = r'#include\s+"([^"]+)"'
        includes = re.finditer(include_pattern, content)
        dir_path = os.path.dirname(filepath)
        
        for include in includes:
            include_file = include.group(1)
            include_path = os.path.join(dir_path, include_file)
            if os.path.exists(include_path):
                self.parse_header_file(include_path)

        # Parse struct definitions
        struct_pattern = r'typedef\s+struct[^{]*{([^}]+)}\s*(\w+)\s*;'
        structs = re.finditer(struct_pattern, content)

        for struct_match in structs:
            struct_body = struct_match.group(1)
            struct_name = struct_match.group(2)
            
            fields = {}
            for line in struct_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('//'):
                    field_match = re.match(r'(\w+)\s+(\w+);', line)
                    if field_match:
                        type_name, field_name = field_match.groups()
                        if type_name in self.struct_formats:
                            format_char, size = self.struct_formats[type_name]
                            fields[field_name] = StructField(
                                name=field_name,
                                type_name=type_name,
                                format=format_char,
                                size=size,
                                is_struct=False
                            )
                        else:
                            fields[field_name] = StructField(
                                name=field_name,
                                type_name=type_name,
                                format=None,
                                size=None,
                                is_struct=True,
                                subfields=None
                            )

            self.struct_fields[struct_name] = fields


    def calculate_sizes(self):
        """Calculate sizes and set up subfields for all structures after all files are parsed"""
        def process_struct(struct_name: str, visited: set) -> tuple[int, dict]:
            if struct_name in visited:
                raise RuntimeError(f"Circular dependency detected for struct {struct_name}")
            
            if struct_name not in self.struct_fields:
                raise RuntimeError(f"Unknown structure type: {struct_name}")
                
            visited.add(struct_name)
            total_size = 0
            fields = self.struct_fields[struct_name]
            
            for field in fields.values():
                if field.is_struct:
                    if field.type_name not in self.struct_fields:
                        raise RuntimeError(f"Unknown structure type: {field.type_name}")
                    # Recursively process substructure
                    size, subfields = process_struct(field.type_name, visited.copy())
                    field.size = size
                    field.subfields = subfields
                total_size += field.size
                
            self.struct_sizes[struct_name] = total_size
            return total_size, fields

        # Process all structures
        for struct_name in list(self.struct_fields.keys()):
            if struct_name not in self.struct_sizes:
                self.struct_sizes[struct_name], self.struct_fields[struct_name] = process_struct(struct_name, set())


    def unpack_data(self, data: bytes, root_struct: str) -> dict:
        """Unpack binary data according to the parsed structure"""
        def unpack_struct(data: bytes, offset: int, fields: Dict[str, StructField]) -> tuple[dict, int]:
            result = {}
            current_offset = offset
            print(f"Unpacking struct {fields} at offset {current_offset}")
            
            for field_name, field in fields.items():
                if field.is_struct:
                    sub_result, new_offset = unpack_struct(data, current_offset, field.subfields)
                    result[field_name] = sub_result
                    current_offset = new_offset
                else:
                    value = struct.unpack_from(field.format, data, current_offset)[0]
                    result[field_name] = value
                    current_offset += field.size
                    
            return result, current_offset

        result, _ = unpack_struct(data, 0, self.struct_fields[root_struct])
        return result

if __name__ == "__main__":
    # Example usage
    parser = CStructParser("../MK/Inc")
    t = parser.unpack_data(bytearray(224), 'T_TARGET')
    print(t)
