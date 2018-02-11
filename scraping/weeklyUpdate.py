from bs4 import UnicodeDammit
from bs4 import BeautifulSoup
from mechanize import Browser
from collections import Counter
from getGameStats import *
from getPlayerStats import *
from findPlayer import *
from parseProjections import *
from datetime import datetime
import time
import re
import os
import sys
import MySQLdb as mdb

#CHANGE THE FOLLOWING LINE IF IT'S THE FIRST WEEK!!!
firstweek = True

monthNames = ['AUG','SEP','OCT','NOV','DEC','JAN','FEB']
weekdays = ['SUN','MON','TUE','WED','THU','FRI','SAT']
monthNums = ['08','09','10','11','12','01','02']
positionNames = ['Center','Cornerback','Defensive Back','Defensive End','Defensive Tackle','Defensive Lineman','Free Safety','Fullback','Halfback','Holder','Linebacker','Long Snapper','Nose Tackle','Offensive Guard','Offensive Lineman','Offensive Tackle','Place kicker','Punter','Quarterback','Running Back','Safety','Strong Safety','Tight End','Wide Receiver']
positions = ['C','CB','DB','DE','DT','DL','FS','FB','HB','H','LB','LS','NT','OG','OL','OT','PK','P','QB','RB','S','SS','TE','WR']
htmldir = os.getcwd() + "\\html\\"
projectionweek = 0

con = mdb.connect('pigskin.psych.indiana.edu','dba','password','pigskin')




#  EVERYTHING DEPENDS ON A DB CONNECTION
with con:
    cur = con.cursor()

#  DETERMINE THE MAXIMUM SEASON AND WEEK IN THE DB
#  ALSO MAKE A STRUCTURE OF THE GAMEIDS in the MAX WEEK
    cur.execute("SELECT CAST(MAX(season) AS CHAR) FROM games;")
    seasonResults = cur.fetchall()
    maxseason = seasonResults[0][0]
    cur.execute("SELECT CAST(MAX(week) AS CHAR) FROM games WHERE season = " + maxseason + ";")
    weekResults = cur.fetchall()
    maxweek = weekResults[0][0]
    #maxweek = '16'
    cur.execute("SELECT CAST(gameid AS CHAR) FROM games WHERE season = " + maxseason + " AND week = " + maxweek + ";")
    gameResults = cur.fetchall()
    gamesInMaxWeek = list()
    for gameResult in gameResults:
        gamesInMaxWeek.append(gameResult[0]) # clean up the results returned from DB
    if ((maxweek != '17')&(maxweek != '1'))&firstweek:
        print "FIRSTWEEK IS SET TO 'True' BUT THIS CAN'T BE, SINCE THE " + maxseason + " SEASON'S"
        print "DATA ISN'T YET COMPLETE IN THE DB. NOW THROWING YOU AN ERROR AND BREAKING."
        sys.exit("SEE ABOVE")
    else:
        print "DATABASE CURRENTLY STOPS AT WEEK " + maxweek + " OF THE " + maxseason + " SEASON. "
        print "CHECKING FOR LEFTOVER DATA FROM THIS WEEK..."

