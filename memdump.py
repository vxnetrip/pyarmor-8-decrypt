import os
import sys
import ctypes
import psutil
import string
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Constants for memory protection
PAGE_READONLY = 0x02
PAGE_READWRITE = 0x04
PAGE_WRITECOPY = 0x08
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_READWRITE = 0x40

# Memory information structures
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong)
    ]

def get_process_handle(pid):
    PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
    return ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

def read_memory(handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t(0)
    if not ctypes.windll.kernel32.ReadProcessMemory(handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(bytes_read)):
        raise ctypes.WinError(ctypes.get_last_error())
    return buffer.raw[:bytes_read.value]

def is_readable_region(protect):
    readable_protections = [
        PAGE_READONLY, PAGE_READWRITE, PAGE_WRITECOPY, PAGE_EXECUTE_READ, PAGE_EXECUTE_READWRITE
    ]
    return protect in readable_protections

def check_pid():
    os.system("tasklist | findstr python")

def dump(pid):
    process = psutil.Process(pid)
    handle = get_process_handle(pid)

    out_file = f'{pid}.dump'
    
    with open(out_file, 'wb') as out_f:
        address = 0
        memory_basic_information = MEMORY_BASIC_INFORMATION()
        while ctypes.windll.kernel32.VirtualQueryEx(handle, ctypes.c_void_p(address), ctypes.byref(memory_basic_information), ctypes.sizeof(memory_basic_information)):
            if is_readable_region(memory_basic_information.Protect):
                start = memory_basic_information.BaseAddress
                size = memory_basic_information.RegionSize
                end = start + size
                print(f"{Fore.GREEN}{hex(start)} - {hex(end)}")
                try:
                    chunk = read_memory(handle, start, size)
                    out_f.write(chunk)
                except (OSError, ctypes.WinError):
                    print(f"{Fore.RED}{hex(start)} - {hex(end)} [error, skipped]", file=sys.stderr)
                    continue
            address += memory_basic_information.RegionSize
    print(f"{Fore.YELLOW}Memory dump saved to {out_file}")

def extract_strings(filename, min_length=4):
    with open(filename, 'rb') as f:
        result = ""
        printable = set(string.printable.encode())
        chunk = f.read(1024)
        while chunk:
            for byte in chunk:
                if byte in printable:
                    result += chr(byte)
                else:
                    if len(result) >= min_length:
                        yield result
                    result = ""
            chunk = f.read(1024)
        if len(result) >= min_length:
            yield result

def dump_string(dump_file, pid):
    output_file = f"{pid}.strings"
    with open(output_file, 'w') as out_f:
        for s in extract_strings(dump_file):
            out_f.write(s + '\n')
    print(f"{Fore.YELLOW}Strings extracted to {output_file}")

def main_menu():
    while True:
        print('\nCreated by pssyho')
        print("\nMenu:")
        print(f"{Fore.CYAN}1. Check PID")
        print(f"{Fore.CYAN}2. Dump")
        print(f"{Fore.CYAN}3. Dump-String")
        print(f"{Fore.CYAN}4. Exit")
        choice = input(f"{Fore.CYAN}Enter your choice: ")

        if choice == '1':
            check_pid()
        elif choice == '2':
            pid = int(input(f"{Fore.CYAN}Enter PID to dump: "))
            dump(pid)
        elif choice == '3':
            pid = int(input(f"{Fore.CYAN}Enter PID to extract strings from: "))
            dump_file = f"{pid}.dump"
            dump_string(dump_file, pid)
        elif choice == '4':
            break
        else:
            print(f"{Fore.RED}Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
