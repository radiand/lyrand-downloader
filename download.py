import argparse
import csv
import json
import multiprocessing

from typing import List, Tuple

import plyr


def flatten(l):
    return [item for sublist in l for item in sublist]


def sanitize_artist(txt):
    return txt.split(",")[0]


def sanitize_title(txt):
    return txt.split("-")[0]


def csv2list(path: str) -> List[Tuple[str, str]]:
    with open(path) as f:
        reader = csv.reader(f)
        next(reader, None)  # drop header
        return [(r[2], r[1]) for r in reader]


def fetch_track_lyrics(artist, title):
    query = plyr.Query(artist=artist, title=title, get_type="lyrics")
    items = query.commit()
    if not items:
        print("ERROR: {} - {} has no lyrics".format(artist, title))
        return None
    decoded = items[0].data.decode("utf-8")
    if decoded == "Instrumental" or decoded == "[ INSTRUMENTAL ]":
        print("{} - {} is instrumental".format(artist, title))
        return None
    return decoded


def fetch_track_lyrics_worker(artist, title, storage):
    lyrics = fetch_track_lyrics(artist, title)
    if lyrics:
        storage.append((artist, title, lyrics))


def download_lyrics(tracks):
    manager = multiprocessing.Manager()
    lyrics = manager.list()

    processes = []

    for artist, title in tracks:
        p = multiprocessing.Process(
            target=fetch_track_lyrics_worker,
            args=(sanitize_artist(artist), sanitize_title(title), lyrics))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    return list(lyrics)


def get_args():
    ap = argparse.ArgumentParser(description="download lyrics")
    ap.add_argument("input", help="paths to csv files generated by Exportify", nargs="+")
    ap.add_argument("-o", "--output", help="path to .json file to be dumped")
    return ap.parse_args()


def main():
    args = get_args()

    tracks = flatten([csv2list(path) for path in args.input])
    lyrics = download_lyrics(tracks)

    print("downloaded lyrics for {} out of {} tracks".format(len(lyrics), len(tracks)))

    if args.output:
        with open(args.output, "w") as f:
            json.dump(list(lyrics), f)
    else:
        print(json.dumps(list(lyrics), indent=2))


if __name__ == "__main__":
    main()

