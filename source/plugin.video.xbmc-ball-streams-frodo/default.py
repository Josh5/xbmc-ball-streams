import xbmc, xbmcplugin, xbmcaddon, xbmcgui
import ballstreams, utils
import os, datetime, threading, random, time

# xbmc-ball-streams
# author: craig mcnicholas, andrew wise
# contact: craig@designdotworks.co.uk, zergcollision@gmail.com

# deals with a bug where errors are thrown 
# if data directory does not exist.
addonId = 'plugin.video.xbmc-ball-streams-frodo'
dataPath = 'special://profile/addon_data/' + addonId
if not os.path.exists: os.makedirs(dataPath)
addon = xbmcaddon.Addon(id = addonId)
addonPath = addon.getAddonInfo('path')

# Method to draw the home screen
def HOME():
    print 'HOME()'
    utils.addDir(addon.getLocalizedString(100005), utils.Mode.ONDEMAND, '', None, 2, showfanart)
    utils.addDir(addon.getLocalizedString(100006), utils.Mode.LIVE, '', None, 2, showfanart)

    setViewMode()

# Method to draw the archives screen
def ONDEMAND():
    print 'ONDEMAND()'
    utils.addDir(addon.getLocalizedString(100007), utils.Mode.ONDEMAND_BYDATE, '', None, 2, showfanart)
    utils.addDir(addon.getLocalizedString(100008), utils.Mode.ONDEMAND_BYTEAM, '', None, 2, showfanart)
    
    # Append Recent day events
    ONDEMAND_RECENT(session)

    setViewMode()

# Method to draw the archives by date screen
# which scrapes the external source and presents
# a list of months/years for archives
def ONDEMAND_BYDATE(session):
    print 'ONDEMAND_BYDATE(session)'

    # Retrieve the available dates
    dates = ballstreams.onDemandDates(session)

    # Find unique months/years
    monthsYears = []
    for date in dates:
        current = str(date.month) + '/' + str(date.year)
        if monthsYears.count(current) < 1:
            monthsYears.append(current)

    # Count total number of items for ui
    totalItems = len(monthsYears)

    # Add directories for months
    for monthYear in monthsYears:
        # Create datetime for string formatting
        index = monthYear.index("/")
        year = monthYear[index+1:]
        month = monthYear[:index]
        date = datetime.date(int(year), int(month), 1)
        params = {
            'year': str(year),
            'month': str(month)
        }
        utils.addDir(date.strftime('%B %Y'), utils.Mode.ONDEMAND_BYDATE_YEARMONTH, '', params, totalItems, showfanart)

    # Add custom date directory
    utils.addDir('[ Custom Date ]', utils.Mode.ONDEMAND_BYDATE_CUSTOM, '', None, 2, showfanart)

    setViewMode()

# Method to draw the on-demand by date screen
# which scrapes the external source and presents
# a list of days for a given year and month of archives
def ONDEMAND_BYDATE_YEARMONTH(session, year, month):
    print 'ONDEMAND_BYDATE_YEARMONTH(session, year, month)'
    print 'Year: ' + str(year)
    print 'Month: ' + str(month)

    # Retrieve the available dates
    dates = ballstreams.onDemandDates(session)

    # Find unique days
    days = []
    for date in dates:
        if year == date.year and month == date.month and days.count(date.day) < 1:
            days.append(date.day)

    # Count total number of items for ui
    totalItems = len(days)

    # Add directories for days
    for day in days:
        # Create datetime for string formatting
        date = datetime.date(year, month, day)
        params = {
            'year': str(year),
            'month': str(month),
            'day': str(day)
        }
        utils.addDir(date.strftime('%A %d %B %Y'), utils.Mode.ONDEMAND_BYDATE_YEARMONTH_DAY, '', params, totalItems, showfanart)

    setViewMode()

# Method to draw the archives by date screen
# which scrapes the external source and presents
# a list of on-demand events for a given day
def ONDEMAND_BYDATE_YEARMONTH_DAY(session, year, month, day):
    print 'ONDEMAND_BYDATE_YEARMONTH_DAY(session, year, month, day)'
    print 'Year: ' + str(year)
    print 'Month: ' + str(month)
    print 'Day: ' + str(day)

    # Retrieve the events
    date = datetime.date(year, month, day)
    try:
        events = ballstreams.dateOnDemandEvents(session, date)
    except Exception as e:
        print 'Warning:  No events found for date: ' + str(date) + ' Msg: ' + str(e)
        return

    totalItems = len(events)

    for event in events:
        # Create datetime for string formatting
        parts = event.date.split('/')
        day = int(parts[1])
        month = int(parts[0])
        year = int(parts[2])
        dateStr = ' - ' + datetime.date(year, month, day).strftime('%d %b \'%y')

        # Build matchup
        homeTeam = event.homeTeam if not shortNames else ballstreams.shortTeamName(event.homeTeam, addonPath)
        awayTeam = event.awayTeam if not shortNames else ballstreams.shortTeamName(event.awayTeam, addonPath)
        matchupStr = awayTeam + ' @ ' + homeTeam
        if awayTeam == '' or homeTeam == '': # Indicates special event
            matchupStr = awayTeam + homeTeam
        if feedType == 'Home Feed':
            matchupStr = matchupStr + '*'
        elif feedType == 'Away Feed':
            matchupStr = awayTeam + '* @ ' + homeTeam
        # Build title
        title = event.event + ': ' + matchupStr + dateStr
        if event.homeTeam == session.favteam or event.awayTeam == session.favteam:
            title = '[COLOR red][B]' + title + '[/B][/COLOR]'

        params = {
            'eventId': event.eventId,
            'feedType': event.feedType,
            'dateStr': dateStr
        }
        utils.addDir(title, utils.Mode.ONDEMAND_BYDATE_YEARMONTH_DAY_EVENT, '', params, totalItems, showfanart)

    setViewMode()

