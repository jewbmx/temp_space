# -*- coding: utf-8 -*-

"""
#########################################


This is a little note added to show the changes for this new module to be added in.
(Not included in the actual addon, just this temp file.)
[ Anyone feeling like testing this or helping out with the coding, contact me however for whatever lol. ]

### settings.xml changes...

        <setting id="trailer.source" type="enum" label="Trailers Source" values="TMDb|YouTube|IMDb|Trakt|Multi" default="2" />
		<setting id="trailers.tmdb" type="bool" label="Use TMDb" default="true" enable="!eq(-1,false)" subsetting="true" visible="eq(-1,4)" />
		<setting id="trailers.youtube" type="bool" label="Use YouTube" default="true" enable="!eq(-2,false)" subsetting="true" visible="eq(-2,4)" />
		<setting id="trailers.imdb" type="bool" label="Use IMDb" default="true" enable="!eq(-3,false)" subsetting="true" visible="eq(-3,4)" />
		<setting id="trailers.trakt" type="bool" label="Use Trakt" default="true" enable="!eq(-4,false)" subsetting="true" visible="eq(-4,4)" />
        <setting id="trailer.select" type="enum" label="Trailers Action" values="Auto Play|Select" default="1" />


### system.py changes...

    elif action == 'trailer':
        from resources.lib.modules import control
        if not control.condVisibility('System.HasAddon(plugin.video.youtube)'):
            control.installAddon('plugin.video.youtube')
        from resources.lib.modules import trailer
        trailer.source().get(name, url, tmdb, imdb, season, episode, windowedtrailer)
        ## Some Old Code Saved...
        #trailer_source = control.setting('trailer.source') or '2'
        #if trailer_source == '0':
            #trailer.TMDb_trailer().play(tmdb, imdb, season, episode, windowedtrailer)
        #elif trailer_source == '1':
            #trailer.YT_trailer().play(name, url, tmdb, imdb, season, episode, windowedtrailer)
        #else:
            #trailer.IMDb_trailer().play(imdb, name, tmdb, season, episode, windowedtrailer)


--Futher plans/goals are...
-(x)To cleanup the code. (Done but could always be redone lol.)
-(_)Maybe swap tmdb to my tmdb_utils trailer defs.
-(x)Maybe make all the search sources run then show a full list like ['(Trakt) Rampage Trailer', '(TMDb) Rampage Trailer']...
-(x)And if its not already done from whats listed above this, reduce the repeated code used when it could be used in one def and passed around.
-(_)Possible suicide due to this module and everything regarding youtube :)


#########################################
"""

import re
import sys
import random

import six
from six.moves.urllib_parse import quote_plus

from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control
from resources.lib.modules import log_utils
#from resources.lib.modules import tmdb_utils
from resources.lib.modules import trakt


try:
    #from infotagger.listitem import ListItemInfoTag
    from resources.lib.modules.listitem import ListItemInfoTag
except:
    pass

kodi_version = control.getKodiVersion()


