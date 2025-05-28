# CStructParser

A Python utility for parsing C struct definitions from header files and unpacking binary data according to those structures.

## Overview

CStructParser is a tool that helps bridge the gap between C and Python by:
- Parsing C struct definitions from header files
- Calculating struct sizes and memory layouts
- Unpacking binary data into Python dictionaries based on the parsed structures

## Features

- Supports nested structures
- Handles common C types (float, int32_t, uint16_t)
- Follows #include directives to parse dependent headers
- Detects circular dependencies
- Provides easy-to-use dictionary output

## Usage

```python
from CStructParser import CStructParser

# Initialize parser with path to C header files
parser = CStructParser("path/to/headers")

# Unpack binary data according to root structure (defaults to 'T_TARGET')
binary_data = bytearray(224)  # Your binary data
result = parser.unpack_data(binary_data)
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

Given a C header file with:

```c
typedef struct {
    float value1;
    int32_t value2;
    uint16_t value3;
} MyStruct;
```

The parser will create a Python dictionary structure:

```python
{
    'value1': 1.23,
    'value2': 42,
    'value3': 65535
}
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)