# Method to draw the archives by date screen
# which scrapes the external source and presents
# a list of on-demand streams for a given event
def ONDEMAND_BYDATE_YEARMONTH_DAY_EVENT(session, eventId, feedType, dateStr):
    print 'ONDEMAND_BYDATE_YEARMONTH_DAY_EVENT(session, eventId, feedType, dateStr)'
    print 'eventId: ' + eventId
    print 'feedType: ' + str(feedType)
    print 'dateStr: ' + dateStr

    # Build streams
    onDemandStream = ballstreams.onDemandEventStreams(session, eventId, location)

    totalItems = 10 # max possible

    if onDemandStream == None or onDemandStream.streamSet == None:
        return None

    # Build matchup
    homeTeam = onDemandStream.homeTeam if not shortNames else ballstreams.shortTeamName(onDemandStream.homeTeam, addonPath)
    awayTeam = onDemandStream.awayTeam if not shortNames else ballstreams.shortTeamName(onDemandStream.awayTeam, addonPath)
    matchupStr = awayTeam + ' @ ' + homeTeam
    if awayTeam == '' or homeTeam == '': # Indicates special event
        matchupStr = awayTeam + homeTeam
    if feedType == 'Home Feed':
        matchupStr = matchupStr + '*'
    elif feedType == 'Away Feed':
        matchupStr = awayTeam + '* @ ' + homeTeam
    # Build title
    title = onDemandStream.event + ': ' + matchupStr + dateStr

    if flash and onDemandStream.streamSet['flash'] != None:
        suffix = ' [Flash]'
        utils.addLink(title + suffix, onDemandStream.streamSet['flash'].replace('f4m', 'm3u8'), '', totalItems, showfanart)
    if istream and resolution != 'SD Only' and onDemandStream.streamSet['istream.hd'] != None:
        suffix = ' [iStream HD]'
        utils.addLink(title + suffix, onDemandStream.streamSet['istream.hd'], '', totalItems, showfanart)
    if istream and resolution != 'HD Only' and onDemandStream.streamSet['istream.sd'] != None:
        suffix = ' [iStream SD]'
        utils.addLink(title + suffix, onDemandStream.streamSet['istream.sd'].replace('f4m', 'm3u8'), '', totalItems, showfanart)
    if istream and resolution == 'All' and onDemandStream.streamSet['istream'] != None and onDemandStream.streamSet['istream'] != onDemandStream.streamSet['istream.hd']:
        suffix = ' [iStream]'
        utils.addLink(title + suffix, onDemandStream.streamSet['istream'], '', totalItems, showfanart)
    if progressiveUrl != None and resolution != 'SD Only' and onDemandStream.streamSet['istream.hd'] != None:
        suffix = ' [Progressive HD]'
        utils.addLink(title + suffix, ballstreams.deriveProgressiveUrl(onDemandStream.streamSet['istream.hd'],progressiveUrl), '', totalItems, showfanart)
    if progressiveUrl != None and resolution != 'HD Only' and onDemandStream.streamSet['istream.sd'] != None:
        suffix = ' [Progressive SD]'
        utils.addLink(title + suffix, ballstreams.deriveProgressiveUrl(onDemandStream.streamSet['istream.sd'].replace('f4m', 'm3u8'),progressiveUrl), '', totalItems, showfanart)
    if wmv and onDemandStream.streamSet['wmv'] != None:
        suffix = ' [WMV]'
        utils.addLink(title + suffix, onDemandStream.streamSet['wmv'], '', totalItems, showfanart)

    try:
        hTeam = onDemandStream.homeTeam
        dStr = datetime.datetime.strptime(dateStr, ' - %d %b \'%y')
        HIGHLIGHTSANDCONDENSED_BYTEAM_TEAMDATE(session, hTeam, dStr)
    except Exception as e:
        print 'Error initializing highlights/condensed: ' + str(e)

    setViewMode()

# Method to draw a list of recent month/years
# to custom search on-demand archives
def ONDEMAND_BYDATE_CUSTOM(session):
    print 'ONDEMAND_BYDATE_CUSTOM(session)'

    a = datetime.datetime.today()
    daysBack = 800 # Could be an addon setting
    dateStrList = []
    for x in range (0, daysBack):
        nextDate = a - datetime.timedelta(days = x)
        monthYear = nextDate.strftime('%B %Y')
        if (dateStrList.count(monthYear)==0):
            dateStrList.append(monthYear)
            params = {
                'year': str(nextDate.year),
                'month': str(nextDate.month)
            }
            utils.addDir(monthYear, utils.Mode.ONDEMAND_BYDATE_CUSTOM_YEARMONTH, '', params, 17, showfanart)

    setViewMode()

