
#. Funcs to test strings...


def str_contains(string, items):
    '''     
            # Single character check
                print(str_contains("hello world", "e"))  # Output: True
            # Multiple characters check
                print(str_contains("hello world", ["a", "e", "i"]))  # Output: True
            # Substring check
                print(str_contains("hello world", "world"))  # Output: True
            # List of substrings
                print(str_contains("hello world", ["world", "earth"]))  # Output: True
            # No match
                print(str_contains("hello world", ["x", "y", "z"]))  # Output: False
    '''
    # Check if the inputs are valid
    if not isinstance(string, str):
        raise ValueError("The 'string' argument must be a string.")
    if not isinstance(items, (str, list)):
        raise ValueError("The 'items' argument must be a string or a list of strings.")
    
    # Ensure items is a list, even if it's a single string or character
    if isinstance(items, str):
        items = [items]
    
    # Ensure all items in the list are strings
    if not all(isinstance(item, str) for item in items):
        raise ValueError("All elements in 'items' must be strings.")
    
    return any(item in string for item in items)

