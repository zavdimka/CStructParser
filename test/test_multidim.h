#include <stdint.h>

typedef struct {
    float matrix[3][3];     // Will become float[9]
    int cube[2][2][2];      // Will become int[8]
    uint8_t image[2][4];    // Will become uint8_t[8]
} MultiDimTest;