# Method to draw a list of days for a given month/year
# to custom search on-demand archives
def ONDEMAND_BYDATE_CUSTOM_YEARMONTH(session, year, month):
    print 'ONDEMAND_BYDATE_CUSTOM_YEARMONTH(session, year, month)'
    print 'Year: ' + str(year)
    print 'Month: ' + str(month)

    currentDay = datetime.date.today()
    nextMonthDay = datetime.date(year, month, 1) + datetime.timedelta(days = 31)
    lastMonthDay = datetime.date(nextMonthDay.year, nextMonthDay.month, 1) - datetime.timedelta(days = 1)
    daysBack = int(lastMonthDay.day)

    # COMMENTED THIS OUT - CRASHES XBMC TOO OFTEN EXECUTING TOO MANY API REQUESTS SO QUICKLY
    # if lastMonthDay < currentDay or currentDay.day > 16:
        # params = {
            # 'year': str(year),
            # 'month': str(month),
            # 'day': str(16),
            # 'numberOfDays': str(16)
        # }
        # if str(lastMonthDay.day) == '31':
            # title = '[ Deep Search ' + lastMonthDay.strftime('%B') + ' 16th to ' + str(lastMonthDay.day) + 'st ]'
        # else:
            # title = '[ Deep Search ' + lastMonthDay.strftime('%B') + ' 16th to ' + str(lastMonthDay.day) + 'th ]'
        # utils.addDir(title, utils.Mode.ONDEMAND_BYDATE_CUSTOM_YEARMONTH_RANGE, '', params, 33, showfanart)
    # if lastMonthDay < currentDay or currentDay.day > 1:
        # params = {
            # 'year': str(year),
            # 'month': str(month),
            # 'day': str(1),
            # 'numberOfDays': str(15)
        # }
        # title = '[ Deep Search ' + lastMonthDay.strftime('%B') + ' 1st to 15th ]'
        # utils.addDir(title, utils.Mode.ONDEMAND_BYDATE_CUSTOM_YEARMONTH_RANGE, '', params, 33, showfanart)

    for x in range (0, daysBack):
        nextDate = lastMonthDay - datetime.timedelta(days = x)
        if nextDate <= currentDay:
            params = {
                'year': str(nextDate.year),
                'month': str(nextDate.month),
                'day': str(nextDate.day)
            }
            utils.addDir(nextDate.strftime('%A %d %B %Y'), utils.Mode.ONDEMAND_BYDATE_YEARMONTH_DAY, '', params, 33, showfanart)
    
    setViewMode()

# Method to populate a date range of events
# which scrapes the external source and presents
# a list of events within a date range
def ONDEMAND_BYDATE_CUSTOM_YEARMONTH_RANGE(session, year, month, day, numberOfDays):
    print 'ONDEMAND_RECENT(session)'
    print 'year: ' + str(year)
    print 'month: ' + str(month)
    print 'day: ' + str(day)
    print 'numberOfDays: ' + str(numberOfDays)

    startDate = datetime.date(year, month, day)

    # Loop daysback to Build event list
    i = abs(numberOfDays)-1
    while i >= 0:
        # get current date
        nextDate = startDate + datetime.timedelta(i)
        
        # exit on new month
        if nextDate.month != month:
            continue

        # Build events for day
        ONDEMAND_BYDATE_YEARMONTH_DAY(session, nextDate.year, nextDate.month, nextDate.day)

        # Increment loop to avoid TO INFINITY AND BEYOND!!
        i -= 1

    setViewMode()

# Method to draw the archives by team screen
# which scrapes the external source and presents
# a list of team names (or potentially events)
def ONDEMAND_BYTEAM(session):
    print 'ONDEMAND_BYTEAM(session)'

    # Retrieve the teams
    teams = ballstreams.teams(session)

    # Count total number of items for ui
    totalItems = len(teams)
    
    utils.addDir('[ All Teams ]', utils.Mode.ONDEMAND_BYTEAM_LEAGUE, '', None, totalItems, showfanart)

    # Add directories for teams
    league = []
    for team in teams:
        if (league.count(team.league) == 0):
            league.append(team.league)
            params = {
                'league': team.league
            }
            title = team.league
            utils.addDir(title, utils.Mode.ONDEMAND_BYTEAM_LEAGUE, '', params, totalItems, showfanart)

    setViewMode()

# Method to draw the archives by league screen
# which scrapes the external source and presents
# a list of team names
def ONDEMAND_BYTEAM_LEAGUE(session, league):
    print 'ONDEMAND_BYTEAM_LEAGUE(session, league)'
    print 'League: ' + str(league)

    # Retrieve the teams
    teams = ballstreams.teams(session, league)

    # Count total number of items for ui
    totalItems = len(teams)

    # Add directories for teams
    for team in teams:
        params = {
            'league': team.league,
            'team': team.name
        }
        title = team.name
        if league == None and team.league != None:
            title = team.league + ': ' + team.name
        if team.name == session.favteam:
            title = '[COLOR red][B]' + title + '[/B][/COLOR]'
        utils.addDir(title, utils.Mode.ONDEMAND_BYTEAM_LEAGUE_TEAM, '', params, totalItems, showfanart)

    setViewMode()

