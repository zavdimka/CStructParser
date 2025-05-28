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

## Example

Given C header files with nested structures:

```c
// sensors.h
typedef struct {
    float temperature;
    uint16_t humidity;
    int32_t pressure;
} SensorData;

// device_status.h
typedef struct {
    uint32_t device_id;
    SensorData primary_sensor;
    SensorData backup_sensor;
    uint8_t error_flags;
    float battery_voltage;
} DeviceStatus;
```

The parser will handle nested structures and create a Python dictionary:

```python
# Initialize parser and read binary data
parser = CStructParser("path/to/headers")
binary_data = get_device_data()  # Your binary data source
result = parser.unpack_data(binary_data, root_struct='DeviceStatus')

# Result will be structured as:
{
    'device_id': 12345,
    'primary_sensor': {
        'temperature': 25.4,
        'humidity': 60,
        'pressure': 101325
    },
    'backup_sensor': {
        'temperature': 25.6,
        'humidity': 61,
        'pressure': 101320
    },
    'error_flags': 0,
    'battery_voltage': 3.7
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

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)
