import os

import pandas as pd

from dss_selc.utils import PROXIES, USE_SOCKS

os.environ["HF_HOME"] = "/home/student/anurag/.models/hf"
os.environ["HF_HUB_CACHE"] = "/home/student/anurag/.models/hf/hub"

from datasets import Dataset  # noqa: E402
from transformers import get_linear_schedule_with_warmup  # noqa: F401, E402
from transformers import (  # noqa: E402
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)


def preprocess_function(examples: str) -> list:
    return tokenizer(examples["title"], truncation=True)


proxies = PROXIES if USE_SOCKS is True else None

MODEL_NAME = "microsoft/deberta-base"
MODEL_NAME = "distilbert-base-uncased"
data = Dataset.from_parquet(
    "./dss-selc-dump/classification/solar_classification_train.parquet"
)
data = Dataset.from_dict(data[:])
data = data.train_test_split(test_size=0.10, seed=42, shuffle=True)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, proxies=proxies)
tokenized_data = data.map(preprocess_function, batched=True)
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=1,
    proxies=proxies,
)

tokenized_data = tokenized_data.remove_columns(["title"])

num_epochs = 40
batch_size = 512
num_training_steps = (len(tokenized_data["train"]) / batch_size) * num_epochs
num_warmup_steps = int(0.15 * num_training_steps)
print(f"{num_training_steps=}\n{num_warmup_steps=}")
training_args = TrainingArguments(
    output_dir="./results",
    learning_rate=5e-7,
    per_device_train_batch_size=256,
    per_device_eval_batch_size=256,
    num_train_epochs=num_epochs,
    weight_decay=0.01,
    dataloader_num_workers=0,
    fp16=True,
    save_strategy="epoch",
    eval_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    lr_scheduler_type="linear",
    warmup_steps=num_warmup_steps,
    use_cpu=True,
    logging_strategy="epoch",
    optim="adamw_torch",
)
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_data["train"],
    eval_dataset=tokenized_data["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
)

print("\n\n")
print(" TRAINING BEGAN ".center(10, "="))
print("\n\n")

trainer.train()

output_dir = "./saved_model"
trainer.save_model(output_dir)
tokenizer.save_pretrained(output_dir)

pd.DataFrame(trainer.state.log_history[0::2]).to_parquet("./logs/train_log.parquet")
pd.DataFrame(trainer.state.log_history[1::2]).to_parquet("./logs/eval_log.parquet")
