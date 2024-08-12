import msgpack
from gensim.models import KeyedVectors, Word2Vec
from gensim.models.callbacks import CallbackAny2Vec

from dss_selc.utils import PRJ_PATH

with open(PRJ_PATH / "dss-selc-dump/glove/processed_corpus.msgpack", "rb") as f:
    corpus = msgpack.load(f)


glove_vectors = KeyedVectors.load_word2vec_format(
    fname=PRJ_PATH.parent / ".models/glove/glove.840B.300d.txt",
    binary=False,
    no_header=True,
)

base_model = Word2Vec(vector_size=300, min_count=5, epochs=30, workers=12)
base_model.build_vocab(corpus)
total_examples = base_model.corpus_count

base_model.build_vocab(list(glove_vectors.key_to_index.keys()), update=True)


class callback(CallbackAny2Vec):
    """Callback to print loss after each epoch."""

    def __init__(self) -> None:
        self.epoch = 0
        self.loss_to_be_subed = 0

    def on_epoch_end(self, model: object) -> None:
        loss = model.get_latest_training_loss()
        loss_now = loss - self.loss_to_be_subed
        self.loss_to_be_subed = loss
        print(f"Loss after epoch {self.epoch:>02}: {loss_now:>010}")
        self.epoch += 1


base_model.train(
    corpus,
    total_examples=total_examples,
    epochs=base_model.epochs,
    compute_loss=True,
    callbacks=[callback()],
)
base_model_wv = base_model.wv

dr = PRJ_PATH / "dss-selc-dump/glove/model_01/"
dr.mkdir(exist_ok=True, parents=True)
base_model.save(str(dr) + "/base_model.model")
