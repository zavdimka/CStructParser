typedef struct {
    unsigned int flags : 3;    // 3-bit field
    int mode : 2;     // 2-bit field
    int active : 1;   // 1-bit field
    int reserved : 26; // 26-bit field to fill up to 32 bits
    unsigned int regular_field;         // Regular 4-byte field
} BitFieldExample;