# Method to draw the archives by team screen
# which scrapes the external source and presents
# a list of events for a given team
def ONDEMAND_BYTEAM_LEAGUE_TEAM(session, league, team):
    print 'ONDEMAND_BYTEAM_LEAGUE_TEAM(session, league, team)'
    print 'League: ' + league
    print 'Team: ' + team

    # Retrieve the team events
    events = ballstreams.teamOnDemandEvents(session, ballstreams.Team(team))

    totalItems = len(events)

    for event in events:
        # Check league filter
        if league != None and len(league) > 0 and event.event != None and len(event.event) > 0:
            if not event.event.startswith(league):
                continue # skip to next event

        # Create datetime for string formatting
        parts = event.date.split('/')
        day = int(parts[1])
        month = int(parts[0])
        year = int(parts[2])
        dateStr = ' - ' + datetime.date(year, month, day).strftime('%d %b \'%y')

        homeTeam = event.homeTeam if not shortNames else ballstreams.shortTeamName(event.homeTeam, addonPath)
        awayTeam = event.awayTeam if not shortNames else ballstreams.shortTeamName(event.awayTeam, addonPath)
        matchupStr = awayTeam + ' @ ' + homeTeam
        if awayTeam == '' or homeTeam == '': # Indicates special event
            matchupStr = awayTeam + homeTeam
        if feedType == 'Home Feed':
            matchupStr = matchupStr + '*'
        elif feedType == 'Away Feed':
            matchupStr = awayTeam + '* @ ' + homeTeam
        # Build title
        title = event.event + ': ' + matchupStr + dateStr

        params = {
            'eventId': event.eventId,
            'feedType': event.feedType,
            'dateStr': dateStr
        }
        utils.addDir(title, utils.Mode.ONDEMAND_BYTEAM_LEAGUE_TEAM_EVENT, '', params, totalItems, showfanart)

    setViewMode()

# Method to draw the highlights screen
# which scrapes the external source and presents
# a list of highlights for a given team and/or date
def HIGHLIGHTSANDCONDENSED_BYTEAM_TEAMDATE(session, team, date):
    print 'HIGHLIGHTSANDCONDENSED_BYTEAM_TEAMDATE(session, team, date)'
    print 'Team: ' + str(team)
    print 'Date: ' + str(date)

    highlights = []
    if showhighlight:
        highlights = ballstreams.dateOnDemandHighlights(session, date, team)
    condensedGames = []
    if showcondensed:
        condensedGames = ballstreams.dateOnDemandHighlights(session, date, team)

    totalItems = len(highlights) + len(condensedGames)

    src = []
    for highlight in highlights:
        if team == None or (team == highlight.homeTeam or team == highlight.awayTeam):
            # Create datetime for string formatting
            parts = highlight.date.split('/')
            day = int(parts[1])
            month = int(parts[0])
            year = int(parts[2])
            dateStr = ' - ' + datetime.date(year, month, day).strftime('%d %b \'%y')
            # Build matchup
            homeTeam = highlight.homeTeam if not shortNames else ballstreams.shortTeamName(highlight.homeTeam, addonPath)
            awayTeam = highlight.awayTeam if not shortNames else ballstreams.shortTeamName(highlight.awayTeam, addonPath)
            matchupStr = awayTeam + ' @ ' + homeTeam
            if awayTeam == '' or homeTeam == '': # Indicates special event
                matchupStr = awayTeam + homeTeam
            # Build title
            title = '[Highlight] ' + highlight.event + ': ' + matchupStr + dateStr

            if highlight.highQualitySrc != None and len(highlight.highQualitySrc) > 0 and src.count(highlight.medQualitySrc) == 0:
                utils.addLink(title + ' [Hi]', highlight.highQualitySrc, '', totalItems, showfanart)
                src.append(highlight.highQualitySrc)
            if highlight.medQualitySrc != None and len(highlight.medQualitySrc) > 0 and src.count(highlight.medQualitySrc) == 0:
                utils.addLink(title + ' [Med]', highlight.medQualitySrc, '', totalItems, showfanart)
                src.append(highlight.medQualitySrc)
            if highlight.lowQualitySrc != None and len(highlight.lowQualitySrc) > 0 and src.count(highlight.lowQualitySrc) == 0:
                utils.addLink(title + ' [Lo]', highlight.lowQualitySrc, '', totalItems, showfanart)
                src.append(highlight.lowQualitySrc)
            if highlight.homeSrc != None and len(highlight.homeSrc) > 0 and src.count(highlight.homeSrc) == 0:
                utils.addLink(title + ' [Home]', highlight.homeSrc, '', totalItems, showfanart)
                src.append(highlight.homeSrc)
            if highlight.awaySrc != None and len(highlight.awaySrc) > 0 and src.count(highlight.awaySrc) == 0:
                utils.addLink(title + ' [Away]', highlight.awaySrc, '', totalItems, showfanart)
                src.append(highlight.awaySrc)

    for condensedGame in condensedGames:
        if team == None or (team == condensedGame.homeTeam or team == condensedGame.awayTeam):
            # Create datetime for string formatting
            parts = condensedGame.date.split('/')
            day = int(parts[1])
            month = int(parts[0])
            year = int(parts[2])
            dateStr = ' - ' + datetime.date(year, month, day).strftime('%d %b \'%y')
            # Build matchup
            homeTeam = condensedGame.homeTeam if not shortNames else hockeystreams.shortTeamName(condensedGame.homeTeam, addonPath)
            awayTeam = condensedGame.awayTeam if not shortNames else hockeystreams.shortTeamName(condensedGame.awayTeam, addonPath)
            matchupStr = awayTeam + ' @ ' + homeTeam
            if awayTeam == '' or homeTeam == '': # Indicates special event
                matchupStr = awayTeam + homeTeam
            # Build title
            title = '[Condensed] ' + condensedGame.event + ': ' + matchupStr + dateStr

            if condensedGame.highQualitySrc != None and len(condensedGame.highQualitySrc) > 0 and src.count(condensedGame.medQualitySrc) == 0:
                utils.addLink(title + ' [Hi]', condensedGame.highQualitySrc, '', totalItems, showfanart)
                src.append(condensedGame.highQualitySrc)
            if condensedGame.medQualitySrc != None and len(condensedGame.medQualitySrc) > 0 and src.count(condensedGame.medQualitySrc) == 0:
                utils.addLink(title + ' [Med]', condensedGame.medQualitySrc, '', totalItems, showfanart)
                src.append(condensedGame.medQualitySrc)
            if condensedGame.lowQualitySrc != None and len(condensedGame.lowQualitySrc) > 0 and src.count(condensedGame.lowQualitySrc) == 0:
                utils.addLink(title + ' [Lo]', condensedGame.lowQualitySrc, '', totalItems, showfanart)
                src.append(condensedGame.lowQualitySrc)
            if condensedGame.homeSrc != None and len(condensedGame.homeSrc) > 0 and src.count(condensedGame.homeSrc) == 0:
                utils.addLink(title + ' [Home]', condensedGame.homeSrc, '', totalItems, showfanart)
                src.append(condensedGame.homeSrc)
            if condensedGame.awaySrc != None and len(condensedGame.awaySrc) > 0 and src.count(condensedGame.awaySrc) == 0:
                utils.addLink(title + ' [Away]', condensedGame.awaySrc, '', totalItems, showfanart)
                src.append(condensedGame.awaySrc)

