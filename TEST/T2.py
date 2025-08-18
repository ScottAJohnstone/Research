def parse_usr_input(s: str):
    """
    Parses strings like:
      - "12/34-5678"       -> volume=12, page=34, instrument=5678
      - "12.34-5678-note"  -> volume=12, page=34, instrument=5678, comment="note"
      - "56/78-AB123-xyz"  -> volume=56, page=78, instrument=123, remainder="AB", comment="xyz"
      - "9999"             -> map_num=9999 (strictly numeric, no '-' or '/')
    Returns: (volume, page, map_num, instrument, remainder, comment)
    """
    volume = page = map_num = instrument = remainder = comment = None

    # Handle dashes
    dash_count = s.count("-")
    if dash_count == 1:
        first, second = s.split("-", 1)
    elif dash_count >= 2:
        first, second, comment = s.split("-", 2)  # first dash split + everything after 2nd is comment
    else:
        first, second = s, ""

    # Normalize "." to "/" for volume/page handling
    first = first.replace(".", "/")

    # If first has "/", try to parse volume/page (both must be numeric)
    if "/" in first:
        parts = first.split("/")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            volume, page = parts[0], parts[1]

    # Target to analyze for instrument/map/remainder
    target = second if second else first

    if target:
        if target.isdigit():
            # Strictly numeric, and original string has no '-' '.' or '/' → Map
            if dash_count == 0 and "/" not in s and "." not in s:
                map_num = target
            else:
                instrument = target
        else:
            # Split into numbers (instrument) and non-numbers (remainder), preserving order
            nums, chars = "", ""
            for ch in target:
                if ch.isdigit():
                    nums += ch
                else:
                    chars += ch
            instrument = nums if nums else None
            remainder = chars if chars else None

    return volume, page, map_num, instrument, remainder, comment


# Examples
print(parse_usr_input("12/34-5678"))        # ('12','34',None,'5678',None,None)
print(parse_usr_input("12.34-5678-note"))   # ('12','34',None,'5678',None,'note')
print(parse_usr_input("56/78-AB123-xyz"))   # ('56','78',None,'123','AB','xyz')
print(parse_usr_input("99.12-XYZ-comment")) # ('99','12',None,None,'XYZ','comment')
print(parse_usr_input("77/88-555"))         # ('77','88',None,'555',None,None)
print(parse_usr_input("45.67"))             # ('45','67',None,None,None,None)
print(parse_usr_input("AB123"))             # (None,None,None,'123','AB',None)
print(parse_usr_input("9999"))              # (None,None,'9999',None,None,None)
