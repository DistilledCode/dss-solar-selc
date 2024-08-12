import json
from typing import Any, Iterable

import requests
from spacy_llm.registry import registry

SYS_PROMPT = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
<|eot_id|><|start_header_id|>user<|end_header_id|>
{prompt}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""


def get_answers(
    prompts: list[str],
    url: str,
    config: dict[str, Any],
) -> list[str]:
    result = []
    for prompt in prompts:
        payload = {
            "prompt": SYS_PROMPT.format(prompt=prompt),
            "dynatemp_range": 0.00,
            "cache_prompt": True,
            **config,
        }
        response = requests.post(
            url,
            data=json.dumps(payload),
        )
        result.append(response.json()["content"])
    return result


@registry.llm_models("CustomRESTModel.v1")
def custom_rest_model(url: str, config: dict[str, Any]) -> callable:
    def query_llm(prompts: Iterable[Iterable[str]]) -> Iterable[Iterable[str]]:
        result = []
        for prompts_for_doc in prompts:
            answers_for_doc = get_answers(prompts_for_doc, url, config)
            result.append(answers_for_doc)
        return result

    return query_llm
