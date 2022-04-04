import argparse
import logging
import os
import re
from itertools import chain
from multiprocessing import Process
from random import shuffle
from typing import Any, Dict, List

import kss
import ujson as json
from namuwiki.extractor import extract_text
from tqdm import tqdm

cleaning_first_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in [r"~~[^~]+~~"]]
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

    return text.strip()


def process(proc_id: int, docs: List[Dict[str, Any]], output_dir: str):
    # KSS에서 Too long text 관련 warning이 너무 많이 출력되어 logging disable
    logging.disable(logging.ERROR)

    file = open(os.path.join(output_dir, f"namuwiki_{proc_id:02d}.txt"), "w", encoding="utf-8")
    is_first = True

    for doc in tqdm(docs, disable=(proc_id != 0)):
        title = clean_text(doc["title"])
        body = clean_text(doc["text"])

        if len(body) < 20 or len(title) == 0:
            continue
        else:
            try:
                # sentence 분절
                sentences = body.split("\n")
                sentences = kss.split_sentences(
                    sentences,
                    backend="mecab",
                    max_recover_step=3,
                    max_recover_length=3000,
                    num_workers=0,
                )
                # list of list를 list로 변환
                sentences = chain(*sentences)
                # 각 문장별로 중복 스페이스 제거
                sentences = [" ".join(sentence.split()) for sentence in sentences]
                sentences = "\n".join(sentences)

                if len(sentences) == 0:
                    continue

                if is_first:
                    file.write(f"{title}\n{sentences}\n")
                    is_first = False
                else:
                    file.write(f"\n{title}\n{sentences}\n")
            except Exception:
                continue

    file.close()


def get_argparser():
    """Build the argument parser for main."""
    parser = argparse.ArgumentParser(description="WikiExtractor")
    parser.add_argument("--dump-path", type=str, required=True, help="나무위키 json 파일 경로")
    parser.add_argument("--output-dir", type=str, required=True, help="저장할 폴더 경로")
    parser.add_argument("--num-workers", type=int, default=40)
    return parser


if __name__ == "__main__":
    """
    python3 NamuwikiExtractor.py --dump-path "./나무위키/docData200302.json" --output-dir "."
    """
    parser = get_argparser()
    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.dump_path) as f:
        namuwiki_documents = json.load(f)

    print(f"Total documents: {len(namuwiki_documents)}")

    # 각 워커별로 텍스트 총 길이를 기준으로 고르게 분배
    chunks = [[[], 0] for _ in range(args.num_workers)]
    namuwiki_documents = sorted(namuwiki_documents, key=lambda x: len(x["text"]), reverse=True)
    for document in namuwiki_documents:
        chunks[0][0].append(document)
        chunks[0][1] += len(document["text"])

        chunks = sorted(chunks, key=lambda x: x[1])

    for i, (chunk, total_num_characters) in enumerate(chunks):
        print(f"{i}th worker - {len(chunk)}, {total_num_characters}")

    del namuwiki_documents
    chunks = [chunk for chunk, _ in chunks]
    for i in range(len(chunks)):
        shuffle(chunks[i])

    processes = []
    for i in range(args.num_workers):
        processes.append(Process(target=process, args=(i, chunks[i], args.output_dir)))

    for proc in processes:
        proc.start()

    for proc in processes:
        proc.join()
