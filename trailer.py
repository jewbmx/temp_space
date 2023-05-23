# -*- coding: utf-8 -*-

"""
#########################################


This is a little note added to show the changes for this new module to be added in.
(Not included in the actual addon, just this temp file.)
[ Anyone feeling like testing this or helping out with the coding, contact me however for whatever lol. ]

### settings.xml

<setting id="trailer.source" type="enum" label="Trailers Source" values="TMDb|YouTube|IMDb|Trakt" default="2" />
## Old Code Saved...
#<setting id="trailer.source" type="enum" label="Trailers Source" values="TMDb|YouTube|IMDb" default="2" />


### system.py

    elif action == 'trailer':
        from resources.lib.modules import control
        if not control.condVisibility('System.HasAddon(plugin.video.youtube)'):
            control.installAddon('plugin.video.youtube')
        from resources.lib.modules import trailer
        trailer.source().get(name, url, tmdb, imdb, season, episode, windowedtrailer)
        ## Old Code Saved...
        #trailer_source = control.setting('trailer.source') or '2'
        #if trailer_source == '0':
            #trailer.TMDb_trailer().play(tmdb, imdb, season, episode, windowedtrailer)
        #elif trailer_source == '1':
            #trailer.YT_trailer().play(name, url, tmdb, imdb, season, episode, windowedtrailer)
        #else:
            #trailer.IMDb_trailer().play(imdb, name, tmdb, season, episode, windowedtrailer)


(Each chunk or section is split up with my ghetto #### lines.)
--Futher plans/goals are...
-To cleanup the code.
-Maybe swap tmdb to my tmdb_utils trailer defs.
-Maybe make all the search sources run then show a full list like ['(Trakt) Rampage Trailer', '(TMDb) Rampage Trailer']...
-And if its not already done from whats listed above this, reduce the repeated code used when it could be used in one def and passed around.
-Possible suicide due to this module and everything regarding youtube :)


#########################################
"""


import re
import sys
import random

import simplejson as json
from six.moves import urllib_parse

try:
    #from infotagger.listitem import ListItemInfoTag
    from resources.lib.modules.listitem import ListItemInfoTag
except:
    pass

from resources.lib.modules import client
from resources.lib.modules import client_utils
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import trakt

kodi_version = control.getKodiVersion()


class source:
    def __init__(self):
        self.content = control.infoLabel('Container.Content')
        self.trailer_mode = control.setting('trailer.select') or '1'
        self.trailer_source = control.setting('trailer.source') or '2'
        
        self.youtube_link = 'https://youtube.com'
        self.youtube_watch_link = 'https://youtube.com/watch?v=%s'
        #self.youtube_plugin_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'
        self.youtube_plugin_url = 'plugin://plugin.video.youtube/play/?video_id=%s'
        
        #############################################################
        
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
        
        #############################################################
        
        self.imdb_link = 'https://www.imdb.com/_json/video/'
        
        #############################################################
        
        self.tmdb_key = control.setting('tmdb.api')
        if self.tmdb_key == '' or self.tmdb_key == None:
            self.tmdb_key = 'c8b7db701bac0b26edfcc93b39858972'
        
        self.tmdb_lang = control.apiLanguage().get('tmdb', 'en')
        self.tmdb_lang_link = 'en,null' if self.tmdb_lang == 'en' else 'en,%s,null' % self.tmdb_lang
        
        self.tmdb_movie_link = 'https://api.themoviedb.org/3/movie/%s/videos?api_key=%s&include_video_language=%s' % ('%s', self.tmdb_key, self.tmdb_lang_link)
        self.tmdb_show_link = 'https://api.themoviedb.org/3/tv/%s/videos?api_key=%s&include_video_language=%s' % ('%s', self.tmdb_key, self.tmdb_lang_link)
        self.tmdb_season_link = 'https://api.themoviedb.org/3/tv/%s/season/%s/videos?api_key=%s&include_video_language=%s' % ('%s', '%s', self.tmdb_key, self.tmdb_lang_link)
        self.tmdb_episode_link = 'https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s/videos?api_key=%s&include_video_language=%s' % ('%s', '%s', '%s', self.tmdb_key, self.tmdb_lang_link)
        
        #############################################################


