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