#  SCRAPE GAMEIDS FROM THE MAXWEEK & MAXSEASON TO FIND OUT
#  WHETHER WE CAN LOOK TO THE NEXT WEEK...
    mech = Browser()
    if firstweek:
        week = '1'
    else:
        week = str(int(maxweek)+1)
    #url = "http://espn.go.com/nfl/schedule/_/year/{0!s}/seasontype/2".format(maxseason)
    #url = "http://espn.go.com/nfl/schedule/_/week/{0!s}".format(week)
    url = "http://espn.go.com/nfl/schedule/_/seasontype/2/week/{0!s}".format(week)
    page = mech.open(url)
    html = page.read()
    soup = BeautifulSoup(str(html))
    table=soup.findAll("table","tablehead")[0]
    gamesInMaxWeekScraped = list()
    played = True # ASSUME THE GAMES ARE ALL READY TO SCRAPE
    for row in table.findAll('tr')[1:]:
        col = row.findAll('td')[0]
        if col.get_text().strip().encode("latin-1")[0:3] in weekdays:
            # WE FOUND A DATE LINE
            #  -- CHECK THAT THE DATE IS IN THE PAST
            month = col.get_text().strip().encode("latin-1")[5:8]
            day = col.get_text().strip().encode("latin-1")[9:]
            if month == 'JAN':
                year = str(int(maxseason)+1)
            else:
                year = maxseason
            gameday = datetime.strptime(day+' '+month+' '+year,"%d %b %Y")
            today = datetime.today()
            #today = datetime.strptime('12 SEP 2011',"%d %b %Y")
            if today.date() <= gameday.date():
                played = False # THE GAMES AREN'T IN THE PAST
        elif played:
            # WE HAVEN'T FOUND A DATE IN THE FUTURE YET
            # CHECK THAT WE'RE NOT TRYING TO SCRAPE TEAMS on BYE
            if col.get_text()[1:4].encode("latin-1") != 'Bye':
                gameURL = col.find("a").get("href")
                gameID = gameURL[gameURL.index("=")+1:]
                gamesInMaxWeekScraped.append(gameID)
    A = Counter(gamesInMaxWeek)
    B = Counter(gamesInMaxWeekScraped)
    newgameids = []
    if len(list((B-A).elements())) > 0:
        lastweek = str(int(maxweek)-1)
        projectionweek = lastweek
        week = maxweek
        season = maxseason
        print "THERE'RE NEW STATS FROM WEEK " + maxweek + " (" + str(len(list((B-A).elements()))) + " GAMES). "
        print "PROCEEDING TO RESCRAPE WEEK " + week + ", AND REVISE THE PRIOR WEEK..."
        newgameids = list((B-A).elements())
    elif firstweek:
        lastweek = str(int(maxweek)-1)
        week = maxweek
        season = maxseason
        print "THERE'RE NO NEW STATS FROM WEEK " + maxweek + " (" + str(len(list((B-A).elements()))) + " GAMES). "
        print "JUST REVISING WEEK 1. SET FIRSTWEEK TO 'False' to advance to the next week."
        newgameids = list((B-A).elements())
        projectionweek = 0
        week = '1'
        season = str(int(maxseason)+1)
        print "NO LEFTOVER DATA. ATTEMPTING TO SCRAPE WEEK 1 OF THE " + str(int(maxseason)+1) + " SEASON..."
    elif maxweek == '17':
        season = maxseason
        lastweek = maxweek
        week = '0'
        projectionweek = 17
        print "" + maxseason + "'S DATA SEEMS TO BE COMPLETE."
        print "ATTEMPTING TO REVISE WEEK " + lastweek + " OF THE " + maxseason + " SEASON..."
    else:
        lastweek = maxweek
        week = str(int(maxweek)+1)
        season = maxseason
        projectionweek = maxweek
        print "IT SEEMS LIKE WEEK " + maxweek + " IS COMPLETE. "
        print "ATTEMPTING TO SCRAPE WEEK " + week + ", AND REVISE THE PRIOR WEEK..."

