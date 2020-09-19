from typing import Dict, List


def tag_list_to_dict(tag_list: List[str]) -> Dict[str, str]:
    return {'tags[{}]'.format(i): v for i, v in enumerate(tag_list)}
