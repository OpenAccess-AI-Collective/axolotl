"""Axolotl CLI option group definitions"""

import inspect
from typing import Callable

from axolotl.cli import options
from axolotl.utils.config import option_group_factory


def model_option_group(**kwargs) -> Callable:
    """
    Group of options for model configuration
    """

    return option_group_factory(
        options=[
            options.base_model_option,
            options.base_model_config_option,
            options.model_type_option,
            options.tokenizer_type_option,
            options.tokenizer_config_option,
            options.trust_remote_code_option,
            options.tokenizer_use_fast_option,
            options.adapter_option,
            options.lora_model_dir_option,
            options.base_model_ignore_patterns_option,
            options.model_revision_option,
            options.load_in_8bit_option,
        ],
        **kwargs,
    )


def all_option_group(**kwargs) -> Callable:
    """
    Dynamic option group that contains all options
    """

    all_members = sorted(inspect.getmembers(options))
    callable_options = [
        member[1]
        for member in all_members
        if callable(member[1]) and member[0].endswith("_option")
    ]

    return option_group_factory(
        options=callable_options,
        **kwargs,
    )