#  NOW THAT WE KNOW WHERE WE'RE AT, WE CAN FINALLY 
#  RETRIEVE CURRENT WEEK'S GAMEIDS, IF ANY EXIST
    if firstweek:
        url = "http://espn.go.com/nfl/schedule/_/year/{0!s}/seasontype/2".format(season)
        page = mech.open(url)
        html = page.read()
        thefile = season + "_season.html"
        filename = os.path.join(os.path.dirname(htmldir), thefile)
        #filename = "C:\Users\Ben Motz\Documents\SCRAPING\html\\" + season + "_season.html"
        f = open(filename,"w")
        f.write(html)
        f.close()
        soup = BeautifulSoup(str(html))
    if (len(newgameids)==0)&(week!='0'):
        played = True # ASSUME THE GAMES ARE ALL READY TO SCRAPE
        #table=soup.findAll("table","tablehead")[int(week)-1]
        table=soup.findAll("table","tablehead")[0]
        for row in table.findAll('tr')[1:]:
            col = row.findAll('td')[0]
            if col.get_text().strip().encode("latin-1")[0:3] in weekdays:
                # WE FOUND A DATE LINE
                #  -- CHECK THAT THE DATE IS IN THE PAST
                month = col.get_text().strip().encode("latin-1")[5:8]
                day = col.get_text().strip().encode("latin-1")[9:]
                if month == 'JAN':
                    year = str(int(season)+1)
                else:
                    year = season
                gameday = datetime.strptime(day+' '+month+' '+year,"%d %b %Y")
                today = datetime.today()
                #today = datetime.strptime('12 SEP 2011',"%d %b %Y")
                if today.date() <= gameday.date():
                    played = False # THE GAMES HAVEN'T NECESSARILY HAPPENED YET
            elif played:
                # WE HAVEN'T FOUND A DATE IN THE FUTURE YET
                # CHECK THAT WE'RE NOT TRYING TO SCRAPE TEAMS on BYE
                if col.get_text()[1:4].encode("latin-1") != 'Bye':
                    gameURL = col.find("a").get("href")
                    gameID = gameURL[gameURL.index("=")+1:]
                    newgameids.append(gameID)
        if len(newgameids) == 0 & firstweek:
            print "NO NEW GAMES FROM THE NEW SEASON YET. THERE'S NOTHING TO DO."
            print "NOW THROWING YOU AN ERROR AND BREAKING."
            sys.exit("SEE ABOVE")
        elif len(newgameids) == 0: 
            print "IT SEEMS THAT WE'RE BETWEEN WEEKS; NO NEW GAMEIDS TO SCRAPE."
            print "PROCEEDING TO RESCRAPE THE PREVIOUS WEEK."
        else:
            print 'GAMEIDs RETRIEVED. ' + str(len(newgameids)) + ' games\'ve been played in Week ' + week + ' of the ' + season + ' season.'

#  AT THIS POINT, IF THERE'RE NEW GAMES TO SCRAPE, WE'VE GOT
#  THEIR GAMEIDS.  GOOD.  HOLD OFF UNTIL WE'VE FIGURED OUT
#  WHAT GAMES NEED TO BE RESCRAPED FROM THE PREVIOUS WEEK.

#  RETRIEVE *LAST-WEEK'S* GAMEIDS, CAN COME DIRECT FROM THE DB
    oldgameids = []
    if firstweek:
        nothing = '0'
    else:
        cur.execute("SELECT CAST(gameid AS CHAR) FROM games WHERE season = " + season + " AND week = " + lastweek + ";")
        lastweekResults = cur.fetchall()
        for g in lastweekResults:
            oldgameids.append(g[0])
        print 'LAST WEEK\'S GAMEIDS RETRIEVED. There were ' + str(len(lastweekResults)) + ' in Week ' + lastweek + '.'

#  MERGE LAST WEEK AND CURRENT WEEK
    gameids = oldgameids + newgameids