############################################################################################################
############################################################################################################


    def youtube_play(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
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
            query = urllib_parse.quote_plus(name)
            url = self.youtube_items(query)
            
            #url = self.worker(url)
            
            if not url:
                return control.infoDialog('No trailer found')
            elif url == 'canceled':
                return
            icon = control.infoLabel('ListItem.Icon')
            item = control.item(label=name, path=url)
            item.setProperty('IsPlayable', 'true')
            item.setArt({'icon': icon, 'thumb': icon, 'poster': icon})
            ###
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': name})
            else:
                item.setInfo(type='video', infoLabels={'title': name})
            ###
            control.resolve(handle=int(sys.argv[1]), succeeded=True, listitem=item)
            if windowedtrailer == 1:
                control.sleep(1000)
                while control.player.isPlayingVideo():
                    control.sleep(1000)
                control.execute('Dialog.Close(%s, true)' % control.getCurrentDialogId)
        except:
            log_utils.log('youtube_play', 1)
            return


    def youtube_items(self, query):
        try:
            url = self.youtube_search_link % (query, self.youtube_key)
            result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                url = self.youtube_search_link % (query, self.youtube_keys[0])
                result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                url = self.youtube_search_link % (query, self.youtube_keys[1])
                result = client.scrapePage(url, timeout='30').json()
            if (not result) or ('error' in result):
                return
            
            json_items = result['items']
            ids = [i['id']['videoId'] for i in json_items]
            if not ids:
                return
            if self.trailer_mode == '1':
                vids = []
                for i in json_items:
                    name = client_utils.replaceHTMLCodes(i['snippet']['title'])
                    if kodi_version >= 17:
                        icon = i['snippet']['thumbnails']['default']['url']
                        li = control.item(label=name)
                        li.setArt({'icon': icon, 'thumb': icon, 'poster': icon})
                        vids.append(li)
                    else:
                        vids.append(name)
                select = control.selectDialog(vids, 'YouTube Trailers', useDetails=True)
                if select == -1:
                    return 'canceled'
                vid_id = ids[select]
                url = self.youtube_plugin_url % vid_id
                return url
            for vid_id in ids:
                url = self.resolve(vid_id)
                if url:
                    return url
            return
        except:
            log_utils.log('youtube_items', 1)
            return


############################################################################################################
############################################################################################################



    def trakt_play(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
        try:
            if not imdb or imdb == '0':
                raise Exception()
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
            name += ' trailer'
            url = self.trakt_items(name, results)
            if not url:
                return control.infoDialog('No trailer found')
            elif url == 'canceled':
                return
            icon = control.infoLabel('ListItem.Icon')
            item = control.item(label=name, path=url)
            item.setProperty('IsPlayable', 'true')
            item.setArt({'icon': icon, 'thumb': icon, 'poster': icon})
            ###
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': name})
            else:
                item.setInfo(type='video', infoLabels={'title': name})
            ###
            control.resolve(handle=int(sys.argv[1]), succeeded=True, listitem=item)
            if windowedtrailer == 1:
                control.sleep(1000)
                while control.player.isPlayingVideo():
                    control.sleep(1000)
                control.execute('Dialog.Close(%s, true)' % control.getCurrentDialogId)
        except:
            log_utils.log('trakt_play', 1)
            return


    def trakt_items(self, name, results):
        try:
            if not results:
                return
            items = [results.get('trailer', '')]
            if self.trailer_mode == '1':
                labels = [name]
                select = control.selectDialog(labels, 'Trakt Trailers', useDetails=True)
                if select == -1:
                    return 'canceled'
                vid_id = items[select]
                url = self.resolve(vid_id)
                if url:
                    return url
            for vid_id in items:
                url = self.resolve(vid_id)
                if url:
                    return url
            return
        except:
            log_utils.log('trakt_items', 1)
            return



############################################################################################################
############################################################################################################



    def imdb_play(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
        try:
            if not imdb or imdb == '0':
                raise Exception()
            item_dict = self.imdb_items(imdb, name)
            if not item_dict:
                return control.infoDialog('No trailer found')
            elif item_dict == 'canceled':
                return
            url, title, plot = item_dict['video'], item_dict['title'], item_dict['description']
            icon = control.infoLabel('ListItem.Icon')
            item = control.item(label=title, path=url)
            item.setProperty('IsPlayable', 'true')
            item.setArt({'icon': icon, 'thumb': icon, 'poster': icon})
            ###
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': title, 'plot': plot})
            else:
                item.setInfo(type='video', infoLabels={'title': title, 'plot': plot})
            ###
            control.resolve(handle=int(sys.argv[1]), succeeded=True, listitem=item)
            if windowedtrailer == 1:
                control.sleep(1000)
                while control.player.isPlayingVideo():
                    control.sleep(1000)
                control.execute('Dialog.Close(%s, true)' % control.getCurrentDialogId)
        except:
            log_utils.log('imdb_play', 1)
            return


    def imdb_items(self, imdb, name):
        try:
            link = self.imdb_link + imdb
            items = client.scrapePage(link, timeout='30').json()
            listItems = items['playlists'][imdb]['listItems']
            videoMetadata = items['videoMetadata']
            vids_list = []
            for item in listItems:
                try:
                    desc = item.get('description') or ''
                    videoId = item['videoId']
                    metadata = videoMetadata[videoId]
                    title = metadata['title']
                    icon = metadata['smallSlate']['url2x']
                    related_to = metadata.get('primaryConst') or imdb
                    if (not related_to == imdb) and (not name.lower() in ' '.join((title, desc)).lower()):
                        continue
                    videoUrl = [i['videoUrl'] for i in metadata['encodings'] if i['definition'] in ['1080p', '720p', '480p', '360p', 'SD']]
                    if not videoUrl:
                        continue
                    vids_list.append({'title': title, 'icon': icon, 'description': desc, 'video': videoUrl[0]})
                except:
                    pass
            if not vids_list:
                return
            vids_list = [v for v in vids_list if 'trailer' in v['title'].lower()] + [v for v in vids_list if 'trailer' not in v['title'].lower()]
            if self.trailer_mode == '1':
                vids = []
                for v in vids_list:
                    if kodi_version >= 17:
                        li = control.item(label=v['title'])
                        li.setArt({'icon': v['icon'], 'thumb': v['icon'], 'poster': v['icon']})
                        vids.append(li)
                    else:
                        vids.append(v['title'])
                select = control.selectDialog(vids, 'IMDb Trailers', useDetails=True)
                if select == -1:
                    return 'canceled'
                return vids_list[select]
            return vids_list[0]
        except:
            log_utils.log('imdb_items', 1)
            return



############################################################################################################
############################################################################################################



    def tmdb_play(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
        try:
            t_url = self.tmdb_show_link % tmdb
            s_url = self.tmdb_season_link % (tmdb, season)
            if self.content == 'tvshows':
                if not tmdb or tmdb == '0':
                    return control.infoDialog('No ID found')
                api_url = t_url
            elif self.content == 'seasons':
                if not tmdb or tmdb == '0':
                    return control.infoDialog('No ID found')
                api_url = s_url
            elif self.content == 'episodes':
                if not tmdb or tmdb == '0':
                    return control.infoDialog('No ID found')
                api_url = self.tmdb_episode_link % (tmdb, season, episode)
            else:
                id = tmdb if not tmdb == '0' else imdb
                if not id or id == '0':
                    return control.infoDialog('No ID found')
                api_url = self.tmdb_movie_link % id
            results = self.tmdb_results(api_url, t_url, s_url)
            url = self.tmdb_items(results)
            if not url:
                return control.infoDialog('No trailer found')
            elif url == 'canceled':
                return
            icon = control.infoLabel('ListItem.Icon')
            name = control.infoLabel('ListItem.Title')
            item = control.item(label=name, path=url)
            item.setProperty('IsPlayable', 'true')
            item.setArt({'icon': icon, 'thumb': icon, 'poster': icon})
            ###
            if kodi_version >= 20:
                info_tag = ListItemInfoTag(item, 'video')
                info_tag.set_info({'title': name})
            else:
                item.setInfo(type='video', infoLabels={'title': name})
            ###
            control.resolve(handle=int(sys.argv[1]), succeeded=True, listitem=item)
            if windowedtrailer == 1:
                control.sleep(1000)
                while control.player.isPlayingVideo():
                    control.sleep(1000)
                control.execute('Dialog.Close(%s, true)' % control.getCurrentDialogId)
        except:
            log_utils.log('tmdb_play', 1)
            return


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
                    return
            return results
        except:
            log_utils.log('tmdb_results', 1)
            return


    def tmdb_items(self, results):
        try:
            if not results:
                return
            if self.trailer_mode == '1':
                items = [i.get('key') for i in results]
                labels = [' | '.join((i.get('name', ''), i.get('type', ''))) for i in results]
                select = control.selectDialog(labels, 'TMDb Trailers', useDetails=True)
                if select == -1:
                    return 'canceled'
                vid_id = items[select]
                url = self.youtube_plugin_url % vid_id
                return url
            results = [x for x in results if x.get('type') == 'Trailer'] + [x for x in results if x.get('type') != 'Trailer']
            items = [i.get('key') for i in results]
            for vid_id in items:
                url = self.resolve(vid_id)
                if url:
                    return url
            return
        except:
            log_utils.log('tmdb_items', 1)
            return



############################################################################################################
############################################################################################################


    def get(self, name='', url='', tmdb='', imdb='', season='', episode='', windowedtrailer=0):
        try:
            if self.trailer_source == '0':
                trailer_play = self.tmdb_play
            elif self.trailer_source == '1':
                trailer_play = self.youtube_play
            elif self.trailer_source == '2':
                trailer_play = self.imdb_play
            else:
                trailer_play = self.trakt_play
            trailer_play(name, url, tmdb, imdb, season, episode, windowedtrailer)
        except:
            log_utils.log('get', 1)
            pass


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
                return url
            elif not url.startswith('http'):
                url = self.youtube_watch_link % url
                url = self.resolve(url)
                if not url:
                    raise Exception()
                return url
            else:
                raise Exception()
        except:
            log_utils.log('worker', 1)
            return


    def resolve(self, url):
        try:
            id = url.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
            url = self.youtube_watch_link % id
            result = client.scrapePage(url, timeout='30').text
            message = client_utils.parseDOM(result, 'div', attrs={'id': 'unavailable-submessage'})
            message = ''.join(message)
            alert = client_utils.parseDOM(result, 'div', attrs={'id': 'watch7-notification-area'})
            if len(alert) > 0:
                raise Exception()
            if re.search('[a-zA-Z]', message):
                raise Exception()
            url = self.youtube_plugin_url % id
            return url
        except:
            log_utils.log('resolve', 1)
            return


