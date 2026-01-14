def fib(n: int):
    return 0 if n == 0 else 1 if n == 1 else fib(n - 2) + fib(n - 1)

def char_to_bond(char):
    bond_symbols = {1: ['1', '-', '|'],
                    2: ['2', '=', '‖'],
                    3: ['3', '≡', '⦀']}

    for item in bond_symbols.items():
        if char in item[1]:
            return item[0]

    return 0

def dict_get_or_create(dict, *args):
    if args and (not args[0] in dict):
        dict.update({args[0]: {}})
    if len(args) > 1:
        return dict_get_or_create(dict[args[0]], *args[1:])
    return dict[args[0]]
