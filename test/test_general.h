#include <stdint.h>

// Test structures for CStructParser
// Basic types and arrays
typedef struct {
    float temperature[2];
    uint16_t humidity[8];
    int32_t pressure;
} SensorData;

// Nested structure
typedef struct {
    int8_t x;
    int8_t y;
    int8_t z;
} Vector3D;

typedef struct {
    Vector3D position;
    Vector3D velocity;
    float rotation[3];
} ObjectState;

// Complex nested structure with arrays
typedef struct {
    char name[16];
    uint32_t timestamp;
    SensorData readings[4];
    ObjectState movement;
    float calibration_matrix[3][3];
} DeviceData;

// Structure with all basic types
typedef struct {
    char c;
    unsigned char uc;
    short s;
    unsigned short us;
    int i;
    unsigned int ui;
    long l;
    unsigned long ul;
    float f;
    double d;
    int8_t i8;
    uint8_t u8;
    int16_t i16;
    uint16_t u16;
    int32_t i32;
    uint32_t u32;
    int64_t i64;
    uint64_t u64;
} AllTypes;