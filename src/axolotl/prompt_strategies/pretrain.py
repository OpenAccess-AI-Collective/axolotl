from typing import Generator

from transformers import BatchEncoding

from axolotl.prompt_tokenizers import PromptTokenizingStrategy


class PretrainTokenizer:
    def build_prompt(self, prompt) -> Generator[str, None, None]:
        yield prompt


class PretrainTokenizationStrategy(PromptTokenizingStrategy):
    def __init__(self, *args, max_length=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_length:
            self.max_length = max_length

    def _tokenize(
        self, prompt: str, add_eos_token: bool = True, strip_bos_token: bool = False
    ) -> BatchEncoding:
        res = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length - 1,
            add_special_tokens=True,
            return_overflowing_tokens=True,
            stride=256,
        )
        res["input_ids"] = [
            seq + [self.tokenizer.eos_token_id] for seq in res["input_ids"]
        ]
        res["attention_mask"] = [seq + [1] for seq in res["attention_mask"]]

        return res

    def tokenize_prompt(self, prompt):
        self._tokenize(prompt)


def load(tokenizer, cfg):
    strat = PretrainTokenizationStrategy(
        PretrainTokenizer(),
        tokenizer,
        cfg.train_on_inputs,
        cfg.sequence_len,
        max_length=cfg.sequence_len * 64,
    )
    return strat