# Method to draw the archive streams by event screen
# which scrapes the external source and presents
# a list of streams for a given stream id
def ONDEMAND_BYTEAM_LEAGUE_TEAM_EVENT(session, eventId, feedType, dateStr):
    print 'ONDEMAND_BYTEAM_LEAGUE_TEAM_EVENT(session, eventId, feedType, dateStr)'
    print 'eventId: ' + eventId
    print 'feedType: ' + str(feedType)
    print 'dateStr: ' + str(dateStr)

    # Build streams
    onDemandStream = ballstreams.onDemandEventStreams(session, eventId, location)

    totalItems = 6 # max possible

    if onDemandStream == None or onDemandStream.streamSet == None:
        return None

    # Build matchup
    homeTeam = onDemandStream.homeTeam if not shortNames else ballstreams.shortTeamName(onDemandStream.homeTeam, addonPath)
    awayTeam = onDemandStream.awayTeam if not shortNames else ballstreams.shortTeamName(onDemandStream.awayTeam, addonPath)
    matchupStr = awayTeam + ' @ ' + homeTeam
    if awayTeam == '' or homeTeam == '': # Indicates special event
        matchupStr = awayTeam + homeTeam
    if feedType == 'Home Feed':
        matchupStr = matchupStr + '*'
    elif feedType == 'Away Feed':
        matchupStr = awayTeam + '* @ ' + homeTeam
    # Build title
    title = onDemandStream.event + ': ' + matchupStr + str(dateStr)

    if flash and onDemandStream.streamSet['flash'] != None:
        suffix = ' [Flash]'
        utils.addLink(title + suffix, onDemandStream.streamSet['flash'].replace('f4m', 'm3u8'), '', totalItems, showfanart)
    if istream and resolution != 'SD Only' and onDemandStream.streamSet['istream.hd'] != None:
        suffix = ' [iStream HD]'
        utils.addLink(title + suffix, onDemandStream.streamSet['istream.hd'], '', totalItems, showfanart)
    if istream and resolution != 'HD Only' and onDemandStream.streamSet['istream.sd'] != None:
        suffix = ' [iStream SD]'
        utils.addLink(title + suffix, onDemandStream.streamSet['istream.sd'].replace('f4m', 'm3u8'), '', totalItems, showfanart)
    if istream and resolution == 'All' and onDemandStream.streamSet['istream'] != None and onDemandStream.streamSet['istream'] != onDemandStream.streamSet['istream.hd']:
        suffix = ' [iStream]'
        utils.addLink(title + suffix, onDemandStream.streamSet['istream'], '', totalItems, showfanart)
    if progressiveUrl != None and resolution != 'SD Only' and onDemandStream.streamSet['istream.hd'] != None:
        suffix = ' [Progressive HD]'
        utils.addLink(title + suffix, ballstreams.deriveProgressiveUrl(onDemandStream.streamSet['istream.hd'],progressiveUrl), '', totalItems, showfanart)
    if progressiveUrl != None and resolution != 'HD Only' and onDemandStream.streamSet['istream.sd'] != None:
        suffix = ' [Progressive SD]'
        utils.addLink(title + suffix, ballstreams.deriveProgressiveUrl(onDemandStream.streamSet['istream.sd'].replace('f4m', 'm3u8'),progressiveUrl), '', totalItems, showfanart)
    if wmv and onDemandStream.streamSet['wmv'] != None:
        suffix = ' [WMV]'
        utils.addLink(title + suffix, onDemandStream.streamSet['wmv'], '', totalItems, showfanart)

    try:
        hTeam = onDemandStream.homeTeam
        dStr = datetime.datetime.strptime(dateStr, ' - %d %b \'%y')
        HIGHLIGHTSANDCONDENSED_BYTEAM_TEAMDATE(session, hTeam, dStr)
    except Exception as e:
        print 'Error initializing highlights/condensed: ' + str(e)

    setViewMode()