#  RETRIEVE PAGES FOR ALL GAMES
#  OVERWRITE OLD FILES
#  IF FAILS, ABORT EVERYTHING <- should happen automatically
    print 'FETCHING CURRENT ESPN BOX SCORE AND PLAY-BY-PLAY PAGES...'
    for g in gameids:
        print ".",
        boxURL = 'http://espn.go.com/nfl/boxscore?gameId=' + g
        page = mech.open(boxURL)
        html = page.read()
        thefile = 'boxscore_' + g + '.html'
        target = os.path.join(os.path.dirname(htmldir), thefile)
        #target = 'C:\Users\Ben Motz\Documents\SCRAPING\html\\boxscore_' + g + '.html'
        w = open(target,"w")
        w.write(html)
        w.close()
        playbyplayURL = 'http://espn.go.com/nfl/playbyplay?gameId=' + g + '&period=0'
        page = mech.open(playbyplayURL)
        html = page.read()
        thefile = 'playbyplay_' + g + '.html'
        target = os.path.join(os.path.dirname(htmldir), thefile)
        #target = 'C:\Users\Ben Motz\Documents\SCRAPING\html\\playbyplay_' + gameID + '.html'
        w = open(target,"w")
        w.write(html)
        w.close()
    print "\n" + 'ESPN PAGES RETRIEVED.  NOW SEARCHING FOR NEW PLAYERS...'

#  CREATE TEMPORARY TABLE WITH
#  ALL PLAYER_IDS FROM CURRENT
#  AND LAST WEEK
    weeksPlayers = []
    for g in gameids:
        print ".",
        thefile = 'boxscore_' + g + '.html'
        source = os.path.join(os.path.dirname(htmldir), thefile)
        #source = "C:\Users\Ben Motz\Documents\SCRAPING\html\\boxscore_" + g + ".html"
        w = open(source,"r")
        html = w.readlines()
        w.close()
        soup = BeautifulSoup(str(html))
        playerLinks = soup.find_all(href=re.compile("http://espn.go.com/nfl/player/_/id/.*"))
        for i in playerLinks:
            playerURL = i.get("href")
            playerID = re.findall("\d+",playerURL)[0] # find the number in the url
            weeksPlayers.append(playerID)
    weeksPlayers = list(set(weeksPlayers)) # dedupe
    cur.execute("CREATE TEMPORARY TABLE weeksPlayers (playerid INT);")
    for p in weeksPlayers:
        cur.execute("INSERT INTO weeksPlayers (playerid) VALUES (\"" + p + "\");")
    cur.execute("SELECT CAST(playerid AS CHAR) FROM weeksPlayers w WHERE NOT EXISTS (SELECT 1 FROM players p WHERE w.playerid = p.playerid);")
    newPlayerResults = cur.fetchall()
    newPlayers = []
    for i in range(0,len(newPlayerResults)):
        newPlayers.append(newPlayerResults[i][0])
    cur.execute("DROP TEMPORARY TABLE weeksPlayers;")
    if len(newPlayers) == 1:
        print "\n" + 'THERE WAS 1 NEW PLAYER FOUND. NOW RETRIEVING HIS PLAYER PAGE...'
    elif len(newPlayers) == 0:
        print "\n" + 'THERE WERE NO NEW PLAYERS FOUND.'
    else:
        print "\n" + '' + str(len(newPlayers)) + ' NEW PLAYERS FOUND. RETRIEVING THEIR PLAYER PAGES...'
        

