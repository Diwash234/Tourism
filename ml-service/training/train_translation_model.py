"""
training/train_translation_model.py

Fine-tunes a Nepali<->English translation model
(starting point: Helsinki-NLP/opus-mt-en-ne) on a parallel corpus.

NOT RUN YET in this deliverable: it needs a real parallel corpus in
data/languages/ne-en.tsv (the file currently there is a ~10-phrase
starter dictionary for the rule-based fallback, not training data) and
transformers/sentencepiece installed. translation_engine.py already
uses that small dictionary directly and will pick up a fine-tuned model
here automatically once you save one to model/translation/model/.

Run once you have a real corpus (thousands of aligned sentence pairs):
    pip install transformers sentencepiece datasets
    python training/train_translation_model.py
"""
import os
import csv
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    DataCollatorForSeq2Seq,
)

CORPUS_PATH = "data/languages/ne-en.tsv"
BASE_MODEL = "Helsinki-NLP/opus-mt-en-ne"
MODEL_OUT_DIR = "model/translation/model"


def load_pairs():
    pairs = []
    with open(CORPUS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) >= 2:
                pairs.append({"ne": row[0].strip(), "en": row[1].strip()})
    return pairs


def main():
    pairs = load_pairs()
    if len(pairs) < 500:
        print(
            f"Only {len(pairs)} phrase pairs in {CORPUS_PATH} - that's a "
            "fallback dictionary, not enough to fine-tune on. Add a real "
            "parallel corpus (thousands of sentence pairs) before running this."
        )
        return

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)

    dataset = Dataset.from_list(pairs)

    def preprocess(batch):
        inputs = tokenizer(batch["en"], truncation=True, padding="max_length", max_length=64)
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(batch["ne"], truncation=True, padding="max_length", max_length=64)
        inputs["labels"] = labels["input_ids"]
        return inputs

    tokenized = dataset.map(preprocess, batched=True)

    args = Seq2SeqTrainingArguments(
        output_dir=MODEL_OUT_DIR,
        per_device_train_batch_size=8,
        num_train_epochs=3,
        save_strategy="epoch",
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=tokenized,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )
    trainer.train()

    os.makedirs(MODEL_OUT_DIR, exist_ok=True)
    model.save_pretrained(MODEL_OUT_DIR)
    tokenizer.save_pretrained(MODEL_OUT_DIR)
    print(f"Saved fine-tuned translation model to {MODEL_OUT_DIR}")


if __name__ == "__main__":
    main()