import wikipediaapi
import requests
import mwparserfromhell
from difflib import get_close_matches
import unicodedata
import logging
from typing import Optional, Dict, Any, List

class WikipediaPersonCollector:
    def get_politician_info(self, name: str):
        """
        Compatibility method for legacy enrichment pipeline.
        Returns an object with .url, .summary, .image_url attributes if found, else None.
        """
        result = self.get_info(name)
        if not result or result.get('error'):
            return None
        # Create a simple object with .url, .summary, .image_url for compatibility
        class WikipediaResult:
            def __init__(self, url, summary, image_url):
                self.url = url
                self.summary = summary
                self.image_url = image_url
        return WikipediaResult(
            result.get('wikipedia_url', ''),
            result.get('wikipedia_summary', ''),
            result.get('wikipedia_image_url', '')
        )


    """
    Bulletproof Wikipedia collector for Finnish politicians.
    Input: canonical full name (str)
    Output: dict with wikipedia_url, wikipedia_summary, wikipedia_image_url, etc.
    Handles all fallbacks, logs every step, and never fails silently.
    """
    def __init__(self, user_agent: str = None):
        self.logger = logging.getLogger("wikipedia_person_collector")
        if not self.logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.user_agent = user_agent or "FinnishPoliticianAnalysisBot/1.0 (shaikat1993@gmail.com)"
        self.wiki_fi = wikipediaapi.Wikipedia(language='fi', user_agent=self.user_agent)
        self.wiki_en = wikipediaapi.Wikipedia(language='en', user_agent=self.user_agent)

    def get_info(self, name: str) -> Dict[str, Any]:
        self.logger.info(f"[LOOKUP] Starting Wikipedia lookup for: {name}")
        tried = []
        # 1. Finnish Wikipedia strategies
        page = self._try_all_strategies(self.wiki_fi, name, 'fi', tried)
        # 2. English Wikipedia if not found
        if not page:
            page = self._try_all_strategies(self.wiki_en, name, 'en', tried)
        # 3. Wikidata fallback
        if not page:
            page = self._wikidata_fallback(name, tried)
        # 4. If still not found, return error
        if not page or not page.exists():
            error_msg = f"No Wikipedia page found for: {name}. Tried: {tried}"
            self.logger.error(error_msg)
            return {'error': error_msg, 'wikipedia_url': '', 'wikipedia_summary': '', 'wikipedia_image_url': '', 'wikipedia_lang': '', 'wikipedia_pageid': '', 'wikipedia_raw_infobox': {}}
        # Extract info
        summary = page.summary or ''
        url = page.fullurl
        image_url = self._get_image_url(page)
        infobox = self._parse_infobox(page.text)
        lang = page.language
        pageid = getattr(page, 'pageid', '')
        self.logger.info(f"[SUCCESS] Found Wikipedia page for {name}: {url}")
        return {
            'wikipedia_url': url,
            'wikipedia_summary': summary,
            'wikipedia_image_url': image_url,
            'wikipedia_lang': lang,
            'wikipedia_pageid': pageid,
            'wikipedia_raw_infobox': infobox,
            'error': ''
        }

    def _try_all_strategies(self, wiki, name, lang, tried):
        # Try exact
        tried.append(f"exact:{name}:{lang}")
        page = wiki.page(name)
        if page.exists():
            return page
        # Normalized
        norm = self._normalize_name(name)
        if norm != name:
            tried.append(f"norm:{norm}:{lang}")
            page = wiki.page(norm)
            if page.exists():
                return page
        # First + last only
        tokens = name.split()
        if len(tokens) > 2:
            simple = f"{tokens[0]} {tokens[-1]}"
            tried.append(f"simple:{simple}:{lang}")
            page = wiki.page(simple)
            if page.exists():
                return page
        # Last only if unique
        if len(tokens) > 1:
            last = tokens[-1]
            tried.append(f"last:{last}:{lang}")
            page = wiki.page(last)
            if page.exists():
                return page
        # Fuzzy match in MP category
        try:
            if lang == 'fi':
                cat = wiki.page("Luokka:Suomen kansanedustajat")
            else:
                cat = wiki.page("Category:Members of the Parliament of Finland")
            if cat.exists():
                candidates = [m.title for m in cat.categorymembers.values() if m.ns == 0]
                match = get_close_matches(name, candidates, n=1, cutoff=0.75)
                if match:
                    tried.append(f"fuzzy:{match[0]}:{lang}")
                    page = wiki.page(match[0])
                    if page.exists():
                        return page
        except Exception as e:
            self.logger.warning(f"Fuzzy search failed ({lang}): {e}")
        return None

    def _wikidata_fallback(self, name, tried):
        try:
            url = f'https://www.wikidata.org/w/api.php?action=wbsearchentities&search={requests.utils.quote(name)}&language=fi&format=json&type=item'
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('search'):
                    entity = data['search'][0]
                    qid = entity['id']
                    # Get sitelinks for fi/enwiki
                    url2 = f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json'
                    r2 = requests.get(url2, timeout=5)
                    if r2.status_code == 200:
                        d2 = r2.json()
                        sitelinks = d2['entities'][qid]['sitelinks']
                        for key in ['fiwiki', 'enwiki']:
                            if key in sitelinks:
                                title = sitelinks[key]['title']
                                lang = 'fi' if key == 'fiwiki' else 'en'
                                wiki = self.wiki_fi if lang == 'fi' else self.wiki_en
                                tried.append(f"wikidata:{title}:{lang}")
                                page = wiki.page(title)
                                if page.exists():
                                    return page
        except Exception as e:
            self.logger.warning(f"Wikidata fallback failed: {e}")
        return None

    def _normalize_name(self, name):
        return unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

    def _parse_infobox(self, text: str) -> Dict[str, Any]:
        try:
            wikicode = mwparserfromhell.parse(text)
            templates = [t for t in wikicode.filter_templates() if "Infobox" in t.name.lower()]
            infobox = {}
            if templates:
                t = templates[0]
                for param in t.params:
                    pname = str(param.name).strip().lower()
                    pval = str(param.value).strip()
                    infobox[pname] = pval
            return infobox
        except Exception as e:
            self.logger.warning(f"Infobox parsing failed: {e}")
            return {}

    def _get_image_url(self, page) -> Optional[str]:
        # 1. Try Wikidata (P18 property)
        if hasattr(page, 'wikibase') and page.wikibase:
            wikidata_url = f'https://www.wikidata.org/wiki/Special:EntityData/{page.wikibase}.json'
            try:
                r = requests.get(wikidata_url, timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    entity = data['entities'][page.wikibase]
                    claims = entity.get('claims', {})
                    if 'P18' in claims:
                        image_name = claims['P18'][0]['mainsnak']['datavalue']['value']
                        from urllib.parse import quote
                        image_url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{quote(image_name)}'
                        return image_url
            except Exception as e:
                self.logger.warning(f"Wikidata image fetch failed: {e}")
        # 2. Fallback: Wikipedia API 'pageimages'
        try:
            api_url = (
                f"https://{page.language}.wikipedia.org/w/api.php?action=query&titles="
                f"{requests.utils.quote(page.title)}&prop=pageimages&format=json&pithumbsize=500"
            )
            resp = requests.get(api_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                pages = data.get('query', {}).get('pages', {})
                for p in pages.values():
                    if 'thumbnail' in p and 'source' in p['thumbnail']:
                        return p['thumbnail']['source']
        except Exception as e:
            self.logger.warning(f"Wikipedia API image fetch failed: {e}")
        return None

if __name__ == "__main__":
    import sys
    name = " ".join(sys.argv[1:])
    collector = WikipediaPersonCollector()
    result = collector.get_info(name)
    print("\nRESULT:")
    for k, v in result.items():
        print(f"{k}: {v}")
