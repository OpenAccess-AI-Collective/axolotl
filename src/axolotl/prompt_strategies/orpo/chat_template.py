"""chatml prompt tokenization strategy for ORPO"""
from typing import Any, Dict, Generator, List, Optional, Tuple

from pydantic import BaseModel

from axolotl.prompt_tokenizers import IGNORE_INDEX, PromptTokenizingStrategy
from axolotl.prompters import Prompter
from axolotl.utils.chat_templates import chat_templates


class Message(BaseModel):
    """message/turn"""

    role: str
    content: str
    label: Optional[bool] = None


class MessageList(BaseModel):
    """conversation"""

    messages: List[Message]


def load(
    tokenizer, cfg, ds_cfg: Optional[Dict[str, Any]] = None, **kwargs
):  # pylint: disable=possibly-unused-variable,unused-argument
    """
    chatml transforms for datasets with system, input, chosen, rejected
    """

    chat_template = chat_templates("chatml", system_message=cfg.default_system_message)
    if ds_cfg and "chat_template" in ds_cfg:
        chat_template = ds_cfg["chat_template"]
        try:
            chat_template = chat_templates(
                chat_template, system_message=cfg.default_system_message
            )
        except ValueError:
            pass

    return ORPOTokenizingStrategy(
        ORPOPrompter(chat_template, tokenizer),
        tokenizer,
        cfg.train_on_inputs,
        cfg.sequence_len,
    )


class ORPOTokenizingStrategy(PromptTokenizingStrategy):
    """
    rejected_input_ids
    input_ids
    rejected_attention_mask
    attention_mask
    rejected_labels
    labels
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

    def get_chosen_conversation_thread(self, prompt) -> MessageList:
        """Dataset structure mappings"""

        messages: List[Message] = []
        if system := prompt.get("system", None):
            messages.append(Message(role="system", content=system, label=False))
        else:
            messages.append(Message(role="system", content="", label=False))
        messages.append(Message(role="user", content=prompt["prompt"], label=False))
        messages.append(
            Message(
                role="assistant", content=prompt["chosen"][1]["content"], label=True
            )
        )
        return MessageList(messages=messages)

    def get_rejected_conversation_thread(self, prompt) -> MessageList:
        """Dataset structure mappings"""

        messages: List[Message] = []
        if system := prompt.get("system", None):
            messages.append(Message(role="system", content=system, label=False))
        else:
            messages.append(Message(role="system", content="", label=False))

        messages.append(Message(role="user", content=prompt["prompt"], label=False))
        messages.append(
            Message(
                role="assistant", content=prompt["rejected"][1]["content"], label=True
            )
        )
        return MessageList(messages=messages)

    def tokenize_prompt(self, prompt):
        # pass the rejected prompt/row to the Prompter to get the formatted prompt
        prompt_len = 0
        rejected_message_list = self.get_rejected_conversation_thread(prompt)
        input_ids = []
        labels = []
        for _, (part, label) in enumerate(
            self.prompter.build_prompt(rejected_message_list)
        ):
            if not part:
                continue
            _input_ids = self.tokenizer.encode(part, add_special_tokens=False)
            prev_idx = len(input_ids)
            input_ids += _input_ids[prev_idx:]
            if label:
                labels += input_ids[prev_idx:]
            else:
                labels += [IGNORE_INDEX] * (len(input_ids) - prev_idx)
                prompt_len = len(input_ids)
        # remap the input_ids, attention_mask and labels
        rejected_input_ids = input_ids
        rejected_labels = labels
        # pass the chosen prompt/row to the Prompter to get the formatted prompt
        chosen_message_list = self.get_chosen_conversation_thread(prompt)
        input_ids = []
        labels = []
        for _, (part, label) in enumerate(
            self.prompter.build_prompt(chosen_message_list)
        ):
            if not part:
                continue
            _input_ids = self.tokenizer.encode(part, add_special_tokens=False)
            prev_idx = len(input_ids)
            input_ids += _input_ids[prev_idx:]
            if label:
                labels += input_ids[prev_idx:]
            else:
                labels += [IGNORE_INDEX] * (len(input_ids) - prev_idx)

        return {
            "rejected_input_ids": rejected_input_ids,
            "rejected_labels": rejected_labels,
            "rejected_attention_mask": [1] * len(rejected_labels),
            "input_ids": input_ids,
            "labels": labels,
            "attention_mask": [1] * len(labels),
            "prompt_attention_mask": [1] * prompt_len
            + [0] * (len(labels) - prompt_len),
        }


class ORPOPrompter(Prompter):
    """Single Turn prompter for ORPO"""

    def __init__(self, chat_template, tokenizer):
        self.chat_template = chat_template
        self.tokenizer = tokenizer

    def build_prompt(
        self,
        message_list: MessageList,
    ) -> Generator[Tuple[str, bool], None, None]:
        conversation = []
        for message in message_list.messages:
            conversation.append(message.model_dump())
            if message.role == "system":
                yield self.tokenizer.apply_chat_template(
                    conversation,
                    add_generation_prompt=False,
                    chat_template=self.chat_template,
                    tokenize=False,
                ), False
            if message.role == "user":
                yield self.tokenizer.apply_chat_template(
                    conversation,
                    add_generation_prompt=True,
                    chat_template=self.chat_template,
                    tokenize=False,
                ), False
            if message.role == "assistant":
                yield self.tokenizer.apply_chat_template(
                    conversation,
                    add_generation_prompt=False,
                    chat_template=self.chat_template,
                    tokenize=False,
                ), True
