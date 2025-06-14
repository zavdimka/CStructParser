from dataclasses import dataclass
from typing import Dict, List, Optional
import re
import os
import struct
from ctype_format import CTypeFormat


@dataclass
class StructField:
    name: str
    type_name: str  # Store original type name
    format: Optional[str]
    size: Optional[int]
    is_struct: bool
    array_size: Optional[int] = None  # Size of array, None if not an array
    subfields: Dict[str, 'StructField'] = None
    bit_size: Optional[int] = None  # Size in bits for bit fields
    bit_offset: Optional[int] = None  # Offset in bits within the current byte


class CStructParser:
    def __init__(self, path_or_string: str, endian: str = 'little', debug: bool = False):
        """
        Initialize CStructParser
        Args:
            path_or_string: Either a path to directory containing header files,
                          or a string containing C struct definitions
            endian: Endianness of the data, either 'little' or 'big'
            debug: Enable debug output
        """
        if endian not in ('little', 'big'):
            raise ValueError("Endian must be either 'little' or 'big'")
            
        self.endian_prefix = '<' if endian == 'little' else '>'
        self.struct_formats = CTypeFormat.get_all_formats()
        self.struct_sizes = {}
        self.struct_fields = {}
        self.debug = debug

        # Check if the input is a directory path or content string
        if os.path.isdir(path_or_string):
            # Parse all header files in the directory
            for file in os.listdir(path_or_string):
                if file.endswith('.h'):
                    filepath = os.path.join(path_or_string, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    self.parse_header_file_as_string(content)
        else:
            # Treat input as direct content string
            self.parse_header_file_as_string(path_or_string)

        # Calculate sizes for all parsed structures
        try:
            self.calculate_sizes()
        except RuntimeError as e:
            print(f"Error calculating sizes: {e}")
            raise
        

    def _remove_comments(self, content: str) -> str:
        """Remove C-style comments from the content."""
        # Remove multi-line comments first
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove single-line comments
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        return content

    def parse_header_file_as_string(self, content: str)-> None: 
        """Parse a header file content string to extract structure definitions."""
        cleaned_content = self._remove_comments(content)
        struct_pattern = r'typedef\s+struct[^{]*{([^}]+)}\s*(\w+)\s*;'
        structs = re.finditer(struct_pattern, cleaned_content)

        for struct_match in structs:
            struct_body = struct_match.group(1)
            struct_name = struct_match.group(2)
            
            fields = {}
            current_byte_offset = 0
            current_bit_offset = 0
            current_base_type = None
            current_base_size = 0
            
            for line in struct_body.split('\n'):
                line = line.strip()
                if line:
                    # Try to match bit field first
                    bit_field_match = re.match(r'((?:\w+\s+)*\w+)\s+(\w+)\s*:\s*(\d+)\s*;', line)
                    if bit_field_match:
                        type_name, field_name, bit_size = bit_field_match.groups()
                        type_name = type_name.strip()  # Clean up any extra whitespace
                        bit_size = int(bit_size)
                        
                        self._debug_print(f"Processing bit field: {field_name} of type {type_name} with size {bit_size} bits")
                        self._debug_print(f"Current state: base_type={current_base_type}, bit_offset={current_bit_offset}")
                        
                        if type_name not in self.struct_formats:
                            raise ValueError(f"Unsupported bit field type: {type_name}")
                            
                        format_char, base_size = self.struct_formats[type_name]
                        self._debug_print(f"Base type size: {base_size} bytes")
                        
                        # Check if we need to start a new base type
                        if current_bit_offset + bit_size > base_size * 8:
                            self._debug_print("Starting new base type storage unit (exceeded bits)")
                            current_byte_offset += current_base_size if current_base_size > 0 else 0
                            current_bit_offset = 0
                            current_base_type = type_name
                            current_base_size = base_size
                        elif current_base_type is None:
                            self._debug_print("Starting first base type storage unit")
                            current_base_type = type_name
                            current_base_size = base_size
                            
                        fields[field_name] = StructField(
                            name=field_name,
                            type_name=type_name,
                            format=format_char,
                            size=base_size,
                            is_struct=False,
                            array_size=None,
                            bit_size=bit_size,
                            bit_offset=current_bit_offset
                        )
                        self._debug_print(f"Created bit field {field_name} with offset {current_bit_offset}")
                        current_bit_offset += bit_size
                        self._debug_print(f"Updated bit offset to {current_bit_offset}")
                        
                    else:
                        # Reset bit field tracking when encountering non-bit field
                        if current_bit_offset > 0:
                            current_byte_offset += current_base_size
                            current_bit_offset = 0
                            current_base_type = None
                            current_base_size = 0
                        
                        # Handle regular fields
                        field_match = re.match(r'((?:\w+\s+)*\w+)\s+(\w+)(?:\[(\d+)\])*;', line)
                        if field_match:
                            type_name, field_name = field_match.groups()[:2]
                            type_name = type_name.strip()  # Clean up any extra whitespace
                            
                            # Find all array dimensions using findall
                            dimensions = re.findall(r'\[(\d+)\]', line)
                            # Calculate total array size as product of all dimensions
                            array_size = 1
                            if dimensions:
                                for dim in dimensions:
                                    array_size *= int(dim)
                            else:
                                array_size = None
                        
                            if type_name in self.struct_formats:
                                format_char, size = self.struct_formats[type_name]
                                # Add endianness prefix for multi-byte types, but not for chars and single bytes
                                if size > 1 and format_char not in ('c', 'b', 'B'):
                                    format_char = format_char
                                fields[field_name] = StructField(
                                    name=field_name,
                                    type_name=type_name,
                                    format=format_char,
                                    size=size * (array_size if array_size else 1),
                                    is_struct=False,
                                    array_size=array_size,
                                    bit_size=None,
                                    bit_offset=None
                                )
                            else:
                                fields[field_name] = StructField(
                                    name=field_name,
                                    type_name=type_name,
                                    format=None,
                                    size=None,
                                    is_struct=True,
                                    array_size=array_size,
                                    subfields=None
                                )

            self.struct_fields[struct_name] = fields


    def calculate_sizes(self) -> None:
        """Calculate sizes and set up subfields for all structures after all files are parsed"""
        def process_struct(struct_name: str, visited: set) -> tuple[int, dict]:
            if struct_name in visited:
                raise RuntimeError(f"Circular dependency detected for struct {struct_name}")
            
            if struct_name not in self.struct_fields:
                raise RuntimeError(f"Unknown structure type: {struct_name}")
                
            visited.add(struct_name)
            total_size = 0
            fields = self.struct_fields[struct_name]
            
            current_base_type = None  # Track base type for bit fields
            current_bits_used = 0     # Track bits used in current base type
            total_size = 0
            
            for field in fields.values():
                if field.bit_size is not None:
                    # Handle bit fields
                    if current_base_type is None or current_bits_used + field.bit_size > self._get_type_size(field.type_name) * 8:
                        # If we're starting a new base type or would exceed current one
                        if current_base_type is not None:
                            total_size += self._get_type_size(current_base_type)
                        current_base_type = field.type_name
                        current_bits_used = field.bit_size
                    else:
                        current_bits_used += field.bit_size
                else:
                    # Regular field - first complete any pending bit field storage
                    if current_base_type is not None:
                        total_size += self._get_type_size(current_base_type)
                        current_base_type = None
                        current_bits_used = 0

                    if field.array_size:
                        if field.is_struct:
                            # Array of structures
                            struct_size, subfields = process_struct(field.type_name, visited.copy())
                            field.size = struct_size * field.array_size
                            field.subfields = subfields
                        else:
                            # Array of basic types
                            field.size = self._get_type_size(field.type_name) * field.array_size
                    else:
                        if field.is_struct:
                            # Single structure
                            struct_size, subfields = process_struct(field.type_name, visited.copy())
                            field.size = struct_size
                            field.subfields = subfields
                        else:
                            # Single basic type
                            field.size = self._get_type_size(field.type_name)
                    
                    total_size += field.size
            
            # Add size of last bit field group if exists
            if current_base_type is not None:
                total_size += self._get_type_size(current_base_type)
                
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
            current_bit_field_value = None
            current_base_type = None
            
            for field_name, field in fields.items():
                if field.bit_size is not None:
                    # Handle bit fields
                    if field.bit_offset == 0:
                        # Start of a new bit field group
                        format_char = self._get_struct_format(field.type_name)
                        current_bit_field_value = struct.unpack_from(f"{self.endian_prefix}{format_char}", data, current_offset)[0]
                        current_base_type = field.type_name
                    
                    # Extract bits from the current bit field value
                    mask = (1 << field.bit_size) - 1
                    value = (current_bit_field_value >> field.bit_offset) & mask
                    result[field_name] = value
                    
                    # Move to next byte group if this was the last bit field in current group
                    is_last_field = field is list(fields.values())[-1]
                    next_field = None if is_last_field else list(fields.values())[list(fields.values()).index(field) + 1]
                    if is_last_field or next_field.bit_size is None or next_field.bit_offset == 0:
                        current_offset += self._get_type_size(current_base_type)
                        current_bit_field_value = None
                else:
                    # Handle regular fields
                    if field.array_size:
                        array_size = field.array_size
                        if field.is_struct:
                            # Handle array of structures
                            array_values = []
                            for _ in range(array_size):
                                sub_result, sub_offset = unpack_struct(data, current_offset, self.struct_fields[field.type_name])
                                array_values.append(sub_result)
                                current_offset = sub_offset
                            result[field_name] = array_values
                        else:
                            # Handle array of basic types
                            struct_format = self._get_struct_format(field.type_name)
                            array_format = f"{self.endian_prefix}{array_size}{struct_format}"
                            values = struct.unpack_from(array_format, data, current_offset)
                            result[field_name] = list(values)
                            current_offset += array_size * self._get_type_size(field.type_name)
                    else:
                        if field.is_struct:
                            # Handle nested structure
                            sub_result, sub_offset = unpack_struct(data, current_offset, self.struct_fields[field.type_name])
                            result[field_name] = sub_result
                            current_offset = sub_offset
                        else:
                            # Handle basic type
                            struct_format = self._get_struct_format(field.type_name)
                            value = struct.unpack_from(f"{self.endian_prefix}{struct_format}", data, current_offset)[0]
                            result[field_name] = value
                            current_offset += self._get_type_size(field.type_name)
                    
            return result, current_offset

        result, _ = unpack_struct(data, 0, self.struct_fields[root_struct])
        return result


    def pack_data(self, data_dict: dict, root_struct: str) -> bytes:
        """Pack dictionary data according to the parsed structure"""
        def pack_struct(data_dict: dict, fields: Dict[str, StructField]) -> bytes:
            result = bytearray()
            current_byte = 0
            current_bit_pos = 0
            current_base_type = None
            base_type_size = 0
            
            for field_name, field in fields.items():
                field_data = data_dict.get(field_name, None)
                
                if field.bit_size is not None:
                    # Handle bit fields
                    value = field_data if field_data is not None else 0
                    mask = (1 << field.bit_size) - 1
                    value &= mask
                    
                    # Check if we're starting a new base type
                    if field.bit_offset == 0:
                        if current_bit_pos > 0:
                            # Write previous base type if exists
                            result.extend(struct.pack(f"{self.endian_prefix}{current_base_type}", current_byte))
                        current_byte = value
                        current_bit_pos = field.bit_size
                        current_base_type = field.format
                        base_type_size = self._get_type_size(field.type_name)
                    else:
                        current_byte |= (value << field.bit_offset)
                        current_bit_pos = field.bit_offset + field.bit_size
                    
                    # Write byte if this is the last field or next field is not a bit field
                    is_last_field = field is list(fields.values())[-1]
                    next_field = None if is_last_field else list(fields.values())[list(fields.values()).index(field) + 1]
                    if is_last_field or next_field.bit_size is None or next_field.bit_offset == 0:
                        result.extend(struct.pack(f"{self.endian_prefix}{current_base_type}", current_byte))
                        current_byte = 0
                        current_bit_pos = 0
                else:
                    # Handle regular fields
                    if current_bit_pos > 0:
                        # Flush any remaining bit fields
                        result.extend(struct.pack(f"{self.endian_prefix}{current_base_type}", current_byte))
                        current_byte = 0
                        current_bit_pos = 0
                        current_base_type = None
                    
                    if field.array_size:
                        array_data = field_data if field_data else [0] * field.array_size
                        array_data.extend([0] * (field.array_size - len(array_data)))
                        array_format = f"{self.endian_prefix}{field.array_size}{field.format}"
                        result.extend(struct.pack(array_format, *array_data[:field.array_size]))
                    else:
                        value = field_data if field_data is not None else 0
                        result.extend(struct.pack(f"{self.endian_prefix}{field.format}", value))
                
            return bytes(result)

        if root_struct not in self.struct_fields:
            raise ValueError(f"Unknown structure: {root_struct}")
            
        return pack_struct(data_dict, self.struct_fields[root_struct])

    def print_struct_tree(self, root_struct: str, indent: str = "", is_array: bool = False) -> None:
        """Print the structure tree starting from the given root structure.
        
        Args:
            root_struct: Name of the root structure to print
            indent: Current indentation level (used recursively)
            is_array: Whether the current structure is part of an array
        """
        if root_struct not in self.struct_fields:
            raise ValueError(f"Unknown structure: {root_struct}")

        array_info = "[]" if is_array else ""
        print(f"{indent}└── {root_struct}{array_info}")
        fields = self.struct_fields[root_struct]
        
        for field_name, field in fields.items():
            new_indent = indent + "    "
            array_suffix = f"[{field.array_size}]" if field.array_size else ""
            
            if field.is_struct:
                # For struct types, recursively print their fields
                print(f"{new_indent}└── {field_name}{array_suffix} ({field.type_name})")
                self.print_struct_tree(field.type_name, new_indent + "    ", bool(field.array_size))
            else:
                # For basic types, print type information with bit field details if present
                size_info = f"{field.size} bytes"
                type_info = f"{field.type_name} ({size_info})"
                if field.bit_size is not None:
                    bit_info = f" [bits {field.bit_offset}:{field.bit_offset + field.bit_size - 1}]"
                    type_info += bit_info
                print(f"{new_indent}└── {field_name}{array_suffix}: {type_info}")


    def get_struct_size(self, struct_name: str) -> int:
        """Get the total size of a structure in bytes."""
        if struct_name not in self.struct_sizes:
            raise ValueError(f"Unknown structure: {struct_name}")
        return self.struct_sizes[struct_name]

    def _get_struct_format(self, type_name: str) -> str:
        """Get struct format character for a given type name."""
        type_formats = {
            'char': 'c',
            'unsigned char': 'B',
            'short': 'h',
            'unsigned short': 'H',
            'int': 'i',
            'unsigned int': 'I',
            'long': 'l',
            'unsigned long': 'L',
            'float': 'f',
            'double': 'd',
            'int8_t': 'b',
            'uint8_t': 'B',
            'int16_t': 'h',
            'uint16_t': 'H',
            'int32_t': 'i',
            'uint32_t': 'I',
            'int64_t': 'q',
            'uint64_t': 'Q'
        }
        return type_formats.get(type_name, '')

    def _get_type_size(self, type_name: str) -> int:
        """Get size in bytes for a given type name."""
        type_sizes = {
            'char': 1,
            'unsigned char': 1,
            'short': 2,
            'unsigned short': 2,
            'int': 4,
            'unsigned int': 4,
            'long': 8,
            'unsigned long': 8,
            'float': 4,
            'double': 8,
            'int8_t': 1,
            'uint8_t': 1,
            'int16_t': 2,
            'uint16_t': 2,
            'int32_t': 4,
            'uint32_t': 4,
            'int64_t': 8,
            'uint64_t': 8
        }
        if type_name in self.struct_fields:
            return self.struct_sizes[type_name]
        return type_sizes.get(type_name, 0)

    def _print_struct_sizes(self):
        """Debug helper to print all structure sizes"""
        print("\nStructure sizes:")
        for struct_name in self.struct_fields:
            size = self.get_struct_size(struct_name)
            field_sizes = []
            for field in self.struct_fields[struct_name].values():
                field_sizes.append(f"{field.name}:{field.size}")
            print(f"{struct_name} ({size} bytes) - Fields: {', '.join(field_sizes)}")
    
    def _debug_print(self, *args):
        """Print debug information if debug flag is set"""
        if self.debug:
            print("[DEBUG]", *args)


if __name__ == "__main__":
    # Example 1: Parse structures from a directory
    print("Example 1: Parsing from directory")
    parser = CStructParser("test", endian='little')
    parser._print_struct_sizes()  # Add debug output
    
    print("\nStructure tree for MultiDimTest:")
    parser.print_struct_tree("MultiDimTest")
    print(f"\nTotal size: {parser.get_struct_size('MultiDimTest')} bytes\n")

    # Example 2: Parse structure directly from string
    print("\nExample 2: Parsing from string")
    struct_def = """
    typedef struct {
    unsigned int flags : 3;    // 3-bit field
    int mode : 2;     // 2-bit field
    int active : 1;   // 1-bit field
    int reserved : 26; // 26-bit field to fill up to 32 bits
    unsigned int regular_field;         // Regular 4-byte field
    } DirectStruct;
    """
    parser2 = CStructParser(struct_def, endian='little')
    print("\nStructure tree for DirectStruct:")
    parser2.print_struct_tree("DirectStruct")
    print(f"\nTotal size: {parser2.get_struct_size('DirectStruct')} bytes")

    
    # Create and unpack test data
    test_data = bytearray(parser2.get_struct_size('DirectStruct'))
    result = parser2.unpack_data(test_data, 'DirectStruct')
    print("\nUnpacked data:")
    print(result)

    result = parser2.pack_data(result, 'DirectStruct')
    print("\nPacked data (as bytes):")
    print(result)

    #Example 3: Unpacking data from a parsed structure
    print("\nExample 3: Unpacking data from directory")
    print("\nStructure tree for DeviceData:")
    parser.print_struct_tree("DeviceData")
    print(f"\nTotal size: {parser.get_struct_size('DeviceData')} bytes\n")
    print("Unpacking example data:")
    print(parser.unpack_data(bytes(parser.get_struct_size('DeviceData')), 'DeviceData'))

    print("\nExample 4: Unpacking bit fields")
    parser.print_struct_tree("BitFieldExample")
    print(f"\nTotal size: {parser.get_struct_size('BitFieldExample')} bytes\n")
    print(parser.unpack_data(bytes(parser.get_struct_size('BitFieldExample')), 'BitFieldExample'))

