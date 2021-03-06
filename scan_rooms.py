import socket
import time
import argparse
import pickle
import json


PORTS = {"ssh": 22,
         "rdp": 3389}
ROOMS = {"TP Info A": 8,
         "TP Info B": 9,
         "TP Info C": 114,
         "TP Info D": 109,
         "TP Info E": 112,
         "Radiocom": 203}
HOSTNAME_TEMPLATE = "tc405-{:03d}-{:02d}.insa-lyon.fr"
PC_COUNT = 16
TIMEOUT = 0.5
LOOP_DELAY = None
OUTPUT_FORMAT = "text"
OUTPUT_BASENAME = "tc_pc_scan"
PROGRESS_DISPLAY_LEN = 32


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("room_names", nargs="*", choices=["all"] + list(ROOMS), default="all")
    parser.add_argument("--pc-count", "-c", type=int, default=PC_COUNT)
    parser.add_argument("--timeout", "-t", type=float, default=TIMEOUT)
    parser.add_argument("--loop-delay", "-d", type=float, default=LOOP_DELAY)
    parser.add_argument("--output-format", "-f", choices=["pickle", "pkl", "text", "txt", "json"], default=OUTPUT_FORMAT)
    parser.add_argument("--output-file", "-o")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.room_names == "all":
        args.room_names = list(ROOMS)

    if args.output_format == "pickle":
        args.output_format = "pkl"
    elif args.output_format == "text":
        args.output_format = "txt"

    if args.output_file is None:
        args.output_file = ".".join((OUTPUT_BASENAME, args.output_format))

    return args


def test_port(host, port, timeout=1.0):
     with socket.socket() as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except socket.error:
            return False


def progress_bar(progress, bar_len=PROGRESS_DISPLAY_LEN):
    return "[{: <{}}] ({:4.0%})".format("=" * int(bar_len * progress), bar_len, progress)


def scan_rooms(room_names, pc_count=16, timeout=1.0, verbose=False):
    rooms = []
    if verbose:
        total_count = len(room_names) * pc_count
        n = 0
    for room_name in room_names:
        room_id = ROOMS[room_name]
        online_pcs = []
        for pc_id in range(1, pc_count + 1):
            host = HOSTNAME_TEMPLATE.format(room_id, pc_id)
            if verbose:
                print("\r{} {: <30}".format(progress_bar(n / total_count), host), end='')
                n += 1
            answers = [protocol for protocol, port in PORTS.items() if test_port(host, port, timeout)]
            if answers:
                online_pcs.append({"id": pc_id, "host_name": host, "protocols": answers})
        if online_pcs:
            rooms.append({"name": room_name, "online_pcs": online_pcs})
    if verbose:
        print("\r{} {: <30}".format(progress_bar(1), "Done!"))
    return rooms


def save_pickle(rooms, output_file):
    with open(output_file, 'wb') as f:
        pickle.dump(rooms, f)


def save_text(rooms, output_file):
    with open(output_file, 'w') as f:
        for room in rooms:
            f.write("{:-^37}\n".format(room["name"]))
            for pc in room["online_pcs"]:
                f.write("  {: >7}  {}\n".format("/".join(pc["protocols"]), pc["host_name"]))
            f.write("\n")


def save_json(rooms, output_file):
    with open(output_file, 'w') as f:
        json.dump(rooms, f, indent=4)


def main(args):
    while True:
        rooms = scan_rooms(args.room_names, args.pc_count, args.timeout, args.verbose)

        if args.output_format == "pkl":
            save_pickle(rooms, args.output_file)
        elif args.output_format == "txt":
            save_text(rooms, args.output_file)
        elif args.output_format == "json":
            save_json(rooms, args.output_file)

        if args.loop_delay is None:
            break
        else:
            time.sleep(args.loop_delay)


if __name__ == "__main__":
    main(parse_args())