#  FOR ANY PLAYERS NOT IN THE
#  PLAYERS TABLE, DOWNLOAD THEIR
#  PAGES, ADD INFO TO PLAYERS
#  TABLE
    for p in newPlayers:
        thefile = 'player_' + p + '.html'
        playerfile = os.path.join(os.path.dirname(htmldir), thefile)
        #playerfile = "C:\Users\Ben Motz\Documents\SCRAPING\html\\player_" + p + ".html"
        if not os.path.isfile(playerfile):
            page = mech.open("http://espn.go.com/nfl/player/stats/_/id/" + p)
            playerhtml = page.read()
            x = open(playerfile,"w")
            x.write(playerhtml)
            x.close()
        f = open(playerfile,"r")
        html = f.readlines()
        f.close()
        soup = BeautifulSoup(str(html))
        fullname = soup.findAll(attrs={"property":"og:title"})[0].get("content")
        playerdetail = soup.findAll("li","first")[0].get_text().strip().encode("latin-1")    
        if playerdetail.find('#') != -1:
            position = playerdetail[playerdetail.find(' ')+1:]
        else:
            try:
                position = positions[positionNames.index(playerdetail)]
            except ValueError:
                print str(i) + ': ' + playerdetail
        try:
            playerbirthdate = soup.findAll("span",text='Born')[0].parent.get_text().replace('Born','').strip().encode("latin-1")
            pbstop = playerbirthdate.find('(Age:')
            if pbstop != -1:
                playerbirthdate = playerbirthdate[0:pbstop-1]
            birthplaceFlag = playerbirthdate.find(" in ")
            if birthplaceFlag != -1:
                playerbirthdate = playerbirthdate[0:birthplaceFlag]
            c = time.strptime(playerbirthdate, "%b %d, %Y")
            playerbirthdate = time.strftime("%d %b %Y",c)
        except IndexError:
            playerbirthdate = '01 Jan 1900'
        date = time.strftime("%Y-%m-%d",c)
        cur.execute("INSERT INTO players (playerid, fullname, position, birthdate) \
                     VALUES (\"" + p + "\", \"" + fullname + "\", \"" + position + "\", \"" + date + "\")")
    if len(newPlayers) > 1:
        print 'PLAYER DATA RETRIEVED, SAVED, AND INSERTED INTO DATABASE.'

#  SCRAPE AND INSERT DATA FOR GAMES TABLE
    print 'SCRAPING DETAILS ABOUT GAMES, AND UPDATING DATABASE...'
    for gameid in gameids:
        print ".",
        if gameid in newgameids:
            gameweek = week
        elif gameid in oldgameids:
            gameweek = lastweek
        else:
            # THIS REALLY SHOULDN'T HAPPEN, BUT I CAN'T RESIST:
            sys.exit("CAN'T IDENTIFY A GAMEIDS'S WEEK. TYPE gameid TO CHECK DETAIL")
        values = getGameDetails(gameweek, season, gameid)
        cur.execute("REPLACE INTO games VALUES (" + values + ");")
    print "\n" + 'SCRAPED AND INSERTED DETAILS ABOUT GAMES.'

#  SCRAPE AND INSERT PROJECTION DATA
##    print 'SCRAPING DETAILS ABOUT PLAYER PROJECTIONS, AND UPDATING DATABASE...'
##    if projectionweek > 0:
##        categories = ['0','2','4','6','16','17']
##        catLabels = ['QB','RB','WR','TE','DST','PK']
##        for categoryID in categories:
##            projectionURL = 'http://games.espn.go.com/ffl/tools/projections?&slotCategoryId={0!s}&startIndex=0&scoringPeriodId={1!s}&seasonId={2!s}'.format(categoryID,projectionweek,season)
##            page = mech.open(projectionURL)
##            html = page.read()
##            thefile = 'projection_' + projectionweek + '_' + catLabels[categories.index(categoryID)] + '.html'
##            target = os.path.join(os.path.dirname(htmldir), thefile)
##            w = open(target,"w")
##            w.write(html)
##            w.close()
##            projInsert = parseProjections(target)
##            cur.execute(projInsert)
##    print 'PROJECTIONS FOR WEEK ' + projectionweek + ' INSERTED INTO DATABASE'

