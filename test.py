import cstruct

cstruct.parse("""
    struct A {
      int32_t x;
      int32_t y;
    };

    struct B {
      struct A a;
      int32_t z;
    };
    """)

A = cstruct.get_type("struct A")
B = cstruct.get_type("struct B")

        # Create new structure class using parse
        self.struct_class = cstruct.CStruct.parse(
            cleaned_content,
            __byte_order__='<' if self.endian == 'little' else '>'
        )

a = A(x=10, y=20)
b = B(a=a, z=30)

bs = b.pack()

b2 = B()
b2.unpack(bs)
print(b2)