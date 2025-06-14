# CStructParser

A Python utility to parse binary data according to the C struct definitions from header files, powered by the `cstruct` library.

## Overview

CStructParser is a tool that helps bridge the gap between C and Python by:
- Parsing C struct definitions from header files
- Creating Python classes that mirror C structures using `cstruct`
- Unpacking binary data into Python objects based on the parsed structures
- Supporting bit fields and complex nested structures

## Features

- Built on the robust `cstruct` library
- Parses C struct definitions from header files
- Supports nested structures and arrays
- Handles common C types (float, int32_t, uint16_t, etc.)
- Supports bit fields
- Configurable endianness (little-endian or big-endian)
- Easy conversion between binary data and Python dictionaries
- Visual structure tree printing

## Installation

First, install the required dependency:

```bash
pip install cstruct
```

Then clone this repository or copy the CStructParser files into your project.

## Usage

CStructParser can be used in two ways: by parsing header files from a directory, or by directly passing C struct definitions as a string.

### Parsing from Header Files

```python
from CStructParser import CStructParser

# Initialize parser with path to C header files
parser = CStructParser("path/to/headers", endian='little')  # or 'big' for big-endian data

# Pack Python dictionary into binary data
data_dict = {
    'device_id': 1234,
    'primary_sensor': {
        'temperature': 25.5,
        'humidity': 65,
        'pressure': 1013
    }
}
binary_data = parser.pack_data(data_dict, root_struct='DeviceStatus')

# Unpack binary data back into dictionary
result = parser.unpack_data(binary_data, root_struct='DeviceStatus')
print(result)

# Print structure tree for visualization
parser.print_struct_tree('DeviceStatus')
```

### Parsing from String

```python
from CStructParser import CStructParser

# Define structure directly
struct_def = """
typedef struct {
    float values[4];
    uint32_t count;
} DirectStruct;
"""

# Initialize parser with structure definition
parser = CStructParser(struct_def, endian='little')

# Pack data into binary format
data = {
    'values': [1.0, 2.0, 3.0, 4.0],
    'count': 4
}
binary_data = parser.pack_data(data, 'DirectStruct')

# Unpack binary data back
result = parser.unpack_data(binary_data, 'DirectStruct')
print(result)
```

### Working with Bit Fields

```python
from CStructParser import CStructParser

# Define structure with bit fields
struct_def = """
typedef struct {
    uint8_t flag1 : 1;
    uint8_t flag2 : 2;
    uint8_t flag3 : 5;
} BitFlags;
"""

parser = CStructParser(struct_def)
data = {'flag1': 1, 'flag2': 2, 'flag3': 15}
binary = parser.pack_data(data, 'BitFlags')
result = parser.unpack_data(binary, 'BitFlags')
print(result)  # {'flag1': 1, 'flag2': 2, 'flag3': 15}
```

## Supported C Types

The parser supports all standard C types through the `cstruct` library:

### Standard C Types
- `char`, `unsigned char`
- `short`, `unsigned short`
- `int`, `unsigned int`
- `long`, `unsigned long`
- `long long`, `unsigned long long`
- `float`, `double`

### Fixed-Width Types (stdint.h)
- `int8_t`, `uint8_t`
- `int16_t`, `uint16_t`
- `int32_t`, `uint32_t`
- `int64_t`, `uint64_t`

## Performance

By using the `cstruct` library, CStructParser provides efficient binary data handling with minimal overhead. The library creates optimized Python classes that directly map to C structures, making it suitable for handling large binary data sets.