# Method to draw the live screen
# which scrapes the external source and presents
# a list of current day events
def LIVE(session):
    print 'LIVE(session)'

    # Find live events
    events = ballstreams.liveEvents(session)

    totalItems = len(events) + 2

    if totalItems > 13:
        # Add refresh button
        refreshParams = {
            'refresh': 'True'
        }
        utils.addDir(addon.getLocalizedString(100015), mode, '', refreshParams, totalItems, showfanart)

    for event in events:
        # Build prefix
        prefix = '[COLOR blue][B][LIVE][/B][/COLOR] '
        if event.isFuture:
            prefix = '[COLOR lightblue][Coming Soon][/COLOR] '
        elif event.isFinal:
            prefix = '[Final] '
        # Build matchup
        homeTeam = event.homeTeam if not shortNames else ballstreams.shortTeamName(event.homeTeam, addonPath)
        awayTeam = event.awayTeam if not shortNames else ballstreams.shortTeamName(event.awayTeam, addonPath)
        matchupStr = awayTeam + ' @ ' + homeTeam
        if awayTeam == '' or homeTeam == '': # Indicates special event
            matchupStr = awayTeam + homeTeam
        if event.feedType == 'Home Feed':
            matchupStr = matchupStr + '*'
        elif event.feedType == 'Away Feed':
            matchupStr = awayTeam + '* @ ' + homeTeam
        # Build period
        periodStr = ''
        if event.period == 'HALF - ':
            periodStr = ' - HALF'
        elif event.period != '':
            periodStr = ' - ' + event.period if event.period != None else ''
        # Build score
        homeScore = event.homeScore if event.homeScore != None and len(event.homeScore)>0 else '0'
        awayScore = event.awayScore if event.awayScore != None and len(event.awayScore)>0 else '0'
        scoreStr = ' - ' + awayScore + '-' + homeScore if showscores and not event.isFuture else ''
        # Build start time
        startTimeStr = ''
        if periodStr == '':
            startTimeStr = ' - ' + event.startTime
        # Build title
        title = prefix + event.event + ': ' + matchupStr + scoreStr + periodStr + startTimeStr
        if event.homeTeam == session.favteam or event.awayTeam == session.favteam:
            title = prefix + '[COLOR red][B]' + event.event + ': ' + matchupStr + scoreStr + periodStr + startTimeStr + '[/B][/COLOR]'

        if event.isFinal:
            now = ballstreams.adjustedDateTime()
            params = {
                'year': str(now.year),
                'month': str(now.month),
                'day': str(now.day)
            }
            utils.addDir(title, utils.Mode.ONDEMAND_BYDATE_YEARMONTH_DAY, '', params, totalItems, showfanart)
        elif event.isFuture:
            refreshParams = {
                'refresh': 'True'
            }
            utils.addDir(title, mode, '', refreshParams, totalItems, showfanart)
        else:
            params = {
                'eventId': event.eventId
            }
            utils.addDir(title, utils.Mode.LIVE_EVENT, '', params, totalItems, showfanart)

    # Add refresh button
    refreshParams = {
        'refresh': 'True'
    }
    utils.addDir(addon.getLocalizedString(100015), mode, '', refreshParams, totalItems, showfanart)

    setViewMode()

# Method to draw the live streams screen
# which scrapes the external source and presents
# a list of current day event streams for an event id
def LIVE_EVENT(session, eventId):
    print 'LIVE_EVENT(session, eventId)'
    print 'eventId: ' + eventId

    # Build streams
    liveStream = ballstreams.liveEventStreams(session, eventId, location)

    totalItems = 15 # max possible

    if liveStream == None or liveStream.streamSet == None:
        return None

    # Build prefix
    prefix = '[COLOR blue][B][LIVE][/B][/COLOR] '
    # Build matchup
    homeTeam = liveStream.homeTeam if not shortNames else ballstreams.shortTeamName(liveStream.homeTeam, addonPath)
    awayTeam = liveStream.awayTeam if not shortNames else ballstreams.shortTeamName(liveStream.awayTeam, addonPath)
    matchupStr = awayTeam + ' @ ' + homeTeam
    if awayTeam == '' or homeTeam == '': #indicates special event
        matchupStr = awayTeam + homeTeam
    if liveStream.feedType == 'Home Feed':
        matchupStr = matchupStr + '*'
    elif liveStream.feedType == 'Away Feed':
        matchupStr = awayTeam + '* @ ' + homeTeam
    # Build period
    periodStr = ''
    if liveStream.period == 'HALF - ':
        periodStr = ' - HALF'
    elif liveStream.period != '':
        periodStr = ' - ' + liveStream.period if liveStream.period != None else ''
    # Build score
    homeScore = liveStream.homeScore if liveStream.homeScore != None and len(liveStream.homeScore)>0 else '0'
    awayScore = liveStream.awayScore if liveStream.awayScore != None and len(liveStream.awayScore)>0 else '0'
    scoreStr = ' - ' + awayScore + '-' + homeScore if showscores else ''
    # Build start time
    startTimeStr = ''
    if periodStr == '':
        startTimeStr = ' - ' + liveStream.startTime
    # Build title
    title = prefix + liveStream.event + ': ' + matchupStr + scoreStr + periodStr + startTimeStr

    # Add links
    if truelive and resolution != 'SD Only' and liveStream.streamSet['truelive.hd'] != None:
        suffix = ' [TrueLive HD]'
        utils.addLink(title + suffix, liveStream.streamSet['truelive.hd'], '', totalItems, showfanart)
    if truelive and resolution != 'HD Only' and liveStream.streamSet['truelive.sd'] != None:
        suffix = ' [TrueLive SD]'
        utils.addLink(title + suffix, liveStream.streamSet['truelive.sd'], '', totalItems, showfanart)
    if flash and liveStream.streamSet['flash'] != None:
        suffix = ' [Flash]'
        utils.addLink(title + suffix, liveStream.streamSet['flash'].replace('f4m', 'm3u8'), '', totalItems, showfanart)
    if istream and resolution != 'SD Only' and liveStream.streamSet['istream.hd'] != None:
        suffix = ' [iStream HD]'
        utils.addLink(title + suffix, liveStream.streamSet['istream.hd'], '', totalItems, showfanart)
    if istream and resolution != 'HD Only' and liveStream.streamSet['istream.sd'] != None:
        suffix = ' [iStream SD]'
        utils.addLink(title + suffix, liveStream.streamSet['istream.sd'].replace('f4m', 'm3u8'), '', totalItems, showfanart)
    if istream and resolution == 'All' and liveStream.streamSet['istream'] != None and liveStream.streamSet['istream'] != liveStream.streamSet['istream.hd']:
        suffix = ' [iStream]'
        utils.addLink(title + suffix, liveStream.streamSet['istream'], '', totalItems, showfanart)
    if dvr and resolution != 'SD Only' and liveStream.streamSet['nondvrhd'] != None:
        suffix = ' [DVR HD]'
        utils.addLink(title + suffix, liveStream.streamSet['nondvrhd'], '', totalItems, showfanart)
    if dvr and resolution != 'HD Only' and liveStream.streamSet['nondvrsd'] != None:
        suffix = ' [DVR SD]'
        utils.addLink(title + suffix, liveStream.streamSet['nondvrsd'], '', totalItems, showfanart)
    if dvr and resolution == 'All' and liveStream.streamSet['nondvr'] != None:
        suffix = ' [DVR]'
        utils.addLink(title + suffix, liveStream.streamSet['nondvr'], '', totalItems, showfanart)
    if wmv and liveStream.streamSet['wmv'] != None:
        suffix = ' [WMV]'
        utils.addLink(title + suffix, liveStream.streamSet['wmv'], '', totalItems, showfanart)

    # Add refresh button
    refreshParams = {
        'refresh': 'True',
        'eventId': eventId
    }
    utils.addDir(addon.getLocalizedString(100015), mode, '', refreshParams, totalItems, showfanart)

    setViewMode()

