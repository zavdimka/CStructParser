# CStructParser

A Python utility to parse binary data according to the C struct definitions from header files.

## Overview

CStructParser is a tool that helps bridge the gap between C and Python by:
- Parsing C struct definitions from header files
- Calculating struct sizes and memory layouts
- Unpacking binary data into Python dictionaries based on the parsed structures

## Features

- Supports nested structures
- Handles common C types (float, int32_t, uint16_t)
- Supports multi-dimensional arrays (automatically flattened)
- Parse from directory of header files or directly from string
- Configurable endianness (little-endian or big-endian)
- Detects circular dependencies
- Provides easy-to-use dictionary output
- Visual structure tree printing

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

## Supported C Types

The parser supports a comprehensive set of C types mapped to Python struct formats:

### Standard C Types
- `char` -> 'c' (1 byte)
- `signed char` -> 'b' (1 byte)
- `unsigned char` -> 'B' (1 byte)
- `short` -> 'h' (2 bytes)
- `unsigned short` -> 'H' (2 bytes)
- `int` -> 'i' (4 bytes)
- `unsigned int` -> 'I' (4 bytes)
- `long` -> 'l' (4 bytes)
- `unsigned long` -> 'L' (4 bytes)
- `long long` -> 'q' (8 bytes)
- `unsigned long long` -> 'Q' (8 bytes)
- `float` -> 'f' (4 bytes)
- `double` -> 'd' (8 bytes)
- `long double` -> 'd' (8 bytes)

### Fixed-Width Types (stdint.h)
- `int8_t`, `uint8_t` -> 'b'/'B' (1 byte)
- `int16_t`, `uint16_t` -> 'h'/'H' (2 bytes)
- `int32_t`, `uint32_t` -> 'i'/'I' (4 bytes)
- `int64_t`, `uint64_t` -> 'q'/'Q' (8 bytes)

### Extended Integer Types
- Minimum-width types (e.g., `int_least8_t`)
- Fast types (e.g., `int_fast8_t`)
- Pointer types (`intptr_t`, `uintptr_t`)
- Maximum-width types (`intmax_t`, `uintmax_t`)

Notes:
- Sizes assume a 64-bit system for pointer types
- `long double` is mapped to regular `double` as Python's struct module doesn't support extended precision
- All integer types follow standard C alignment rules

## Example

## Example

Here are examples of supported structure definitions:

```c
// Basic structure with arrays and nested types
typedef struct {
    float temperature[2];    // Array of 2 floats
    uint16_t humidity[8];    // Array of 8 uint16_t
    int32_t pressure;        // Single value
} SensorData;

// Structure with multi-dimensional arrays
typedef struct {
    float matrix[3][3];     // 3x3 matrix (becomes float[9])
    int cube[2][2][2];      // 3D array (becomes int[8])
    uint8_t image[2][4];    // 2D array (becomes uint8_t[8])
} MultiDimTest;
```

The parser will handle arrays, nested structures, and create a Python dictionary. It also provides a tree view of the structure:

```python
# Initialize parser and read binary data
parser = CStructParser("path/to/headers", endian='little')

# Print structure tree
print("Structure tree for MultiDimTest:")
parser.print_struct_tree("MultiDimTest")

# Output will look like:
└── MultiDimTest
    └── matrix[9]: float (36 bytes)
    └── cube[8]: int (32 bytes)
    └── image[8]: uint8_t (8 bytes)

# Unpack data
result = parser.unpack_data(binary_data, root_struct='MultiDimTest')

# Result will be structured as:
{
    'matrix': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Flattened 3x3 matrix
    'cube': [0, 0, 0, 0, 0, 0, 0, 0],                          # Flattened 2x2x2 cube
    'image': [0, 0, 0, 0, 0, 0, 0, 0]                          # Flattened 2x4 array
}
```

```text
DeviceStatus (29 bytes total):
├── device_id      : uint32_t  [0-3]   4 bytes
├── primary_sensor : SensorData [4-17]  14 bytes
│   ├── temperature : float     [4-7]   4 bytes
│   ├── humidity    : uint16_t  [8-9]   2 bytes
│   └── pressure    : int32_t   [10-13] 4 bytes
├── backup_sensor  : SensorData [14-27] 14 bytes
│   ├── temperature : float     [14-17] 4 bytes
│   ├── humidity    : uint16_t  [18-19] 2 bytes
│   └── pressure    : int32_t   [20-23] 4 bytes
├── error_flags    : uint8_t    [24]    1 byte
└── battery_voltage: float      [25-28] 4 bytes
```

## Key Features

- Bi-directional conversion between Python dictionaries and C structs
- Automatic handling of missing fields (defaults to 0)
- Array padding for undersized input arrays
- Nested structure support for both packing and unpacking

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)
