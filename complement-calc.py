def complement_calculator(value, show_all_bit_widths=False, show_results_as_hex=False):
    widths = [8]
    if show_all_bit_widths:
        widths.extend([16, 32, 64, 256])

    print(f"\nCalculating complements for: {value} (0x{abs(value):X})")
    print("=" * 80)
    for bits in widths:
        name: str = f"{bits}-bit"
        max_val = (1 << (bits - 1)) - 1
        min_val = -(1 << (bits - 1))
        if not min_val <= value <= max_val:
            print(f"\n{name}: OUT OF RANGE (LARGEST POSSIBLE VALUE: {2**(bits-1)-1})")
            continue
        work_val = abs(value)
        binary = bin(work_val)[2:].zfill(bits)
        ones_comp = int(''.join('1' if b == '0' else '0' for b in binary), 2)
        twos_comp = (ones_comp + 1) & ((1 << bits) - 1)

        # show as blocks of 8 bit
        bin_display = ' '.join(binary[i:i+8] for i in range(0, bits, 8))

        print(f"\n{name}:")
        print(f"  Binary:     {bin_display}")

        if show_results_as_hex: # case: show as hex
            print(f"  One's comp: 0x{ones_comp:0{bits//4}X}")
            print(f"  Two's comp: 0x{twos_comp:0{bits//4}X}")
        else:  # case: show as bin
            ones_comp_bin = bin(ones_comp)[2:].zfill(bits)
            twos_comp_bin = bin(twos_comp)[2:].zfill(bits)
            ones_comp_display = ' '.join(ones_comp_bin[i:i+8] for i in range(0, bits, 8))
            twos_comp_display = ' '.join(twos_comp_bin[i:i+8] for i in range(0, bits, 8))
            print(f"  One's comp: {ones_comp_display}")
            print(f"  Two's comp: {twos_comp_display}")


def main():
    SHOW_ALL_BIT_WIDTHS = True
    SHOW_RESULTS_AS_HEX = False
    input_str = input("Enter number (e.g. 165 or 0xa5): ").lower()
    # add 0x if hex string is provided and it is missing, also don't allow - (negative number)
    if "0x" not in input_str:
        for c in input_str:
            if not c.isdigit():
                if c == "-":
                    print("Do not put a negative number!")
                    return
                input_str = "0x" + input_str
                break

    try:
        value = int(input_str, 0)
        complement_calculator(value, SHOW_ALL_BIT_WIDTHS, SHOW_RESULTS_AS_HEX)
    except ValueError as e:
        print(f"Invalid input: {e}")


main()
