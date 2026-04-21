import math

def is_number(x):
    """
    Retourne True si x est un int ou float (mais pas bool).
    """
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def format_float_sci(value):
    try:
        f = float(value)
    except:
        return value

    if f == 0:
        return "0"

    # Exposant basé sur la valeur brute
    exp = int(math.floor(math.log10(abs(f))))

    # Mantisse brute
    mantissa = f / (10 ** exp)

    # Mantisse arrondie à 2 décimales
    mantissa_str = f"{mantissa:.2f}".rstrip("0").rstrip(".")

    if exp == 0 or exp == 1:
        return mantissa_str

    return f"{mantissa_str} × 10^{exp}"


def parse_position(pos_str):
    """
    Convertit une position génomique en tuple (chromosome, start)
    pour permettre un tri correct.
    """
    s = pos_str.strip().lower()

    # Enlever "chr" si présent
    if s.startswith("chr"):
        s = s[3:]

    # Séparer chromosome et positions
    if ":" not in s:
        # Pas de chromosome → chromosome = 0
        try:
            return (0, int(s))
        except:
            return (0, 0)

    chrom, rest = s.split(":", 1)

    # Convertir chromosome
    if chrom == "x":
        chrom_num = 23
    elif chrom == "y":
        chrom_num = 24
    elif chrom in ("m", "mt"):
        chrom_num = 25
    else:
        try:
            chrom_num = int(chrom)
        except:
            chrom_num = 0

    # Gérer start-end
    if "-" in rest:
        start, _ = rest.split("-", 1)
    else:
        start = rest

    try:
        start_num = int(start)
    except:
        start_num = 0

    return (chrom_num, start_num)
