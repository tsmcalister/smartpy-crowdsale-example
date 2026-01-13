import smartpy as sp


@sp.module
def rng_utils():
    """
    All functions here assume 32 bytes of entropy
    consider using sp.sha256() before passing to the function
    """

    def draw_uniform(params: sp.record(entropy=sp.bytes, n=sp.nat)) -> sp.nat:
        # Edge-case: n ≤ 1 ⇒ always return 0
        if params.n <= 1:
            return sp.nat(0)
        else:

            # ── fetch randomness ────────────────────────────────────────────────
            entropy = params.entropy

            # how many bits are required to represent numbers < n ?
            bits_needed = sp.nat(0)
            y = sp.as_nat(params.n - 1)
            while y > 0:
                y = y >> 1
                bits_needed += 1

            # bit masks for a byte (MSB → LSB)
            masks = [
                sp.bytes("0x80"),
                sp.bytes("0x40"),
                sp.bytes("0x20"),
                sp.bytes("0x10"),
                sp.bytes("0x08"),
                sp.bytes("0x04"),
                sp.bytes("0x02"),
                sp.bytes("0x01"),
            ]
            ZERO = sp.bytes("0x00")

            # accumulators
            idx = sp.nat(0)  # which byte we are on
            num = sp.nat(0)  # candidate number being built
            bits_collected = sp.nat(0)
            result = sp.nat(0)
            drawn = False

            # ── rejection-sampling loop ────────────────────────────────────────
            while not drawn:
                # get next byte of entropy
                match sp.slice(idx, 1, entropy):
                    case Some(byte):
                        idx += 1
                        # iterate through its bits (MSB → LSB)
                        for m in masks:
                            if not drawn:  # ignore extra bits after success
                                bit_is_one = sp.and_bytes(byte, m) != ZERO
                                num = (num << 1) + (sp.nat(1) if bit_is_one else sp.nat(0))
                                # sp.trace(num)
                                bits_collected += 1

                                # once we have enough bits, evaluate the candidate
                                if bits_collected == bits_needed:
                                    if num < params.n:  # accept
                                        result = num
                                        drawn = True
                                    else:  # reject → reset and keep sampling
                                        num = sp.nat(0)
                                        bits_collected = sp.nat(0)
                    case None:
                        # if we run out of bytes
                        idx = 0
                        entropy = sp.sha256(entropy)
            return result