# Method to populate recent events
# which scrapes the external source and presents
# a list of recent days events
def ONDEMAND_RECENT(session):
    print 'ONDEMAND_RECENT(session)'
    print 'daysback: ' + daysback

    # Check disable option
    if daysback == 'Disable':
        return

    # Loop daysback to Build event list
    i = 0
    while i <= int(daysback):
        # get current date
        recentDate = ballstreams.getRecentDateTime(i)

        # Build events for day
        ONDEMAND_BYDATE_YEARMONTH_DAY(session, recentDate.year, recentDate.month, recentDate.day)

        # Increment loop to avoid TO INFINITY AND BEYOND!!
        i += 1

# Set view mode according to addon settings
def setViewMode():
    if viewmode != None:
        try:
            xbmc.executebuiltin('Container.SetViewMode(' + viewmode + ')')
        except Exception as e:
            print 'Warning:  Unable to set view mode:  ' + str(e)

# Load general settings
username = addon.getSetting('username')
password = addon.getSetting('password')
resolution = addon.getSetting('resolution')
shortNames = addon.getSetting('shortnames')
shortNames = shortNames != None and shortNames.lower() == 'true'
showscores = addon.getSetting('showscores')
showscores = showscores != None and showscores.lower() == 'true'
showfanart = addon.getSetting('showfanart')
showfanart = showfanart != None and showfanart.lower() == 'true'
showhighlight = addon.getSetting('showhighlight')
showhighlight = showhighlight != None and showhighlight.lower() == 'true'
showcondensed = addon.getSetting('showcondensed')
showcondensed = showcondensed != None and showcondensed.lower() == 'true'
viewmode = addon.getSetting('viewmode')
if viewmode != None and viewmode == 'Big List':
    viewmode = '51'
elif viewmode != None and viewmode == 'List':
    viewmode = '50'
elif viewmode != None and viewmode == 'Thumbnail':
    viewmode = '500'
else: # Default
    viewmode = None

# Load stream settings
istream = addon.getSetting('istream')
istream = istream != None and istream.lower() == 'true'
flash = addon.getSetting('flash')
flash = flash != None and flash.lower() == 'true'
wmv = 'True'
truelive = addon.getSetting('truelive')
truelive = truelive != None and truelive.lower() == 'true'
dvr = addon.getSetting('dvr')
dvr = dvr != None and dvr.lower() == 'true'
location = addon.getSetting('location')
if location != None and location.lower() == 'auto':
    location = None # Location is special, if it is 'Auto' then it is None
daysback = addon.getSetting('daysback')
progressiveUrl = addon.getSetting('progressive')
if progressiveUrl == 'Disabled':
    progressiveUrl = None
elif progressiveUrl == 'Asia':
    progressiveUrl = 'http://119.81.135.3/vod5/'
elif progressiveUrl == 'Australia':
    progressiveUrl = 'http://168.1.75.9/vod5/'
elif progressiveUrl == 'Europe':
    progressiveUrl = 'http://159.8.16.17/vod5/'
elif progressiveUrl == 'North America - Central':
    progressiveUrl = 'http://198.23.71.68/vod5/'
elif progressiveUrl == 'North America - East':
    progressiveUrl = 'http://198.23.71.68/vod5/'
elif progressiveUrl == 'North America - East Canada':
    progressiveUrl = 'http://198.23.71.68/vod5/'