#  SCRAPE AND INSERT PLAYER STATS FOR EACH GAME
    print 'SCRAPING PLAYER STATS FOR EACH GAME...',
    cur.connection.autocommit(True)
    for gameid in gameids:
        print "\n  GAMEID " + gameid + ":",
        if gameid in newgameids:
            gameweek = week
        elif gameid in oldgameids:
            gameweek = lastweek
        thefile = 'boxscore_' + gameid + '.html'
        gameFilename = os.path.join(os.path.dirname(htmldir), thefile)
        #gameFilename = "C:\Users\Ben Motz\Documents\SCRAPING\html\\boxscore_" + gameid + ".html"
        f = open(gameFilename,"r")
        html = f.readlines()
        f.close()
        soup = BeautifulSoup(str(html))
        gameYear = str(int(gameid[0:2])+1980)
        gameMonth = gameid[2:4]
        gameDay = gameid[4:6]
        gameDatetime = datetime.strptime(gameDay+' '+gameMonth+' '+gameYear,"%d %m %Y")
        gameWeekday = datetime.strftime(gameDatetime,"%a").upper()
        gameDate = datetime.strftime(gameDatetime,"%Y-%m-%d")
        # EACH OF THESE MySQL COMMANDS (strings) ARE DEFINED IN getPlayerStats
        # THEY CREATE TEMPORARY TABLES, WHICH ARE EMPTY UNTIL THE NEXT STEP
        cur.execute(createPassing)
        cur.execute(createRushing)
        cur.execute(createReceiving)
        cur.execute(createFumbles)
        cur.execute(createKicking)
        cur.execute(createFumbleReturn)
        cur.execute(createTwoPointConversions)
        cur.execute(createOffense)
        cur.execute(createDefense)
        # NOW BEGIN POPULATING THE TEMPORARY TABLES
        cur.execute(getPassing(soup))
        print ".",
        cur.execute(getRushing(soup))
        print ".",
        cur.execute(getReceiving(soup))
        print ".",
        if getFumbles(soup) != "":
            cur.execute(getFumbles(soup))
        print ".",
        cur.execute(getKicking(soup))
        print ".",
        if getFumbleReturnTD(soup) != "":
            cur.execute(getFumbleReturnTD(soup))
        print ".",
        cur.execute(getDefense(soup))
        print ".",
        if getTwoPointConversions(soup) != "":
            cur.execute(getTwoPointConversions(soup))
        print ".",
        # BUILD THE BIG OFFENSE TABLE
        cur.execute("CREATE TEMPORARY TABLE offenders AS (SELECT gameid,playerID,team,opponent FROM passTemp) " + \
                                                  "UNION (SELECT gameid,playerID,team,opponent FROM rushTemp) " + \
                                                  "UNION (SELECT gameid,playerID,team,opponent FROM receivingTemp) " + \
                                                  "UNION (SELECT gameid,playerID,team,opponent FROM fumbleTemp) " + \
                                                  "UNION (SELECT gameid,playerID,team,opponent FROM fumbleReturnTemp) " + \
                                                  "UNION (SELECT gameid,playerID,team,opponent FROM twoPtConversionTemp);")
        offenseBuild = "INSERT INTO offenseTemp (gameid,playerID,fullname,team,opponent,position," + \
                       "passAtt,passComp,passYds,passTDs,passINT," + \
                       "rushAtt,rushYds,rushTDs," + \
                       "receptions,recYds,recTDs," + \
                       "fumblesLost, fumblesReturned, twoPointConvs) " + \
                       "SELECT DISTINCT a.gameid, a.playerid, x.fullname, a.team, a.opponent, x.position, " + \
                       "SUM(IFNULL(b.passAtt,0)), SUM(IFNULL(b.passComp,0)), SUM(IFNULL(b.passYds,0)), SUM(IFNULL(b.passTDs,0)), SUM(IFNULL(b.passINT,0)), " + \
                       "SUM(IFNULL(c.rushAtt,0)), SUM(IFNULL(c.rushYds,0)), SUM(IFNULL(c.rushTDs,0)), " + \
                       "SUM(IFNULL(d.receptions,0)), SUM(IFNULL(d.recYds,0)), SUM(IFNULL(d.recTDs,0)), " + \
                       "SUM(IFNULL(e.fumblesLost,0)), SUM(IFNULL(f.fumblesReturned,0)), COUNT(g.conversiontype) " + \
                       "FROM offenders a " + \
                       "LEFT JOIN passTemp b ON a.playerID = b.playerID " + \
                       "LEFT JOIN rushTemp c ON a.playerID = c.playerID " + \
                       "LEFT JOIN receivingTemp d ON a.playerID = d.playerID " + \
                       "LEFT JOIN fumbleTemp e ON a.playerID = e.playerID " + \
                       "LEFT JOIN fumbleReturnTemp f ON a.playerID = f.playerID " + \
                       "LEFT JOIN twoPtConversionTemp g ON a.playerID = g.playerID " + \
                       "LEFT JOIN players x ON a.playerID = x.playerID " + \
                       "GROUP BY a.gameid, a.playerid, x.fullname, a.team, a.opponent, x.position;"
        cur.execute(offenseBuild)
        print ".",
        # ADD FANTASY POINTS TO THE TEMPORARY TABLES
        cur.execute("ALTER TABLE offenseTemp ADD fantasyPoints DOUBLE(5,2) AFTER position;")
        cur.execute("ALTER TABLE kickTemp ADD fantasyPoints DOUBLE(5,2) AFTER position;")
        cur.execute("ALTER TABLE defenseTemp ADD fantasyPoints DOUBLE(5,2) AFTER position;")
        cur.execute("SET SQL_SAFE_UPDATES=0;")
        print ".",
        # OUT WITH THE OLD, AND IN WITH THE NEW
        cur.execute("DELETE FROM offense WHERE gameid = " + gameid + ";")
        cur.execute("INSERT INTO offense (SELECT gameid,"+gameweek+","+season+",playerID,fullname,team,opponent,position,fantasyPoints,passAtt,passComp,passYds,passTDs,passINT,rushAtt,rushYds,rushTDs,receptions,recYds,recTDs,fumblesLost, fumblesReturned, twoPointConvs FROM offenseTemp);")
        cur.execute("DELETE FROM kicking WHERE gameid = " + gameid + ";")
        cur.execute("INSERT INTO kicking (SELECT a.gameid,"+gameweek+","+season+",a.playerID,x.fullname,a.team,a.opponent,a.position,a.fantasyPoints,IFNULL(a.attXP,0),IFNULL(a.madeXP,0),IFNULL(a.att00_29,0),IFNULL(a.made00_29,0),IFNULL(a.att30_39,0),IFNULL(a.made30_39,0),IFNULL(a.att40_49,0),IFNULL(a.made40_49,0),IFNULL(a.att50_up,0),IFNULL(a.made50_up,0) FROM kickTemp a LEFT JOIN players x ON a.playerid = x.playerid);")
        cur.execute("DELETE FROM defenseandspecialteams WHERE gameid = " + gameid + ";")
        cur.execute("INSERT INTO defenseAndSpecialTeams (SELECT a.gameid,"+gameweek+","+season+",a.playerID,x.fullname,a.team,a.opponent,a.position,a.fantasyPoints,IFNULL(a.tackles,0),IFNULL(a.sacks,0),IFNULL(a.interceptions,0),IFNULL(a.fumblesRecovered,0),IFNULL(a.safeties,0),IFNULL(a.defensiveTDs,0),IFNULL(a.returnTDs,0),IFNULL(a.ptsAllowed,0) FROM defenseTemp a LEFT JOIN players x ON a.playerid = x.playerid);")
        # CALCULATE FANTASY POINTS
        cur.execute(offensePoints) # EACH OF THESE MySQL COMMANDS (strings) ARE DEFINED IN getPlayerStats
        cur.execute(kickingPoints)
        cur.execute(defensePoints1)
        cur.execute(defensePoints2)
        cur.execute(defensePoints3)
        cur.execute(defensePoints4)
        cur.execute(defensePoints5)
        cur.execute(defensePoints6)
        cur.execute(defensePoints7)
        print ".",
        # NOW DROP THE TEMPORARY TABLES SO THAT WE 
        # CAN MAKE FRESH ONES FOR THE NEXT GAME
        cur.execute(dropTempTables)
    print '\nALL PLAYER STATS SUCCESSFULLY INSERTED INTO DATABASE.'



con.close()

