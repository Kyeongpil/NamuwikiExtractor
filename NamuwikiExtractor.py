import argparse
import os
import random
import re
from multiprocessing import Lock, Process, Value
from typing import Any, Dict, List

import kss
import ujson as json
from namuwiki.extractor import extract_text
from tqdm import tqdm

capture_values = (("item.namespace", "string"), ("item.title", "string"), ("item.text", "string"))
cleaning_first_patterns = [r"~~[^~]+~~"]
cleaning_first_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in cleaning_first_patterns]
cleaning_patterns = [r"\([^\)]+\)", r"/^#[0-9a-f]{3,6}$/i"]
cleaning_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in cleaning_patterns]
replace_patterns = {"\\n": "\n", "\\'": "'"}


def clean_text(text: str) -> str:
    for regex in cleaning_first_patterns:
        text = re.sub(regex, "", text)

    text = extract_text(text)

    for regex in cleaning_patterns:
        text = re.sub(regex, "", text)
    for k, v in replace_patterns:
        text = text.replace(k, v)

    return text


def process(
    proc_id: int,
    docs: List[Dict[str, Any]],
    output_dir: str,
    lock: Lock,
    total_invalid_documents: Value,
):
    file = open(os.path.join(output_dir, f"namuwiki_{proc_id:02d}.txt"), "w", encoding="utf-8")
    is_first = True

    for doc in tqdm(docs, disable=(proc_id != 0)):
        doc["title"] = clean_text(doc["title"])
        doc["text"] = clean_text(doc["text"])
        doc["text"] = doc["text"].replace("\n\n", "\n")

        if len(doc["text"]) < 20:
            with lock:
                total_invalid_documents.value += 1
            continue
        else:
            try:
                # sentence 분절
                sentences = kss.split_sentences(doc["text"], num_workers=0, backend="mecab", max_recover_length=100000)
                sentences = [" ".join(sentence.replace("\n", " ").split(" ")) for sentence in sentences]
                doc["text"] = "\n".join(sentences).strip()
            except Exception as e:
                print(e)
                with lock:
                    total_invalid_documents.value += 1
                continue

        if is_first:
            file.write(f"{doc['title']}\n{doc['text']}\n")
            is_first = False
        else:
            file.write(f"\n{doc['title']}\n{doc['text']}\n")

    file.close()


def get_argparser():
    """Build the argument parser for main."""
    parser = argparse.ArgumentParser(description="WikiExtractor")
    parser.add_argument("--dump-path", type=str, required=True, help="나무위키 json 파일 경로")
    parser.add_argument("--output-dir", type=str, required=True, help="저장할 폴더 경로")
    parser.add_argument("--num-workers", type=int, default=20)
    return parser


if __name__ == "__main__":
    """
    python3 NamuwikiExtractor.py --dump_path "./나무위키/docData200302.json" --output_file "./namuwiki.txt"
    """
    parser = get_argparser()
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.dump_path) as f:
        namuwiki_documents = json.load(f)

    random.seed(0)
    random.shuffle(namuwiki_documents)
    print(f"Total documents: {len(namuwiki_documents)}")

    lock = Lock()
    total_processed_documents = Value("i")
    total_invalid_documents = Value("i")

    processes = []
    for i in range(args.num_workers):
        processes.append(
            Process(
                target=process,
                args=(
                    i,
                    namuwiki_documents[i :: args.num_workers],
                    args.output_dir,
                    lock,
                    total_invalid_documents,
                ),
            )
        )

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()

    print(f"Total invalid documents: {total_invalid_documents.value}")
