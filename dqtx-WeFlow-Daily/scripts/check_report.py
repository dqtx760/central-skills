from pathlib import Path
from html.parser import HTMLParser
import argparse, collections, json, re

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images, self.text = [], [], [], []
        self.hidden = 0
        self.clouds = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'span' and 'cloud-word' in a.get('class', '').split():
            self.clouds.append(a)
        if tag in ('script', 'style'):
            self.hidden += 1
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.links.append(a['href'][1:])
        if tag == 'img':
            self.images.append((a.get('src'), a.get('referrerpolicy'), a.get('data-source')))
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden-1)
    def handle_data(self, data):
        if not self.hidden:
            self.text.append(data)

def check(path):
    baseline = (Path(__file__).resolve().parents[1]/'assets/daily-template.html').read_text(encoding='utf-8')
    output = Path(path).read_text(encoding='utf-8')
    errors = []
    for tag in ('style', 'script'):
        pattern = rf'<{tag}\b[^>]*>(.*?)</{tag}>'
        if re.findall(pattern, baseline, re.S) != re.findall(pattern, output, re.S):
            errors.append(f'{tag} changed from fixed template')
    original, page = Page(), Page()
    original.feed(baseline)
    page.feed(output)
    heading = re.search(r'<h1\b[^>]*>(.*?)</h1>', output, re.S | re.I)
    if not heading or '日报' not in re.sub(r'<[^>]+>', '', heading.group(1)):
        errors.append('First h1 must include 群聊日报')
    for item in page.clouds:
        if item.get('data-weight') not in ('1','2','3','4','5'):
            errors.append('Cloud word must have data-weight 1–5')
        if item.get('data-tone') not in ('0','1','2','3','4','5','6'):
            errors.append('Cloud word must have data-tone 0–6')
        if 'style' in item:
            errors.append('Cloud words must not override fixed styles')
    if page.clouds and sum(x.get('data-weight') == '5' for x in page.clouds) != 1:
        errors.append('Word cloud must have exactly one dominant keyword')
    if collections.Counter(original.images) != collections.Counter(page.images):
        errors.append('QR image addresses or referrerpolicy changed')
    required = ('qr-wechat-open','qr-donation-open','theme-light','top','page','back-to-top','generic-qr-modal','donation-modal','sec-producer')
    for item in required:
        if item in original.ids and item not in page.ids:
            errors.append(f'Missing interaction id: {item}')
    for item, count in collections.Counter(page.ids).items():
        if count > 1:
            errors.append(f'Duplicate id: {item}')
    for target in page.links:
        if target and target not in page.ids:
            errors.append(f'Missing anchor target: {target}')
    placeholders = set(re.findall(r'\[[^\]\n]{1,50}\]', '\n'.join(original.text)))
    remaining = sorted(x for x in placeholders if x in '\n'.join(page.text))
    if remaining:
        errors.append('Unfilled placeholders: '+', '.join(remaining))
    if '<!doctype html>' not in output.lower() or '</html>' not in output.lower():
        errors.append('Incomplete HTML document')
    return {'ok': not errors, 'errors': errors}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('html')
    args = parser.parse_args()
    result = check(args.html)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['ok'] else 1)