elif progressiveUrl == 'North America - West':
    progressiveUrl = 'http://198.23.71.68/vod5/'
elif progressiveUrl == 'Custom':
    progressiveCustomUrl = addon.getSetting('progressiveCustomUrl')
    if progressiveCustomUrl == None:
        progressiveUrl = None
    else:
        progressiveUrl = progressiveCustomUrl

# Load the directory params
params = utils.getParams()

# Print directory params for debugging
for k, v in params.iteritems():
    pass # print k + ': ' + v

# Parse mode
mode = utils.parseParamInt(params, 'mode')

# Parse other variables
year = utils.parseParamInt(params, 'year')
month = utils.parseParamInt(params, 'month')
day = utils.parseParamInt(params, 'day')
numberOfDays = utils.parseParamInt(params, 'numberOfDays')
league = utils.parseParamString(params, 'league')
team = utils.parseParamString(params, 'team')
eventId = utils.parseParamString(params, 'eventId')
feedType = utils.parseParamString(params, 'feedType')
dateStr = utils.parseParamString(params, 'dateStr')
invalid = utils.parseParamString(params, 'invalid')
invalid = invalid != None and invalid.lower() == 'true'
refresh = utils.parseParamString(params, 'refresh')
refresh = refresh != None and refresh.lower() == 'true'

# First check invalid stream else find mode and execute
if invalid:
    print 'Stream unavailable, please check ballstreams.com for wmv stream availability.'
    utils.showMessage(addon.getLocalizedString(100003), addon.getLocalizedString(100004))

# Check if username/password has been provided
if username == None or len(username) < 1 or password == None or len(password) < 1:
    addon.openSettings()
    # Reload settings
    username = addon.getSetting('username')
    password = addon.getSetting('password')

# Check if the user has entered valid settings
settingsInvalid = username == None or len(username) < 1 or password == None or len(password) < 1

# Set flags for end of directory
updateListing = invalid
cacheToDisc = True

# Perform a login
session = None
if settingsInvalid == False:
    try:
        session = ballstreams.login(username, password)
    except ballstreams.ApiException as e:
        print 'Error logging into ballstreams.com account: ' + str(e)

# Check login status and membership status
if session == None:
    mode = utils.Mode.HOME
    print 'The ballstreams.com session was null, login failed'
    utils.showMessage(addon.getLocalizedString(100011), addon.getLocalizedString(100012))
elif session.isPremium == False:
    mode = utils.Mode.HOME
    print 'The ballstreams.com account membership is non-premium, a paid for account is required'
    utils.showMessage(addon.getLocalizedString(100013), addon.getLocalizedString(100014))
else:
    # Attempt to create IP exception
    try:
        print 'Attempting to generate IP exception'
        ipException = ballstreams.ipException(session)
    except Exception as e:
        print 'Error creating an ip exception: ' + str(e)
        utils.showMessage(addon.getLocalizedString(100018), addon.getLocalizedString(100019))

# Invoke mode function
if mode == None or mode == utils.Mode.HOME:
    HOME()
elif mode == utils.Mode.ONDEMAND:
    ONDEMAND()
elif mode == utils.Mode.ONDEMAND_BYDATE:
    ONDEMAND_BYDATE(session)
elif mode == utils.Mode.ONDEMAND_BYDATE_YEARMONTH:
    ONDEMAND_BYDATE_YEARMONTH(session, year, month)
elif mode == utils.Mode.ONDEMAND_BYDATE_YEARMONTH_DAY:
    ONDEMAND_BYDATE_YEARMONTH_DAY(session, year, month, day)
elif mode == utils.Mode.ONDEMAND_BYDATE_YEARMONTH_DAY_EVENT:
    ONDEMAND_BYDATE_YEARMONTH_DAY_EVENT(session, eventId, feedType, dateStr)
elif mode == utils.Mode.ONDEMAND_BYDATE_CUSTOM:
    ONDEMAND_BYDATE_CUSTOM(session)
elif mode == utils.Mode.ONDEMAND_BYDATE_CUSTOM_YEARMONTH:
    ONDEMAND_BYDATE_CUSTOM_YEARMONTH(session, year, month)
elif mode == utils.Mode.ONDEMAND_BYDATE_CUSTOM_YEARMONTH_RANGE:
    ONDEMAND_BYDATE_CUSTOM_YEARMONTH_RANGE(session, year, month, day, numberOfDays)
elif mode == utils.Mode.ONDEMAND_BYTEAM:
    ONDEMAND_BYTEAM(session)
elif mode == utils.Mode.ONDEMAND_BYTEAM_LEAGUE:
    ONDEMAND_BYTEAM_LEAGUE(session,league)
elif mode == utils.Mode.ONDEMAND_BYTEAM_LEAGUE_TEAM:
    ONDEMAND_BYTEAM_LEAGUE_TEAM(session, league, team)
elif mode == utils.Mode.ONDEMAND_BYTEAM_LEAGUE_TEAM_EVENT:
    ONDEMAND_BYTEAM_LEAGUE_TEAM_EVENT(session, eventId, feedType, dateStr)
elif mode == utils.Mode.LIVE:
    LIVE(session)
    updateListing = refresh
    cacheToDisc = False
elif mode == utils.Mode.LIVE_EVENT:
    LIVE_EVENT(session, eventId)
    updateListing = refresh
    cacheToDisc = False

# Signal end of directory
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = cacheToDisc, updateListing = updateListing)