class source:
    def __init__(self):
        self.list = []
        self.content = control.infoLabel('Container.Content')
        self.trailer_mode = control.setting('trailer.select') or '1'
        self.trailer_source = control.setting('trailer.source') or '2'

        self.trailers_tmdb = control.setting('trailers.tmdb') or 'true'
        self.trailers_youtube = control.setting('trailers.youtube') or 'true'
        self.trailers_imdb = control.setting('trailers.imdb') or 'true'
        self.trailers_trakt = control.setting('trailers.trakt') or 'true'

        self.youtube_link = 'https://youtube.com'
        self.youtube_watch_link = 'https://youtube.com/watch?v='
        #self.youtube_plugin_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
        self.youtube_plugin_url = 'plugin://plugin.video.youtube/play/?video_id='
        self.youtube_keys = ['AIzaSyCGfYB9l1K7E2H5jKrl5xk0MHTHtODBego', 'AIzaSyBnZOwDu5u5IjQ5xs5P04gR7oRXK-xfVRE']
        if control.condVisibility('System.HasAddon(plugin.video.youtube)'):
            self.youtube_key = control.addon('plugin.video.youtube').getSetting('youtube.api.key') or ''
        else:
            self.youtube_key = ''
        if not self.youtube_key:
            self.youtube_key = control.setting('youtube.api') or ''
        if not self.youtube_key:
            self.youtube_key = random.choice(self.youtube_keys)
        self.youtube_lang = control.apiLanguage().get('youtube', 'en') or 'en'
        self.youtube_lang_link = '' if self.youtube_lang == 'en' else '&relevanceLanguage=%s' % self.youtube_lang
        if self.trailer_mode == '0':
            self.youtube_search_link = 'https://www.googleapis.com/youtube/v3/search?part=id&type=video&maxResults=10&q=%s&key=%s%s' % ('%s', '%s', self.youtube_lang_link)
        else:
            self.youtube_search_link = 'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=10&q=%s&key=%s%s' % ('%s', '%s', self.youtube_lang_link)
        self.imdb_link = 'https://www.imdb.com/_json/video/'
        self.tmdb_key = control.setting('tmdb.api') or ''
        if not self.tmdb_key:
            self.tmdb_key = 'c8b7db701bac0b26edfcc93b39858972'
        self.tmdb_lang = control.apiLanguage().get('tmdb', 'en')
        self.tmdb_lang_link = 'en,null' if self.tmdb_lang == 'en' else 'en,%s,null' % self.tmdb_lang
        self.tmdb_movie_link = 'https://api.themoviedb.org/3/movie/%s/videos?api_key=%s&include_video_language=%s' % ('%s', self.tmdb_key, self.tmdb_lang_link)
        self.tmdb_show_link = 'https://api.themoviedb.org/3/tv/%s/videos?api_key=%s&include_video_language=%s' % ('%s', self.tmdb_key, self.tmdb_lang_link)
        self.tmdb_season_link = 'https://api.themoviedb.org/3/tv/%s/season/%s/videos?api_key=%s&include_video_language=%s' % ('%s', '%s', self.tmdb_key, self.tmdb_lang_link)
        self.tmdb_episode_link = 'https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s/videos?api_key=%s&include_video_language=%s' % ('%s', '%s', '%s', self.tmdb_key, self.tmdb_lang_link)


    def youtube_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        try:
            if self.content not in ['tvshows', 'seasons', 'episodes']:
                name += ' %s' % control.infoLabel('ListItem.Year')
            elif self.content in ['seasons', 'episodes']:
                if season and episode:
                    name += ' %sx%02d' % (season, int(episode))
                elif season:
                    name += ' season %01d' % int(season)
            if self.content != 'episodes':
                name += ' trailer'
            query = quote_plus(name)
            url = self.youtube_search_link % (query, self.youtube_key)
            result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                url = self.youtube_search_link % (query, self.youtube_keys[0])
                result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                url = self.youtube_search_link % (query, self.youtube_keys[1])
                result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                return []
            results = result['items']
            if not results:
                return []
            for i in results:
                self.list.append({'source': 'YouTube', 'title': i.get('snippet', {}).get('title', ''), 'url': i.get('id', {}).get('videoId', ''), 'type': 'Trailer'})
            return self.list
        except:
            log_utils.log('youtube_trailers', 1)
            return []


    def trakt_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        try:
            if not imdb or imdb == '0':
                return []
            if self.content not in ['tvshows', 'seasons', 'episodes']:
                results = trakt.getMovieSummary(imdb, full=True)
                if not results:
                    year = control.infoLabel('ListItem.Year')
                    try:
                        results = trakt.SearchMovie(name, year, full=True)
                        if results[0]['movie']['title'].lower() != name.lower() or int(results[0]['movie']['year']) != int(year):
                            raise Exception()
                        results = results[0].get('movie', {})
                    except:
                        results = {}
            else:
                results = trakt.getTVShowSummary(imdb, full=True)
                if not results:
                    year = control.infoLabel('ListItem.Year')
                    try:
                        results = trakt.SearchTVShow(name, year, full=True)
                        if results[0]['show']['title'].lower() != name.lower() or int(results[0]['show']['year']) != int(year):
                            raise Exception()
                        results = results[0].get('show', {})
                    except:
                        results = {}
            if not results:
                return []
            else:
                self.list.append({'source': 'Trakt', 'title': name, 'url': results.get('trailer', ''), 'type': 'Trailer'})
            return self.list
        except:
            log_utils.log('trakt_trailers', 1)
            return []


    def imdb_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        try:
            if not imdb or imdb == '0':
                return []
            link = self.imdb_link + imdb
            items = client.scrapePage(link, timeout='30').json()
            listItems = items['playlists'][imdb]['listItems']
            videoMetadata = items['videoMetadata']
            for item in listItems:
                try:
                    videoId = item['videoId']
                    metadata = videoMetadata[videoId]
                    title = metadata['title']
                    related_to = metadata.get('primaryConst') or imdb
                    if not related_to == imdb:
                        continue
                    videoUrl = [i['videoUrl'] for i in metadata['encodings'] if i['definition'] in ['1080p', '720p', '480p', '360p', 'SD']]
                    if not videoUrl:
                        continue
                    videoType = 'Trailer' if 'trailer' in title.lower() else 'N/A'
                    self.list.append({'source': 'IMDb', 'title': title, 'url': videoUrl[0], 'type': videoType})
                except:
                    pass
            return self.list
        except:
            log_utils.log('imdb_trailers', 1)
            return []


    def tmdb_trailers(self, name='', url='', tmdb='', imdb='', season='', episode=''):
        try:
            if not tmdb or tmdb == '0':
                return []
            t_url = self.tmdb_show_link % tmdb
            s_url = self.tmdb_season_link % (tmdb, season)
            if self.content == 'tvshows':
                api_url = t_url
            elif self.content == 'seasons':
                api_url = s_url
            elif self.content == 'episodes':
                api_url = self.tmdb_episode_link % (tmdb, season, episode)
            else:
                api_url = self.tmdb_movie_link % tmdb
            results = self.tmdb_results(api_url, t_url, s_url)
            if not results:
                return []
            for i in results:
                self.list.append({'source': 'TMDb', 'title': i.get('name', ''), 'url': i.get('key', ''), 'type': i.get('type', 'N/A')})
            return self.list
        except:
            log_utils.log('tmdb_trailers', 1)
            return []


    def tmdb_results(self, url, t_url, s_url):
        try:
            items = client.scrapePage(url, timeout='30').json()
            items = items['results']
            items = [r for r in items if r.get('site') == 'YouTube']
            results = [x for x in items if x.get('iso_639_1') == self.tmdb_lang]
            if not self.tmdb_lang == 'en':
                results += [x for x in items if x.get('iso_639_1') == 'en']
            results += [x for x in items if x.get('iso_639_1') not in set([self.tmdb_lang, 'en'])]
            if not results:
                if '/season/' in url and '/episode/' in url:
                    results = self.tmdb_results(s_url, t_url, None)
                elif '/season/' in url:
                    results = self.tmdb_results(t_url, None, None)
                else:
                    return {}
            return results
        except:
            log_utils.log('tmdb_results', 1)
            return {}


    def get(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
        try:
            trailer_list = []
            if self.trailer_source == '0':
                trailer_list = self.tmdb_trailers(name, url, tmdb, imdb, season, episode)
            elif self.trailer_source == '1':
                trailer_list = self.youtube_trailers(name, url, tmdb, imdb, season, episode)
            elif self.trailer_source == '2':
                trailer_list = self.imdb_trailers(name, url, tmdb, imdb, season, episode)
            elif self.trailer_source == '3':
                trailer_list = self.trakt_trailers(name, url, tmdb, imdb, season, episode)
            elif self.trailer_source == '4':
                if self.trailers_tmdb == 'true':
                    trailer_list += self.tmdb_trailers(name, url, tmdb, imdb, season, episode)
                if self.trailers_youtube == 'true':
                    trailer_list += self.youtube_trailers(name, url, tmdb, imdb, season, episode)
                if self.trailers_imdb == 'true':
                    trailer_list += self.imdb_trailers(name, url, tmdb, imdb, season, episode)
                if self.trailers_trakt == 'true':
                    trailer_list += self.trakt_trailers(name, url, tmdb, imdb, season, episode)
            else:
                return control.infoDialog('Trailer settings error')
            ## somehow the results seem to come around 3-ish times each lol.
            ## cant find why so imma be lazy and add the dupe_check :)
            #first_count = len(trailer_list) # Test1 = 163  Test2 = 135
            #log_utils.log('trailer_list first_count: ' + repr(first_count))
            trailer_list = list(self.dupe_check(trailer_list))
            #log_utils.log('trailer_list: ' + repr(trailer_list))
            #final_count = len(trailer_list) # Test1 = 45  Test2 = 38
            #log_utils.log('trailer_list final_count: ' + repr(final_count))
            item = self.select_items(trailer_list)
            return self.item_play(item, windowedtrailer)
        except:
            log_utils.log('get', 1)
            return


    def select_items(self, results):
        try:
            if not results:
                return
            results = [i for i in results if i.get('type') == 'Trailer'] + [i for i in results if i.get('type') != 'Trailer']
            if self.trailer_mode == '1':
                items = ['%s | %s (%s)' % (i.get('source', ''), i.get('title', ''), i.get('type', 'N/A')) for i in results]
                select = control.selectDialog(items, 'Trailers')
                if select == -1:
                    return 'canceled'
                return results[select]
            items = [i.get('url') for i in results]
            for vid_id in items:
                url = self.worker(vid_id)
                if url:
                    return url
            return
        except:
            log_utils.log('select_items', 1)
            return


    def item_play(self, result, windowedtrailer):
        try:
            if not result:
                return control.infoDialog('No trailer found')
            elif result == 'canceled':
                return
            title = result.get('title', '')
            if not title:
                title = control.infoLabel('ListItem.Title')
            url = result.get('url', '')
            if not url.startswith(self.youtube_plugin_url):
                url = self.worker(url)
            item = control.item(label=title, path=url)
            item.setProperty('IsPlayable', 'true')
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': title})
            else:
                item.setInfo(type='video', infoLabels={'title': title})
            control.resolve(handle=int(sys.argv[1]), succeeded=True, listitem=item)
            if windowedtrailer == 1:
                control.sleep(1000)
                while control.player.isPlayingVideo():
                    control.sleep(1000)
                control.execute('Dialog.Close(%s, true)' % control.getCurrentDialogId)
        except:
            log_utils.log('item_play', 1)
            return


    def worker(self, url):
        try:
            if not url:
                raise Exception()
            url = url.replace('http://', 'https://')
            url = url.replace('www.youtube.com', 'youtube.com')
            if url.startswith(self.youtube_link):
                url = self.resolve(url)
                if not url:
                    raise Exception()
            elif not url.startswith('http'):
                url = self.youtube_watch_link + url
                url = self.resolve(url)
                if not url:
                    raise Exception()
            return url
        except:
            log_utils.log('worker', 1)
            return


    def resolve(self, url):
        try:
            id = url.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
            url = self.youtube_watch_link + id
            result = client.scrapePage(url, timeout='30').text
            message = client_utils.parseDOM(result, 'div', attrs={'id': 'unavailable-submessage'})
            message = ''.join(message)
            alert = client_utils.parseDOM(result, 'div', attrs={'id': 'watch7-notification-area'})
            if len(alert) > 0:
                raise Exception()
            if re.search('[a-zA-Z]', message):
                raise Exception()
            url = self.youtube_plugin_url + id
            return url
        except:
            log_utils.log('resolve', 1)
            return []


    def dupe_check(self, items):
        uniqueURLs = set()
        for item in items:
            url = item.get('url')
            if isinstance(url, six.string_types):
                url = url.replace('http://', 'https://')
                if url not in uniqueURLs:
                    uniqueURLs.add(url)
                    yield item
                else:
                    pass
            else:
                yield item


