"""Native fzf contact picker; local matches stay available during directory lookup."""

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


CONFIG = Path(__file__).resolve().parents[2]
CONTACTS = CONFIG / "neomutt/scripts/fetch_contacts"
FZF = Path(__file__).with_name("khal-fzf")


def valid_address(address):
    return (isinstance(address, str) and address.isprintable()
            and re.fullmatch(r"[^@\s,<>]+@[^@\s,<>]+", address))


def unique_contacts(contacts, excluded):
    seen = {address.casefold() for address in excluded}
    result = []
    for name, address in contacts:
        if valid_address(address) and address.casefold() not in seen:
            seen.add(address.casefold())
            name = " ".join(name.split()) if isinstance(name, str) else ""
            result.append(("".join(char for char in name if char.isprintable()), address))
    return result


def local_contacts(excluded):
    result = subprocess.run(
        ["/opt/homebrew/bin/mu", "cfind", "--format=json", "-q"],
        capture_output=True, text=True, timeout=2,
    )
    if result.returncode == 2:  # Empty address book.
        return []
    result.check_returncode()
    rows = json.loads(result.stdout)
    # mu's export order is not a useful initial selection. Prefer personal
    # correspondence, most recently seen first, then frequency for ties.
    rows.sort(key=lambda row: (
        bool(row.get("personal")), row.get("last-seen", 0), row.get("frequency", 0),
    ), reverse=True)
    return unique_contacts(((row.get("name"), row.get("email")) for row in rows), excluded)


def directory_contacts(query, excluded, command=CONTACTS):
    if len(query.strip()) < 3:
        return []
    result = subprocess.run(
        [str(command), query], capture_output=True, text=True, timeout=3.5, check=True,
    )
    rows = json.loads(result.stdout)
    return unique_contacts((item for row in rows for item in row.items()), excluded)


def candidate_lines(contacts):
    # Keep the original address in a hidden field; display/search the readable
    # name and address. Never interpret contact names as terminal escape codes.
    return "".join(f"{address}\t{name} <{address}>\n" for name, address in contacts)


class PickerConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("localhost", timeout=0.2)
        self.path = path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect(self.path)


def current_query(path):
    connection = PickerConnection(path)
    try:
        connection.request("GET", "/?limit=0")
        return json.loads(connection.getresponse().read())["query"]
    finally:
        connection.close()


def feed_directory(process, endpoint, contacts, excluded):
    # Append new contacts to fzf's input stream. Reloading the whole list in
    # fzf 0.74 loses marks on contacts hidden by the current query, even with
    # --id-nth. Keeping the stream open preserves selection and fuzzy search.
    worker = ThreadPoolExecutor(max_workers=1)
    pending = None
    seen = {address.casefold() for _, address in contacts}
    tried = set()
    query, changed = None, time.monotonic()
    try:
        process.stdin.write(candidate_lines(contacts))
        process.stdin.flush()
        while process.poll() is None:
            if pending is not None and pending.done():
                try:
                    extra = unique_contacts(pending.result(), seen | set(excluded))
                    if extra:
                        process.stdin.write(candidate_lines(extra))
                        process.stdin.flush()
                        seen.update(address.casefold() for _, address in extra)
                except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
                    pass  # A directory outage leaves local search usable.
                pending = None
            try:
                latest = current_query(endpoint)
            except (OSError, http.client.HTTPException, ValueError, KeyError):
                latest = query  # fzf may still be starting or already exiting.
            if latest != query:
                query, changed = latest, time.monotonic()
            if (pending is None and query and len(query.strip()) >= 3
                    and query not in tried and time.monotonic() - changed >= 0.25):
                tried.add(query)
                pending = worker.submit(directory_contacts, query, excluded, CONTACTS)
            time.sleep(0.1)
    except BrokenPipeError:
        pass  # Accepted/cancelled while a directory result was arriving.
    finally:
        worker.shutdown(wait=False, cancel_futures=True)


def pick_contacts(query, excluded):
    contacts = local_contacts(excluded)
    with tempfile.TemporaryDirectory(prefix="khal-contacts-") as directory:
        endpoint = str(Path(directory) / "picker.sock")
        with tempfile.TemporaryFile(mode="w+") as output:
            process = subprocess.Popen([
                str(FZF), "--no-height", "--layout=reverse", "--border=rounded",
                "--border-label= 󰀉 Attendees ", "--prompt= ",
                "--header=Alt-Space marks · Enter adds · Esc cancels", "--no-info",
                "--multi", "--marker=", "--no-preview", "--scheme=default", "--tiebreak=index",
                "--delimiter=\t", "--with-nth=2..", "--accept-nth=1",
                f"--query={query}", "--bind=ctrl-g:abort", f"--listen={endpoint}",
            ], stdin=subprocess.PIPE, stdout=output, text=True)
            try:
                feed_directory(process, endpoint, contacts, excluded)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                try:
                    process.stdin.close()
                except BrokenPipeError:
                    pass
            if process.returncode in (1, 130):
                return []
            if process.returncode:
                raise subprocess.CalledProcessError(process.returncode, str(FZF))
            output.seek(0)
            addresses = output.read().splitlines()
            for address in addresses:
                if not valid_address(address) or address.casefold() in {a.casefold() for a in excluded}:
                    raise ValueError("Invalid selected address")
            return list(dict.fromkeys(addresses))
