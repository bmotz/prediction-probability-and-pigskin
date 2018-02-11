from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from datetime import datetime
import time
import re
import os

def getSec(s):
    l = s.split(':')
    return str(int(l[0]) * 60 + int(l[1]))

def getGameDetails(gameweek, season, gameid):
    htmldir = os.getcwd() + "\\html\\"
    thefile = "boxscore_" + gameid + ".html"
    gameFilename = os.path.join(os.path.dirname(htmldir), thefile)
    #gameFilename = "C:\Users\Ben Motz\Documents\SCRAPING\html\\boxscore_" + gameid + ".html"
    f = open(gameFilename,"r")
    html = f.readlines()
    f.close()
    soup = BeautifulSoup(str(html))
    #gameYear = str(int(gameid[0:2])+1980)
    #gameMonth = gameid[2:4]
    #gameDay = gameid[4:6]
    gameDayTimeStr = soup.findAll("div","game-time-location")[0].findAll("p")[0].get_text().strip().encode("latin-1")
    gameDayStr = gameDayTimeStr[gameDayTimeStr.index(",")+2:] # 'September 4, 2014'
    gameDatetime = datetime.strptime(gameDayStr,"%B %d, %Y")
    gameWeekday = datetime.strftime(gameDatetime,"%a").upper()
    gameDate = datetime.strftime(gameDatetime,"%Y-%m-%d")
    teaminfo = soup.findAll("div","team-info")
    awayRecord = soup.findAll(text=re.compile("away\)"))[0].strip().encode("latin-1")
    awayWins = awayRecord[1:awayRecord.index("-")]
    awayLosses = awayRecord[awayRecord.index("-")+1:awayRecord.index(",")]
    homeRecord = soup.findAll(text=re.compile("home\)"))[0].strip().encode("latin-1")
    homeWins = homeRecord[1:homeRecord.index("-")]
    homeLosses = homeRecord[homeRecord.index("-")+1:homeRecord.index(",")]
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    awayScore = teaminfo[0].findAll("span")[0].get_text().strip().encode("latin-1")
    homeScore = teaminfo[1].findAll("span")[0].get_text().strip().encode("latin-1")
    if int(awayScore) > int(homeScore):
        awayWins = str(int(awayWins) - 1)
        if homeLosses.count("-") > 0:
            homeLosses = str(int(homeLosses[:homeLosses.index("-")]) - 1)
        else:
            homeLosses = str(int(homeLosses) - 1)
    elif int(awayScore) < int(homeScore):
        homeWins = str(int(homeWins) - 1)
        if awayLosses.count("-") > 0:
            awayLosses = str(int(awayLosses[:awayLosses.index("-")]) - 1)
        else:
            awayLosses = str(int(awayLosses) - 1)
    else:
        if homeLosses.count("-") > 0:
            homeLosses = str(int(homeLosses[:homeLosses.index("-")]))
        elif awayLosses.count("-") > 0:
            awayLosses = str(int(awayLosses[:awayLosses.index("-")]))
        else:
            nothing = "0"
    gameLocation = soup.findAll("div","game-time-location")[0].findAll("p")[1].get_text().strip().encode("latin-1")
    gameTimeDirty = soup.findAll("div","game-time-location")[0].findAll("p")[0].get_text()[:soup.findAll("div","game-time-location")[0].findAll("p")[0].get_text().index(",")].strip().encode("latin-1")
    hour = gameTimeDirty[:gameTimeDirty.index(":")]
    if "AM" in gameTimeDirty:
        hour = hour
    else:
        hour = str(int(hour) + 12)
    minute = gameTimeDirty[gameTimeDirty.index(":")+1:gameTimeDirty.index(":")+3]
    gameTime = hour + ":" + minute + ":00"
    gameCoverage = soup.findAll(text=re.compile("Coverage"))[0].parent.findAll("strong")[0].get_text().strip().encode("latin-1")
    gameCoverage = gameCoverage.replace("/WatchESPN","") 
    gameAttendanceDirty = soup.findAll(text="Attendance:")[0].parent.next_sibling.strip().encode("latin-1")
    gameAttendance = gameAttendanceDirty.replace(",","")
    if gameAttendance == 'NA':
        gameAttendance = 'NULL'
    gameStatTable = soup.findAll(text="Team Stat Comparison")[0].parent.parent.next_sibling.findAll("table")[0]
    for row in gameStatTable.findAll('tr')[1:]:
        col = row.findAll('td')
        if col[0].get_text().strip().encode("latin-1") == '1st Downs':
            away1stDowns = col[1].get_text().strip().encode("latin-1")
            home1stDowns = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == '3rd down efficiency':
            away3rdDownConv = col[1].get_text().strip().encode("latin-1")[:col[1].get_text().strip().encode("latin-1").index("-")]
            home3rdDownConv = col[2].get_text().strip().encode("latin-1")[:col[2].get_text().strip().encode("latin-1").index("-")]
            away3rdDownAtt  = col[1].get_text().strip().encode("latin-1")[col[1].get_text().strip().encode("latin-1").index("-")+1:]
            home3rdDownAtt  = col[2].get_text().strip().encode("latin-1")[col[2].get_text().strip().encode("latin-1").index("-")+1:]
        elif col[0].get_text().strip().encode("latin-1") == '4th down efficiency':
            away4thDownConv = col[1].get_text().strip().encode("latin-1")[:col[1].get_text().strip().encode("latin-1").index("-")]
            home4thDownConv = col[2].get_text().strip().encode("latin-1")[:col[2].get_text().strip().encode("latin-1").index("-")]
            away4thDownAtt  = col[1].get_text().strip().encode("latin-1")[col[1].get_text().strip().encode("latin-1").index("-")+1:]
            home4thDownAtt  = col[2].get_text().strip().encode("latin-1")[col[2].get_text().strip().encode("latin-1").index("-")+1:]
        elif col[0].get_text().strip().encode("latin-1") == 'Total Yards':
            awayYards = col[1].get_text().strip().encode("latin-1")
            homeYards = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Passing':
            awayPassingYards = col[1].get_text().strip().encode("latin-1")
            homePassingYards = col[2].get_text().strip().encode("latin-1")
        elif (col[0].get_text().strip().encode("latin-1")=='Comp-Att')|(col[0].get_text().strip().encode("latin-1")=='Comp - Att'):
            awayPassComp = col[1].get_text().strip().encode("latin-1")[:col[1].get_text().strip().encode("latin-1").index("-")]
            homePassComp = col[2].get_text().strip().encode("latin-1")[:col[2].get_text().strip().encode("latin-1").index("-")]
            awayPassAtt  = col[1].get_text().strip().encode("latin-1")[col[1].get_text().strip().encode("latin-1").index("-")+1:]
            homePassAtt  = col[2].get_text().strip().encode("latin-1")[col[2].get_text().strip().encode("latin-1").index("-")+1:]
        elif col[0].get_text().strip().encode("latin-1") == 'Rushing':
            awayRushingYards = col[1].get_text().strip().encode("latin-1")
            homeRushingYards = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Rushing Attempts':
            awayRushingAtt = col[1].get_text().strip().encode("latin-1")
            homeRushingAtt = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Penalties':
            awayPenaltyCount = col[1].get_text().strip().encode("latin-1")[:col[1].get_text().strip().encode("latin-1").index("-")]
            homePenaltyCount = col[2].get_text().strip().encode("latin-1")[:col[2].get_text().strip().encode("latin-1").index("-")]
            awayPenaltyYards  = col[1].get_text().strip().encode("latin-1")[col[1].get_text().strip().encode("latin-1").index("-")+1:]
            homePenaltyYards  = col[2].get_text().strip().encode("latin-1")[col[2].get_text().strip().encode("latin-1").index("-")+1:]
        elif col[0].get_text().strip().encode("latin-1") == 'Turnovers':
            awayTurnovers = col[1].get_text().strip().encode("latin-1")
            homeTurnovers = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Fumbles lost':
            awayFumblesLost = col[1].get_text().strip().encode("latin-1")
            homeFumblesLost = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Interceptions thrown':
            awayInterceptionsThrown = col[1].get_text().strip().encode("latin-1")
            homeInterceptionsThrown = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Possession':
            awayPossessionSeconds = getSec(col[1].get_text().strip().encode("latin-1"))
            homePossessionSeconds = getSec(col[2].get_text().strip().encode("latin-1"))
        else:
            nothing = '0'
    lineScoreTable = soup.findAll("table","linescore")[0]
    awayQ1points = lineScoreTable.findAll('tr')[1].findAll('td')[1].get_text().strip().encode("latin-1")
    awayQ2points = lineScoreTable.findAll('tr')[1].findAll('td')[2].get_text().strip().encode("latin-1")
    awayQ3points = lineScoreTable.findAll('tr')[1].findAll('td')[3].get_text().strip().encode("latin-1")
    awayQ4points = lineScoreTable.findAll('tr')[1].findAll('td')[4].get_text().strip().encode("latin-1")
    homeQ1points = lineScoreTable.findAll('tr')[2].findAll('td')[1].get_text().strip().encode("latin-1")
    homeQ2points = lineScoreTable.findAll('tr')[2].findAll('td')[2].get_text().strip().encode("latin-1")
    homeQ3points = lineScoreTable.findAll('tr')[2].findAll('td')[3].get_text().strip().encode("latin-1")
    homeQ4points = lineScoreTable.findAll('tr')[2].findAll('td')[4].get_text().strip().encode("latin-1")
    if len(lineScoreTable.findAll('tr')[0].findAll('td')) > 6:
        awayOTpoints = lineScoreTable.findAll('tr')[1].findAll('td')[5].get_text().strip().encode("latin-1")
        homeOTpoints = lineScoreTable.findAll('tr')[2].findAll('td')[5].get_text().strip().encode("latin-1")
        bigstring = "\"" + gameid + "\", " + gameweek + ", " + season + ", \"" + gameDate + "\", \"" + gameWeekday + "\" , \"" + awayTeam + "\" , \"" + homeTeam + "\" , " + awayScore + " , " + homeScore + " , \"" + gameLocation + "\" , \"" + gameTime + "\" , \"" + gameCoverage + "\" , " + gameAttendance + " , " + awayWins + " , " + awayLosses + " , " + homeWins + " , " + homeLosses + " , " + away1stDowns + " , " + home1stDowns + " , " + away3rdDownConv + " , " + home3rdDownConv + " , " + away3rdDownAtt + " , " + home3rdDownAtt + " , \
                    " + away4thDownConv + " , " + home4thDownConv + " , " + away4thDownAtt + " , " + home4thDownAtt + " , \
                    " + awayYards + " , " + homeYards + " , " + awayPassingYards + " , " + homePassingYards + " , " + awayPassComp + " , " + homePassComp + " , \
                    " + awayPassAtt + " , " + homePassAtt + " , " + awayRushingYards + " , " + homeRushingYards + " , \
                    " + awayRushingAtt + " , " + homeRushingAtt + " , " + awayPenaltyCount + " , " + homePenaltyCount + " , " + awayPenaltyYards + " , " + homePenaltyYards + " , \
                    " + awayTurnovers + " , " + homeTurnovers + " , " + awayFumblesLost + " , " + homeFumblesLost +  " , \
                    " + awayInterceptionsThrown + " , " + homeInterceptionsThrown + " , " + awayPossessionSeconds + " , " + homePossessionSeconds + " , \
                    " + awayQ1points + " , " + awayQ2points + " , " + awayQ3points + " , " + awayQ4points + " , " + awayOTpoints +  " , \
                    " + homeQ1points + " , " + homeQ2points + " , " + homeQ3points + " , " + homeQ4points + " , " + homeOTpoints                 
    else:
        bigstring = "\"" + gameid + "\", " + gameweek + ", " + season + ", \"" + gameDate + "\", \"" + gameWeekday + "\" , \"" + awayTeam + "\" , \"" + homeTeam + "\" , " + awayScore + " , " + homeScore + " , \"" + gameLocation + "\" , \"" + gameTime + "\" , \"" + gameCoverage + "\" , " + gameAttendance + " , " + awayWins + " , " + awayLosses + " , " + homeWins + " , " + homeLosses + " , " + away1stDowns + " , " + home1stDowns + " , " + away3rdDownConv + " , " + home3rdDownConv + " , " + away3rdDownAtt + " , " + home3rdDownAtt + " , \
                    " + away4thDownConv + " , " + home4thDownConv + " , " + away4thDownAtt + " , " + home4thDownAtt + " , \
                    " + awayYards + " , " + homeYards + " , " + awayPassingYards + " , " + homePassingYards + " , " + awayPassComp + " , " + homePassComp + " , \
                    " + awayPassAtt + " , " + homePassAtt + " , " + awayRushingYards + " , " + homeRushingYards + " , \
                    " + awayRushingAtt + " , " + homeRushingAtt + " , " + awayPenaltyCount + " , " + homePenaltyCount + " , " + awayPenaltyYards + " , " + homePenaltyYards + " , \
                    " + awayTurnovers + " , " + homeTurnovers + " , " + awayFumblesLost + " , " + homeFumblesLost +  " , \
                    " + awayInterceptionsThrown + " , " + homeInterceptionsThrown + " , " + awayPossessionSeconds + " , " + homePossessionSeconds + " , \
                    " + awayQ1points + " , " + awayQ2points + " , " + awayQ3points + " , " + awayQ4points + " , NULL , \
                    " + homeQ1points + " , " + homeQ2points + " , " + homeQ3points + " , " + homeQ4points + " , NULL"
    return bigstring
