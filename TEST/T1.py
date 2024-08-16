def generate_path(number):
    num_str = str(number)
    path_parts = []

    if number < 100:
        # Numbers less than 100 don't get broken down
        path_parts.append(num_str.zfill(4))  # Pad to make it a 4-digit number
    else:
        # Iterate over the number string in chunks for numbers 100 and above
        for i in range(len(num_str)):
            # Pad the number with zeros
            part = num_str[:i+1] + '0' * (len(num_str) - i - 1)
            path_parts.append(part)
        
        # The last part is the number itself
        path_parts[-1] = num_str

    # Join the parts with backslashes
    path = "\\".join(path_parts)
    return path

# Test cases
print(generate_path(6687))
