from random import shuffle

import msgpack
import spacy

from dss_selc.utils import PRJ_PATH

nlp = spacy.load("en_core_web_lg")

with open(PRJ_PATH / "dss-selc-dump/glove/corpus.txt", "r") as f:
    corpus = f.readlines()
print(len(corpus), "docs loaded")


def dump_corpus(new_corpus: list) -> None:
    fp = PRJ_PATH / "dss-selc-dump/glove/processed_corpus.msgpack"
    with open(fp, "wb") as f:
        msgpack.dump(new_corpus, f)


new_corpus = []
n_ = len(corpus)
for indx, doc_ in enumerate(corpus, start=1):
    new_doc = []
    doc = nlp(doc_)
    print(f"\r[*] Processing: {indx:>07}/{n_:>07}, ", end="")
    for sentence in doc.sents:
        for token in sentence:
            if token.is_punct is True or token.is_stop is True:
                continue
            new_doc.append(str(token.lemma_).lower())
    print(f"added {len(new_doc):>03} tokens.", " " * 20, end="")
    new_corpus.append(new_doc)
    if indx % 10_000 == 0:
        dump_corpus(new_corpus)

print("\nShuffling data..")
shuffle(new_corpus)

print("\nSaving data..")
dump_corpus(new_corpus)
