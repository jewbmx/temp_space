# -*- coding: UTF-8 -*-

import re
import base64

from six import ensure_text
from six.moves.urllib_parse import parse_qs, urlparse, urlencode

from resources.lib.modules import client
from resources.lib.modules import cleantitle
from resources.lib.modules import source_utils
from resources.lib.modules import log_utils
from resources.lib.modules import scrape_sources


class source:
    def __init__(self):
        try:
            self.results = []
            self.domains = ['fast32.com'] # kat.mn  putlockerfree.net  putlockers.fm
            self.base_link = 'https://fast32.com'
            self.search_link = '/search-movies/%s.html'
        except Exception:
            #log_utils.log('__init__', 1)
            return


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'title': title, 'year': year}
            url = urlencode(url)
            return url
        except:
            #log_utils.log('movie', 1)
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'tvshowtitle': tvshowtitle, 'year': year}
            url = urlencode(url)
            return url
        except:
            #log_utils.log('tvshow', 1)
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url is None:
                return
            url = parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urlencode(url)
            return url
        except:
            #log_utils.log('episode', 1)
            return


    def sources(self, url, hostDict):
        try:
            if url is None:
                return self.results
            data = parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            title = cleantitle.geturl(title)
            year = data['premiered'].split('-')[0] if 'tvshowtitle' in data else data['year']
            query1 = '%s-season-%s' % (title, data['season']) if 'tvshowtitle' in data else title
            query2 = '%s-%s-season-%s' % (title, year, data['season']) if 'tvshowtitle' in data else '%s-%s' % (title, year)
            check1 = cleantitle.get(query1)
            check2 = cleantitle.get(query2)
            url = self.base_link + self.search_link % (query1.replace('-', '%20'))
            html = client.scrapePage(url).text
            results = client.parseDOM(html, 'div', attrs={'class': 'itemInfo'})
            results = [(client.parseDOM(i, 'a', ret='href')[0], client.parseDOM(i, 'a')[0], re.findall('(\d{4})', i)[0]) for i in results]
            #results = [(i[0][0], i[1][0], i[2][0]) for i in results if len(i[0]) > 0 and len(i[1]) > 0 and len(i[2]) > 0]
            try:
                url = [i[0] for i in results if check1 == cleantitle.get(i[1]) and year == i[2]][0]
            except:
                url = [i[0] for i in results if check2 == cleantitle.get(i[1]) and year == i[2]][0]
            if 'tvshowtitle' in data:
                sepi = 'season-%1d/episode-%1d.html' % (int(data['season']), int(data['episode']))
                data = client.scrapePage(url).text
                link = client.parseDOM(data, 'a', ret='href')
                url = [i for i in link if sepi in i][0]
            r = client.scrapePage(url).text
            try:
                v = re.findall(r'document.write\(Base64.decode\("(.+?)"\)', r)[0]
                b64 = base64.b64decode(v)
                b64 = ensure_text(b64, errors='ignore')
                link = client.parseDOM(b64, 'iframe', ret='src')[0]
                link = link.replace('\/', '/').replace('///', '//')
                host = re.findall('([\w]+[.][\w]+)$', urlparse(link.strip().lower()).netloc)[0]
                host = client.replaceHTMLCodes(host)
                valid, host = source_utils.is_host_valid(host, hostDict)
                if valid:
                    self.results.append({'source': host, 'quality': 'SD', 'url': link, 'direct': False})
            except:
                #log_utils.log('sources', 1)
                pass
            try:
                r = client.parseDOM(r, 'div', {'class': 'server_line'})
                r = [(client.parseDOM(i, 'a', ret='href')[0], client.parseDOM(i, 'p', attrs={'class': 'server_servername'})[0]) for i in r]
                if r:
                    for i in r:
                        host = re.sub('Server|Link\s*\d+', '', i[1]).lower()
                        host = client.replaceHTMLCodes(host)
                        if 'other' in host:
                            continue
                        if host in str(self.results):
                            continue
                        link = i[0].replace('\/', '/').replace('///', '//')
                        valid, host = source_utils.is_host_valid(host, hostDict)
                        if valid:
                            self.results.append({'source': host, 'quality': 'SD', 'url': link, 'direct': False})
            except:
                #log_utils.log('sources', 1)
                pass
            return self.results
        except:
            #log_utils.log('sources', 1)
            return self.results


    def resolve(self, url):
        if any(x in url for x in self.domains):
            try:
                r = client.scrapePage(url).text
                try:
                    v = re.findall(r'document.write\(Base64.decode\("(.+?)"\)', r)[0]
                    b64 = base64.b64decode(v)
                    b64 = ensure_text(b64, errors='ignore')
                    try:
                        url = client.parseDOM(b64, 'iframe', ret='src')[0]
                    except:
                        url = client.parseDOM(b64, 'a', ret='href')[0]
                except:
                    u = client.parseDOM(r, 'div', attrs={'class': 'player'})
                    url = client.parseDOM(u, 'a', ret='href')[0]
                url = url.replace('\/', '/').replace('///', '//')
            except:
                #log_utils.log('resolve', 1)
                pass
            return url
        else:
            return url


