from typing import Dict, Tuple


class CTypeFormat:
    # Standard C types
    STANDARD_TYPES = {
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
        'long double': ('d', 8),
    }

    # stdint.h fixed-width types
    FIXED_WIDTH_TYPES = {
        'int8_t': ('b', 1),
        'uint8_t': ('B', 1),
        'int16_t': ('h', 2),
        'uint16_t': ('H', 2),
        'int32_t': ('i', 4),
        'uint32_t': ('I', 4),
        'int64_t': ('q', 8),
        'uint64_t': ('Q', 8),
    }

    # stdint.h minimum-width types
    MIN_WIDTH_TYPES = {
        'int_least8_t': ('b', 1),
        'uint_least8_t': ('B', 1),
        'int_least16_t': ('h', 2),
        'uint_least16_t': ('H', 2),
        'int_least32_t': ('i', 4),
        'uint_least32_t': ('I', 4),
        'int_least64_t': ('q', 8),
        'uint_least64_t': ('Q', 8),
    }

    # stdint.h fast types
    FAST_TYPES = {
        'int_fast8_t': ('b', 1),
        'uint_fast8_t': ('B', 1),
        'int_fast16_t': ('h', 2),
        'uint_fast16_t': ('H', 2),
        'int_fast32_t': ('i', 4),
        'uint_fast32_t': ('I', 4),
        'int_fast64_t': ('q', 8),
        'uint_fast64_t': ('Q', 8),
    }

    # stdint.h pointer and max types
    SPECIAL_TYPES = {
        'intptr_t': ('q', 8),
        'uintptr_t': ('Q', 8),
        'intmax_t': ('q', 8),
        'uintmax_t': ('Q', 8),
    }

    @staticmethod
    def normalize_type_name(type_name: str) -> str:
        """Normalize type name by removing extra spaces and standardizing format."""
        # Remove extra spaces and normalize to single space between words
        return ' '.join(word for word in type_name.split() if word)

    @classmethod
    def get_all_formats(cls) -> Dict[str, Tuple[str, int]]:
        """Returns all format specifications combined into a single dictionary."""
        all_formats = {}
        all_formats.update(cls.STANDARD_TYPES)
        all_formats.update(cls.FIXED_WIDTH_TYPES)
        all_formats.update(cls.MIN_WIDTH_TYPES)
        all_formats.update(cls.FAST_TYPES)
        all_formats.update(cls.SPECIAL_TYPES)

        # Add normalized versions of all type names
        normalized_formats = {}
        for type_name, format_info in all_formats.items():
            normalized_name = cls.normalize_type_name(type_name)
            normalized_formats[normalized_name] = format_info

        all_formats.update(normalized_formats)
        return all_formats
