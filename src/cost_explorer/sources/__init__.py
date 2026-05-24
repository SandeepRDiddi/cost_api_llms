from cost_explorer.sources.anthropic import AnthropicSource
from cost_explorer.sources.cohere import CohereSource
from cost_explorer.sources.google import GoogleSource
from cost_explorer.sources.mistral import MistralSource
from cost_explorer.sources.openai import OpenAISource
from cost_explorer.sources.xai import XAISource


def get_sources():
    return [
        OpenAISource(),
        AnthropicSource(),
        GoogleSource(),
        MistralSource(),
        CohereSource(),
        XAISource(),
    ]
