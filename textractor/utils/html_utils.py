from textractor.data.constants import HTMLLinearizationConfig

def add_id_to_html_tag(prefix, id, config, shorten=False):
    if not isinstance(config, HTMLLinearizationConfig):
        return prefix
    if shorten:
        return prefix[:-1] + f" id={id[:8]}" + prefix[-1]
    else:
        return prefix[:-1] + f" id={id}>" + prefix[-1]
