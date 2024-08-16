import html
from textractor.data.html_linearization_config import HTMLLinearizationConfig

def add_id_to_html_tag(prefix, id, config):
    if not isinstance(config, HTMLLinearizationConfig) or not prefix:
        return prefix
    if config.add_ids_to_html_tags:
        return prefix[:-1] + f' id="{id[:8]}"' + prefix[-1]
    elif config.add_short_ids_to_html_tags:
        return prefix[:-1] + f' id="{id}"' + prefix[-1]
    else:
        return prefix

def escape_text(text, config):
    if not isinstance(config, HTMLLinearizationConfig):
        return text
    else:
        return html.escape(text)
