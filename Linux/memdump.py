# credits to this medium forum https://medium.com/@liad_levy/reverse-pyarmor-obfuscated-python-script-using-memory-dump-technique-9823b856be7a
import sys
import re

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print('Usage:', sys.argv[0], '<process PID>', file=sys.stderr)
        exit(1)

    pid = sys.argv[1]

    # maps contains the mapping of memory of a specific project
    map_file = f"/proc/{pid}/maps"
    mem_file = f"/proc/{pid}/mem"

    # output file
    out_file = f'{pid}.dump'

    # iterate over regions
    with open(map_file, 'r') as map_f, open(mem_file, 'rb', 0) as mem_f, open(out_file, 'wb') as out_f:
        for line in map_f.readlines():  # for each mapped region
            m = re.match(r'([0-9A-Fa-f]+)-([0-9A-Fa-f]+) ([-r])', line)
            if m.group(3) == 'r':  # readable region
                start = int(m.group(1), 16)
                end = int(m.group(2), 16)
                mem_f.seek(start)  # seek to region start
                print(hex(start), '-', hex(end))
                try:
                    chunk = mem_f.read(end - start)  # read region contents
                    out_f.write(chunk)  # dump contents to standard output
                except OSError:
                    print(hex(start), '-', hex(end), '[error,skipped]', file=sys.stderr)
                    continue
    print(f'Memory dump saved to {out_file}')