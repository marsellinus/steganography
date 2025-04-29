"""
Binary test tool for steganography application - decode binary and analyze corrupted text
"""
import sys
from binary_decoder import binary_to_text, text_to_binary
from unicode_handler import binary_to_text_unicode, text_to_binary_unicode, sanitize_text

def print_comparison(binary_input):
    """Print comparison of different decoding methods"""
    print("\n" + "="*60)
    print("BINARY DECODING COMPARISON")
    print("="*60)
    
    # Clean binary input to remove spaces and ensure proper format
    clean_binary = ''.join(c for c in binary_input if c in '01 \n\t')
    
    print(f"\nInput binary (first 50 chars):")
    print(clean_binary[:50] + "..." if len(clean_binary) > 50 else clean_binary)
    print(f"\nTotal binary length: {len(clean_binary)} characters")
    print(f"Clean binary length: {len(''.join(c for c in clean_binary if c in '01'))} bits")
    
    # Simple decoder
    try:
        simple_result = binary_to_text(clean_binary)
        print("\n1. Basic Binary Decoder:")
        print("-" * 40)
        print(simple_result)
        print(f"Length: {len(simple_result)} characters")
    except Exception as e:
        print(f"\n1. Basic Binary Decoder Error: {str(e)}")
    
    # Unicode handler decoder
    try:
        unicode_result = binary_to_text_unicode(clean_binary)
        print("\n2. Unicode Handler Decoder:")
        print("-" * 40)
        print(unicode_result)
        print(f"Length: {len(unicode_result)} characters")
    except Exception as e:
        print(f"\n2. Unicode Handler Decoder Error: {str(e)}")
    
    # Sanitized result
    try:
        sanitized = sanitize_text(unicode_result)
        print("\n3. Sanitized Result:")
        print("-" * 40)
        print(sanitized)
        print(f"Length: {len(sanitized)} characters")
    except Exception as e:
        print(f"\n3. Sanitized Result Error: {str(e)}")
    
    print("\n" + "="*60)

def main():
    """Main function for binary test tool"""
    
    if len(sys.argv) > 1:
        # Read from file if provided
        try:
            with open(sys.argv[1], 'r') as f:
                binary_input = f.read()
                print_comparison(binary_input)
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return
    else:
        # Interactive mode
        print("Binary Test Tool")
        print("\n1. Enter binary string (0s and 1s, spaces allowed)")
        print("2. Paste binary from clipboard")
        print("3. Enter text to convert to binary")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            binary_input = input("\nEnter binary string: ")
            print_comparison(binary_input)
        
        elif choice == '2':
            try:
                import tkinter as tk
                root = tk.Tk()
                root.withdraw()  # Hide the window
                binary_input = root.clipboard_get()
                print("\nPasted from clipboard")
                print_comparison(binary_input)
            except Exception as e:
                print(f"Error pasting from clipboard: {str(e)}")
                binary_input = input("\nEnter binary string manually: ")
                print_comparison(binary_input)
        
        elif choice == '3':
            text_input = input("\nEnter text to convert to binary: ")
            binary = text_to_binary(text_input)
            print(f"\nBinary representation:\n{binary}")
            
            unicode_binary = text_to_binary_unicode(text_input)
            print(f"\nUnicode binary representation:\n{' '.join(unicode_binary[i:i+8] for i in range(0, len(unicode_binary), 8))}")
        
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
