from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from findPlayer import *
import time
import re
import MySQLdb as mdb
import os

gameid = ""
week = ""
season = ""
homeOffensiveFumbleReturns = 0
awayOffensiveFumbleReturns = 0
teams = ['ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN','DET','GB','HOU','IND','JAX','KC','MIA','MIN','NE','NO','NYG','NYJ','OAK','PHI','PIT','SD','SEA','SF','STL','TB','TEN','WSH']
teamDefensePIDs = [51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82]
createPassing = "CREATE TEMPORARY TABLE passTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3)," + \
                "passAtt INT,passComp INT,passYds INT,passTDs INT,passINT INT);"
createRushing = "CREATE TEMPORARY TABLE rushTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3)," + \
                "rushAtt INT,rushYds INT,rushTDs INT);"
createReceiving = "CREATE TEMPORARY TABLE receivingTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3)," + \
                  "receptions INT,recYds INT,recTDs INT);"
createFumbles = "CREATE TEMPORARY TABLE fumbleTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3)," + \
                "fumblesLost INT);"
createKicking = "CREATE TEMPORARY TABLE kickTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3), position VARCHAR(3), " + \
                "attXP INT,madeXP INT,att00_29 INT,made00_29 INT,att30_39 INT,made30_39 INT,att40_49 INT,made40_49 INT,att50_up INT,made50_up INT);"
createDefense = "CREATE TEMPORARY TABLE defenseTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3),position VARCHAR(3)," + \
                "tackles INT, sacks INT,interceptions INT,fumblesRecovered INT,safeties INT,defensiveTDs INT,returnTDs INT,ptsAllowed INT);"
createFumbleReturn = "CREATE TEMPORARY TABLE fumbleReturnTemp (gameid INT,playerID INT,team VARCHAR(3),opponent VARCHAR(3)," + \
                     "fumblesReturned INT);"
createTwoPointConversions = "CREATE TEMPORARY TABLE twoPtConversionTemp (gameid INT, playerID INT, conversiontype VARCHAR(10), team VARCHAR(3), opponent VARCHAR(3) );"        
createOffense = "CREATE TEMPORARY TABLE offenseTemp (gameid INT,playerID INT,fullname VARCHAR(30),team VARCHAR(3),opponent VARCHAR(3), position VARCHAR(3), " + \
                "passAtt INT,passComp INT,passYds INT,passTDs INT,passINT INT, " + \
                "rushAtt INT,rushYds INT,rushTDs INT, " + \
                "receptions INT,recYds INT,recTDs INT, " + \
                "fumblesLost INT, fumblesReturned INT, twoPointConvs INT);"
dropTempTables = "DROP TEMPORARY TABLE passTemp, rushTemp, receivingTemp, fumbleTemp, kickTemp, defenseTemp, fumbleReturnTemp, twoPtConversionTemp, offenders, offenseTemp;"

def getPassing(soup):
    playerlist = ""
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical")    
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    passingStats = soup.findAll(text=re.compile("C/ATT"))[0].parent.parent.parent.next_sibling
    for row in passingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        passAtt = col[1].get_text().strip().encode("latin-1")[col[1].get_text().strip().encode("latin-1").index("/")+1:]
        passComp = col[1].get_text().strip().encode("latin-1")[:col[1].get_text().strip().encode("latin-1").index("/")]
        passYds = col[2].get_text().strip().encode("latin-1")
        passTDs = col[4].get_text().strip().encode("latin-1")
        passINTs = col[5].get_text().strip().encode("latin-1")
        playerlist = playerlist + "(" + gameid + "," + \
                     playerID + ",'" + awayTeam + "','" + homeTeam + "'," + \
                     passAtt + "," + passComp + "," + passYds + "," + passTDs + "," + passINTs + "),"
    passingStats = soup.findAll(text=re.compile("C/ATT"))[1].parent.parent.parent.next_sibling
    for row in passingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        passAtt = col[1].get_text().strip().encode("latin-1")[col[1].get_text().strip().encode("latin-1").index("/")+1:]
        passComp = col[1].get_text().strip().encode("latin-1")[:col[1].get_text().strip().encode("latin-1").index("/")]
        passYds = col[2].get_text().strip().encode("latin-1")
        passTDs = col[4].get_text().strip().encode("latin-1")
        passINTs = col[5].get_text().strip().encode("latin-1")
        playerlist = playerlist + "(" + gameid + "," + \
                     playerID + ",'" + homeTeam + "','" + awayTeam + "'," + \
                     passAtt + "," + passComp + "," + passYds + "," + passTDs + "," + passINTs + "),"
    playerlist = playerlist[:len(playerlist)-1]
    passingInsert = "INSERT INTO passTemp(gameid,playerID,team,opponent,passAtt,passComp,passYds,passTDs,passINT) " + \
                    "VALUES " + playerlist + ";"
    return passingInsert

def getRushing(soup):
    playerlist = ""
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical") 
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    if soup.findAll(text=re.compile(" Rushing"))[0].lower().encode("latin-1").find("tj rushing") > -1:
        # TJ Rushing's messing things up
        rushingStatsX = soup.findAll(text=re.compile(" Rushing"))
        rushingStatsX = filter (lambda a: a.find('Tj Rushing') == -1, rushingStatsX)
        rushingStatsX = filter (lambda a: a != "T. Rushing".encode("UTF-8"), rushingStatsX) # probably unnecessary
    else:
        rushingStatsX = soup.findAll(text=re.compile(" Rushing"))
    rushingStats = rushingStatsX[0].parent.parent.parent.next_sibling
    for row in rushingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        rushAtt = col[1].get_text().strip().encode("latin-1")
        rushYds = col[2].get_text().strip().encode("latin-1")
        rushTDs = col[4].get_text().strip().encode("latin-1")
        playerlist = playerlist + "(" + gameid + "," + \
                     playerID + ",'" + awayTeam + "','" + homeTeam + "'," + \
                     rushAtt + "," + rushYds + "," + rushTDs + "),"
    rushingStats = rushingStatsX[1].parent.parent.parent.next_sibling
    for row in rushingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        rushAtt = col[1].get_text().strip().encode("latin-1")
        rushYds = col[2].get_text().strip().encode("latin-1")
        rushTDs = col[4].get_text().strip().encode("latin-1")
        playerlist = playerlist + "(" + gameid + "," + \
                     playerID + ",'" + homeTeam + "','" + awayTeam + "'," + \
                     rushAtt + "," + rushYds + "," + rushTDs + "),"
    playerlist = playerlist[:len(playerlist)-1]
    rushingInsert = "INSERT INTO rushTemp(gameid,playerID,team,opponent,rushAtt,rushYds,rushTDs) " + \
                    "VALUES " + playerlist + ";"
    return rushingInsert

def getReceiving(soup):
    playerlist = ""
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical") 
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    receivingStats = soup.findAll(text=re.compile(" Receiving"))[0].parent.parent.parent.next_sibling
    for row in receivingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        receptions = col[1].get_text().strip().encode("latin-1")
        recYds = col[2].get_text().strip().encode("latin-1")
        recTDs = col[4].get_text().strip().encode("latin-1")
        playerlist = playerlist + "(" + gameid + "," + \
                     playerID + ",'" + awayTeam + "','" + homeTeam + "'," + \
                     receptions + "," + recYds + "," + recTDs + "),"
    receivingStats = soup.findAll(text=re.compile(" Receiving"))[1].parent.parent.parent.next_sibling
    for row in receivingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        receptions = col[1].get_text().strip().encode("latin-1")
        recYds = col[2].get_text().strip().encode("latin-1")
        recTDs = col[4].get_text().strip().encode("latin-1")
        playerlist = playerlist + "(" + gameid + "," + \
                     playerID + ",'" + homeTeam + "','" + awayTeam + "'," + \
                     receptions + "," + recYds + "," + recTDs + "),"
    playerlist = playerlist[:len(playerlist)-1]
    receivingInsert = "INSERT INTO receivingTemp(gameid,playerID,team,opponent,receptions,recYds,recTDs) " + \
                      "VALUES " + playerlist + ";"
    return receivingInsert

def getFumbles(soup):
    playerlist = ""
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical") 
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    try:
        fumbleStats = soup.findAll(text=re.compile(" Fumbles"))[0].parent.parent.parent.next_sibling
        for row in fumbleStats.findAll("tr"):
            col = row.findAll("td")
            if col[2].get_text().strip().encode("latin-1") != "0":
                playerURL = col[0].find("a").get("href")
                playerID = re.findall("\d+",playerURL)[0]
                fumblesLost = col[2].get_text().strip().encode("latin-1")
                playerlist = playerlist + "(" + gameid + "," + \
                             playerID + ",'" + awayTeam + "','" + homeTeam + "'," + \
                             fumblesLost + "),"
            else:
                nothing = "0"
        fumbleStats = soup.findAll(text=re.compile(" Fumbles"))[1].parent.parent.parent.next_sibling
        for row in fumbleStats.findAll("tr"):
            col = row.findAll("td")
            if col[2].get_text().strip().encode("latin-1") != "0":
                playerURL = col[0].find("a").get("href")
                playerID = re.findall("\d+",playerURL)[0]
                fumblesLost = col[2].get_text().strip().encode("latin-1")
                playerlist = playerlist + "(" + gameid + "," + \
                             playerID + ",'" + homeTeam + "','" + awayTeam + "'," + \
                             fumblesLost + "),"
            else:
                nothing = "0"
        playerlist = playerlist[:len(playerlist)-1]
        if len(playerlist) == 0:
            fumbleInsert = ""
        else:
            fumbleInsert = "INSERT INTO fumbleTemp(gameid,playerID,team,opponent,fumblesLost) " + \
                           "VALUES " + playerlist + ";"
    except:
        fumbleInsert = ""
    finally:
        return fumbleInsert

def getFumbleReturnTD(soup):
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical") 
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    scoringSummary = soup.findAll(text=re.compile("Scoring Summary"))[0].parent.parent.next_sibling
    stuff = []
    for row in scoringSummary.findAll("tr"):
        col = row.findAll("td")
        if len(col) == 0:
            nothing = "0"
        elif col[1].get_text().strip().encode("latin-1") == 'TD':
            details = col[3].get_text().strip().encode("latin-1")
            if int(details.find("Fumble Return")) > 0:
                if col[0].find("img") is None:
                    logoClass = [s for s in col[0].find("div")["class"] if "nfl-small-" in s]
                    teamIndex = logoClass[0][logoClass[0].rfind("-")+1:]
                    teamaroonies =['000','ATL','BUF','CHI','CIN','CLE','DAL','DEN','DET','GB','TEN','IND','KC','OAK','STL','MIA','MIN','NE','NO','NYG','NYJ','PHI','ARI','PIT','SD','SF','SEA','TB','WSH','CAR','JAC','AFC','NFC','BAL','HOU']
                    teamThatScored = teamaroonies[int(teamIndex)]
                else:
                    teamThatScored = col[0].find("img").get("alt").upper()
                stuff.append(teamThatScored)
                playerThatScored = details[:details.index(re.findall("\d+",details)[0])-1]
                stuff.append(playerThatScored)
    poopers = stuff
    insertStatement = ""
    if len(poopers) == 0:
        insertStatement = ""
    else:
        homeOffensiveFumbleReturns = 0
        awayOffensiveFumbleReturns = 0
        for scoopers in range(1,len(poopers)/2+1):
            if gameid == '271014026':
                insertStatement = "" # Pierre Thomas got one, but while he was playing on special teams
            elif gameid == '271202015':
                insertStatement = "" # ESPN called Michael Lehan "Mike" in the boxscore.  He's defense anyway.
            else:
                playeridinfo = getPlayerID(poopers[(2*scoopers)-1], gameid, poopers[(2*scoopers)-2]) # getPlayerID(playername,gameid,team)
                playerid = playeridinfo[0]
                # FIRST NEED TO ENSURE THAT ITS OFFENSIVE
                con2 = mdb.connect('pigskin.psych.indiana.edu','dba',
                                  'somepig','pigskin')
                with con2:
                    cur2 = con2.cursor()
                    thisSql = "SELECT CAST(a.playerid AS CHAR), b.category FROM players a LEFT JOIN positions b ON a.position = b.position WHERE a.playerid = " + playerid + ";"
                    cur2.execute(thisSql)
                    stinkypoo = cur2.fetchall()                  
                    if stinkypoo[0][1] == 'offense':
                        if poopers[scoopers] == homeTeam:
                            team = homeTeam
                            opponent = awayTeam
                            homeOffensiveFumbleReturns = homeOffensiveFumbleReturns + 1
                        else:
                            team = awayTeam
                            opponent = homeTeam
                            awayOffensiveFumbleReturns = homeOffensiveFumbleReturns + 1
                        insertStatement = "INSERT INTO fumbleReturnTemp(gameid,playerID,team,opponent,fumblesReturned) VALUES (" + \
                                          gameid + "," + playerid + ",'" + team + "','" + opponent + "',1); " + insertStatement
                    else:
                        insertStatement = "" + insertStatement
    return insertStatement

def getTwoPointConversions(soup):
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    scoringSummary = soup.findAll(text=re.compile("Scoring Summary"))[0].parent.parent.next_sibling
    stuff = []
    allconversions = []
    for row in scoringSummary.findAll("tr"):
        col = row.findAll("td")
        if len(col) == 0:
            nothing = "0"
        elif col[1].get_text().strip().encode("latin-1") == 'TD':
            details = col[3].get_text().strip().encode("latin-1")
            if int(details.find("Two-Point Conversion")) > 0:
                if col[0].find("img") is None:
                    logoClass = [s for s in col[0].find("div")["class"] if "nfl-small-" in s]
                    teamIndex = logoClass[0][logoClass[0].rfind("-")+1:]
                    teamaroonies =['000','ATL','BUF','CHI','CIN','CLE','DAL','DEN','DET','GB','TEN','IND','KC','OAK','STL','MIA','MIN','NE','NO','NYG','NYJ','PHI','ARI','PIT','SD','SF','SEA','TB','WSH','CAR','JAC','AFC','NFC','BAL','HOU']
                    teamThatScored = teamaroonies[int(teamIndex)]
                else:
                    teamThatScored = col[0].find("img").get("alt").upper()
                if teamThatScored == 'NWE':
                    teamThatScored = 'NE'
                elif teamThatScored == 'NOR':
                    teamThatScored = 'NO'
                elif teamThatScored == 'NWE':
                    teamThatScored = 'NE'
                elif teamThatScored == 'TAM':
                    teamThatScored = 'TB'
                elif teamThatScored == 'KAN':
                    teamThatScored = 'KC'
                elif teamThatScored == 'GNB':
                    teamThatScored = 'GB'
                elif teamThatScored == 'SDG':
                    teamThatScored = 'SD'
                elif teamThatScored == 'SFO':
                    teamThatScored = 'SF'
                stuff.append(teamThatScored)
                playersThatScored = details[details.find("(")+1:details.find(")")]
                stuff.append(playersThatScored)
    conversiondetails = stuff
    if len(conversiondetails) == 0:
        conversionInsertSql = ""
    else:
        for conversionnum in range(1,len(conversiondetails)/2+1):
            if conversiondetails[(conversionnum * 2) - 1] == 'Two-Point Conversion Failed':
                nothing = '0'
            elif 'run for' in conversiondetails[(conversionnum * 2) - 1].lower():
                conversiontype = 'RUN'
                team = conversiondetails[(conversionnum * 2) - 2]
                if team == homeTeam:
                    opponent = awayTeam
                else:
                    opponent = homeTeam
                tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
                if len(tagwithgameid) == 0:
                    tagwithgameid = soup.find_all(rel="canonical") 
                gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
                playername = conversiondetails[(conversionnum * 2) - 1][:conversiondetails[(conversionnum * 2) - 1].lower().find(' run for')]
                conversionplayer = getPlayerID(playername, gameid, conversiondetails[(conversionnum * 2) - 2])
                if conversionplayer[2] == 'K':
                    nothing = '0'
                else:
                    allconversions.append([gameid, conversionplayer[0], conversiontype, team, opponent])
            elif 'pass to' in conversiondetails[(conversionnum * 2) - 1].lower():
                conversiontype = 'PASS'
                team = conversiondetails[(conversionnum * 2) - 2]
                if team == homeTeam:
                    opponent = awayTeam
                else:
                    opponent = homeTeam
                tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
                if len(tagwithgameid) == 0:
                    tagwithgameid = soup.find_all(rel="canonical") 
                gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
                playername = conversiondetails[(conversionnum * 2) - 1][:conversiondetails[(conversionnum * 2) - 1].lower().find(' pass to')]
                conversionplayer = getPlayerID(playername, gameid, conversiondetails[(conversionnum * 2) - 2])
                if conversionplayer[2] == 'K':
                    nothing = '0'
                else:
                    allconversions.append([gameid, conversionplayer[0], conversiontype, team, opponent])
                conversiontype = 'REC'
                team = conversiondetails[(conversionnum * 2) - 2]
                start = conversiondetails[(conversionnum * 2) - 1].lower().find(' pass to ') + 9
                end = conversiondetails[(conversionnum * 2) - 1].lower().find(' for two-point')
                playername = conversiondetails[(conversionnum * 2) - 1][start:end]
                if (playername == 'Stevie Johnson') & (gameid == '330922020'):
                    conversionplayer = '11458'
                else:
                    conversionplayer = getPlayerID(playername, gameid, conversiondetails[(conversionnum * 2) - 2])
                if conversionplayer[2] == 'K':
                    nothing = '0'
                else:
                    allconversions.append([gameid, conversionplayer[0], conversiontype, team, opponent])
        conversionlist = ""
        for i in range(0,len(allconversions)):
            conversionlist = conversionlist + "(" + allconversions[i][0] + "," + allconversions[i][1] + ",'" + allconversions[i][2] + "','" + \
                             allconversions[i][3] + "','" + allconversions[i][4] + "'),"
        conversionlist = conversionlist[:len(conversionlist)-1]
        if conversionlist == "":
            conversionInsertSql = ""
        else:
            conversionInsertSql = "INSERT INTO twoPtConversionTemp(gameid,playerid,conversiontype,team,opponent) " + \
                                  "VALUES " + conversionlist + ";"
    return conversionInsertSql
        

def getKicking(soup):
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical") 
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    playerlist = ""
    # AWAY KICKERS
    kickingStats = soup.findAll(text=re.compile(" Kicking"))[0].parent.parent.parent.next_sibling
    for row in kickingStats.findAll("tr"):
        col = row.findAll("td")
        playerURL = col[0].find("a").get("href")
        playerID = re.findall("\d+",playerURL)[0]
        kickerName = col[0].getText().strip().encode("latin-1").replace(" ","")
        if col[4].getText().strip().encode("latin-1").find("/") > 0:
            madeXP = col[4].getText().strip().encode("latin-1")[:col[4].getText().strip().encode("latin-1").find("/")]
            attXP = col[4].getText().strip().encode("latin-1")[col[4].getText().strip().encode("latin-1").find("/")+1:]
            fgAtt = col[1].getText().strip().encode("latin-1")[col[1].getText().strip().encode("latin-1").find("/")+1:]
        else:
            madeXP = col[3].getText().strip().encode("latin-1")[:col[3].getText().strip().encode("latin-1").find("/")]
            attXP = col[3].getText().strip().encode("latin-1")[col[3].getText().strip().encode("latin-1").find("/")+1:]
            fgAtt = col[1].getText().strip().encode("latin-1")[col[1].getText().strip().encode("latin-1").find("/")+1:]
        thisplayer = [gameid,week,season,playerID,awayTeam,homeTeam,attXP,madeXP,0,0,0,0,0,0,0,0]
        if fgAtt != 0:
            htmldir = os.getcwd() + "\\html\\"
            thefile = "playbyplay_" + gameid + ".html"
            pbpFilename = os.path.join(os.path.dirname(htmldir), thefile)
            k = open(pbpFilename,"r")
            ktml = k.readlines()
            k.close()
            koup = BeautifulSoup(str(ktml))
            kactions = koup.findAll(text=re.compile(kickerName))
            for action in kactions:
                if (action.lower().find("field goal") > 0 and (action.lower().find("fake field goal") == -1 and action.lower().find(" pooch punt") == -1 and action.lower().find("delay of game") == -1 and action.lower().find(" fumbles ") == -1)):
                    detail = action.strip().encode("latin-1")
                    outer = detail.find(" yard field goal")
                    inner = detail[:detail.find(" yard field goal")].rfind(" ")+1
                    distance = int(detail[inner:outer])
                    if detail[outer:].lower().find("no good") > 0 or detail[outer:].lower().find("blocked") > 0:
                        if (distance < 30):
                            thisplayer[8] = thisplayer[8]+1
                        elif (distance < 40):
                            thisplayer[10] = thisplayer[10]+1
                        elif (distance < 50):
                            thisplayer[12] = thisplayer[12]+1
                        else:
                            thisplayer[14] = thisplayer[14]+1
                    else:
                        if (distance < 30):
                            thisplayer[8] = thisplayer[8]+1
                            thisplayer[9] = thisplayer[9]+1
                        elif (distance < 40):
                            thisplayer[10] = thisplayer[10]+1
                            thisplayer[11] = thisplayer[11]+1
                        elif (distance < 50):
                            thisplayer[12] = thisplayer[12]+1
                            thisplayer[13] = thisplayer[13]+1
                        else:
                            thisplayer[14] = thisplayer[14]+1
                            thisplayer[15] = thisplayer[15]+1
        playerlist = playerlist + " (" + gameid + "," + \
                     playerID + ",'" + awayTeam + "','" + homeTeam + "','PK'," + \
                     str(thisplayer[6]) + "," + str(thisplayer[7]) + "," + \
                     str(thisplayer[8]) + "," + str(thisplayer[9]) + "," + \
                     str(thisplayer[10]) + "," + str(thisplayer[11]) + "," + \
                     str(thisplayer[12]) + "," + str(thisplayer[13]) + "," + \
                     str(thisplayer[14]) + "," + str(thisplayer[15]) + "),"
    # HOME KICKERS
    kickingStats = soup.findAll(text=re.compile(" Kicking"))[1].parent.parent.parent.next_sibling
    if (kickingStats is None):
        kickingInsert = ";"
    else:
        for row in kickingStats.findAll("tr"):
            col = row.findAll("td")
            playerURL = col[0].find("a").get("href")
            playerID = re.findall("\d+",playerURL)[0]
            kickerName = col[0].getText().strip().encode("latin-1").replace(" ","")
            if col[4].getText().strip().encode("latin-1").find("/") > 0:
                madeXP = col[4].getText().strip().encode("latin-1")[:col[4].getText().strip().encode("latin-1").find("/")]
                attXP = col[4].getText().strip().encode("latin-1")[col[4].getText().strip().encode("latin-1").find("/")+1:]
                fgAtt = col[1].getText().strip().encode("latin-1")[col[1].getText().strip().encode("latin-1").find("/")+1:]
            else:
                madeXP = col[3].getText().strip().encode("latin-1")[:col[3].getText().strip().encode("latin-1").find("/")]
                attXP = col[3].getText().strip().encode("latin-1")[col[3].getText().strip().encode("latin-1").find("/")+1:]
                fgAtt = col[1].getText().strip().encode("latin-1")[col[1].getText().strip().encode("latin-1").find("/")+1:]
            thisplayer = [gameid,week,season,playerID,awayTeam,homeTeam,attXP,madeXP,0,0,0,0,0,0,0,0]
            if fgAtt != 0:
                htmldir = os.getcwd() + "\\html\\"
                thefile = "playbyplay_" + gameid + ".html"
                pbpFilename = os.path.join(os.path.dirname(htmldir), thefile)
                k = open(pbpFilename,"r")
                ktml = k.readlines()
                k.close()
                koup = BeautifulSoup(str(ktml))
                kactions = koup.findAll(text=re.compile(kickerName))
                for action in kactions:
                    if (action.lower().find("field goal") > 0 and (action.lower().find("fake field goal") == -1 and action.lower().find(" pooch punt") == -1 and action.lower().find("Delay of Game") == -1 and action.lower().find(" fumbles ") == -1)):
                        detail = action.strip().encode("latin-1")
                        outer = detail.find(" yard field goal")
                        inner = detail[:detail.find(" yard field goal")].rfind(" ")+1
                        distance = int(detail[inner:outer])
                        if detail[outer:].lower().find("no good") > 0 or detail[outer:].lower().find("blocked") > 0:
                            if (distance < 30):
                                thisplayer[8] = thisplayer[8]+1
                            elif (distance < 40):
                                thisplayer[10] = thisplayer[10]+1
                            elif (distance < 50):
                                thisplayer[12] = thisplayer[12]+1
                            else:
                                thisplayer[14] = thisplayer[14]+1
                        else:
                            if (distance < 30):
                                thisplayer[8] = thisplayer[8]+1
                                thisplayer[9] = thisplayer[9]+1
                            elif (distance < 40):
                                thisplayer[10] = thisplayer[10]+1
                                thisplayer[11] = thisplayer[11]+1
                            elif (distance < 50):
                                thisplayer[12] = thisplayer[12]+1
                                thisplayer[13] = thisplayer[13]+1
                            else:
                                thisplayer[14] = thisplayer[14]+1
                                thisplayer[15] = thisplayer[15]+1
            playerlist = playerlist + " (" + gameid + "," + \
                         playerID + ",'" + homeTeam + "','" + awayTeam + "','PK'," + \
                         str(thisplayer[6]) + "," + str(thisplayer[7]) + "," + \
                         str(thisplayer[8]) + "," + str(thisplayer[9]) + "," + \
                         str(thisplayer[10]) + "," + str(thisplayer[11]) + "," + \
                         str(thisplayer[12]) + "," + str(thisplayer[13]) + "," + \
                         str(thisplayer[14]) + "," + str(thisplayer[15]) + "),"
        playerlist = playerlist[:len(playerlist)-1]
        kickingInsert = "INSERT INTO kickTemp(gameid,playerID,team,opponent,position,attXP,madeXP,att00_29,made00_29,att30_39,made30_39,att40_49,made40_49,att50_up,made50_up) VALUES" + \
                        playerlist + ";"
    return kickingInsert

def getDefense(soup):
    teaminfo = soup.findAll("div","team-info")
    awayTeam = teaminfo[0].find("a").get("href")[35:teaminfo[0].find("a").get("href")[35:].index("/")+35].upper()
    homeTeam = teaminfo[1].find("a").get("href")[35:teaminfo[1].find("a").get("href")[35:].index("/")+35].upper()
    tagwithgameid = soup.findAll(href=re.compile('^boxscore'))
    if len(tagwithgameid) == 0:
        tagwithgameid = soup.find_all(rel="canonical") 
    gameid = tagwithgameid[0].get("href")[tagwithgameid[0].get("href").index("=")+1:]
    gameStatTable = soup.findAll(text="Team Stat Comparison")[0].parent.parent.next_sibling.findAll("table")[0]
    for row in gameStatTable.findAll('tr')[1:]:
        col = row.findAll('td')
        if col[0].get_text().strip().encode("latin-1") == 'Fumbles lost':
            homeFumblesRec = col[1].get_text().strip().encode("latin-1")
            awayFumblesRec = col[2].get_text().strip().encode("latin-1")
        elif col[0].get_text().strip().encode("latin-1") == 'Interceptions thrown':
            homeInterceptions = col[1].get_text().strip().encode("latin-1")
            awayInterceptions = col[2].get_text().strip().encode("latin-1")
        else:
            nothing = "0"
    # next: find safeties and return touchdowns
    # 261211014: Devin Hester 94 Yd Kickoff Return (Robbie Gould Kick) 
    # 261008018: Reggie Bush 65 Yd Punt Return (John Carney Kick)
    # 261112019: Devin Hester 108 Yd Return Of Attempted Field Goal (Robbie Gould Kick)
    # 271104016: Antonio Cromartie 109 Yd Return Of Attempted Field Goal (Nate Kaeding Kick)
    scoringSummary = soup.findAll(text=re.compile("Scoring Summary"))[0].parent.parent.next_sibling
    homesafeties = 0
    awaysafeties = 0
    homereturns = 0
    awayreturns = 0
    for row in scoringSummary.findAll("tr"):
        col = row.findAll("td")
        if len(col) == 0:
            nothing = "0"
        elif col[1].get_text().strip().encode("latin-1") == 'SF':
            if col[0].find("img") is None:
                logoClass = [s for s in col[0].find("div")["class"] if "nfl-small-" in s]
                teamIndex = logoClass[0][logoClass[0].rfind("-")+1:]
                teamaroonies =['000','ATL','BUF','CHI','CIN','CLE','DAL','DEN','DET','GB','TEN','IND','KC','OAK','STL','MIA','MIN','NE','NO','NYG','NYJ','PHI','ARI','PIT','SD','SF','SEA','TB','WSH','CAR','JAX','AFC','NFC','BAL','HOU']
                teamThatScoredTheSafety = teamaroonies[int(teamIndex)]
            else:
                teamThatScoredTheSafety = col[0].find("img").get("alt").upper()
            if teamThatScoredTheSafety == homeTeam:
                homesafeties = homesafeties + 1
            else:
                awaysafeties = awaysafeties + 1
        elif col[1].get_text().strip().encode("latin-1") == 'TD':
            details = col[3].get_text().strip().encode("latin-1").lower()
            if int(details.find("kickoff return")) > 0 or int(details.find("punt return")) > 0 or int(details.find("return of attempted field goal")) > 0:
                if col[0].find("img") is None:
                    logoClass = [s for s in col[0].find("div")["class"] if "nfl-small-" in s]
                    teamIndex = logoClass[0][logoClass[0].rfind("-")+1:]
                    teamaroonies =['000','ATL','BUF','CHI','CIN','CLE','DAL','DEN','DET','GB','TEN','IND','KC','OAK','STL','MIA','MIN','NE','NO','NYG','NYJ','PHI','ARI','PIT','SD','SF','SEA','TB','WSH','CAR','JAX','AFC','NFC','BAL','HOU']
                    defenseThatScored = teamaroonies[int(teamIndex)]
                else:
                    defenseThatScored = col[0].find("img").get("alt").upper()
                if defenseThatScored == homeTeam:
                    homereturns = homereturns + 1
                else:
                    awayreturns = awayreturns + 1
        else:
            nothing = "0"
    homeSafetyCnt = str(homesafeties)
    awaySafetyCnt = str(awaysafeties)
    homeReturnCnt = str(homereturns)
    awayReturnCnt = str(awayreturns)
    # next: find sacks and tds
    if len(soup.findAll(text=re.compile(" Tackles"))) > 0:
        sackStats = soup.findAll(text=re.compile(" Tackles"))[0].parent.parent.parent.next_sibling.next_sibling
        awayTackles = sackStats.findAll("tr")[0].findAll("th")[1].get_text().strip().encode("latin-1")
        awaySacks = sackStats.findAll("tr")[0].findAll("th")[2].get_text().strip().encode("latin-1")
        sackStats = soup.findAll(text=re.compile(" Tackles"))[1].parent.parent.parent.next_sibling.next_sibling
        homeTackles = sackStats.findAll("tr")[0].findAll("th")[1].get_text().strip().encode("latin-1")
        homeSacks = sackStats.findAll("tr")[0].findAll("th")[2].get_text().strip().encode("latin-1")
        awayDefTDnum = 0
        homeDefTDnum = 0
        for row in scoringSummary.findAll("tr"):
            col = row.findAll("td")
            if len(col) == 0:
                nothing = "0"
            elif col[1].get_text().strip().encode("latin-1") == 'TD':
                details = col[3].get_text().strip().encode("latin-1").lower()
                if int(details.find("fumble return")) > 0 or int(details.find("interception")) > 0:
                    if col[0].find("img") is None:
                        logoClass = [s for s in col[0].find("div")["class"] if "nfl-small-" in s]
                        teamIndex = logoClass[0][logoClass[0].rfind("-")+1:]
                        teamaroonies =['000','ATL','BUF','CHI','CIN','CLE','DAL','DEN','DET','GB','TEN','IND','KC','OAK','STL','MIA','MIN','NE','NO','NYG','NYJ','PHI','ARI','PIT','SD','SF','SEA','TB','WSH','CAR','JAX','AFC','NFC','BAL','HOU']
                        defenseThatScored = teamaroonies[int(teamIndex)]
                    else:
                        defenseThatScored = col[0].find("img").get("src")[47:col[0].find("img").get("src").index(".gif")].upper()
                    if defenseThatScored == homeTeam:
                        homeDefTDnum = homeDefTDnum + 1
                    else:
                        awayDefTDnum = awayDefTDnum + 1
                else:
                    nothing = "0"
            else:
                nothing = "0"
        awayDefTD = str(awayDefTDnum - awayOffensiveFumbleReturns)
        homeDefTD = str(homeDefTDnum - homeOffensiveFumbleReturns)
    elif gameid == '260910027':
        homeDefTD = '0'
        awayDefTD = '1'
        homeSacks = '1'
        awaySacks = '3'
        homeTackles = '48'
        awayTackles = '34'
    else:
        sackStats = soup.findAll(text=re.compile(" Defensive"))[0].parent.parent.parent.next_sibling.next_sibling
        awayTackles = sackStats.findAll("tr")[0].findAll("th")[1].get_text().strip().encode("latin-1")
        awaySacks = sackStats.findAll("tr")[0].findAll("th")[3].get_text().strip().encode("latin-1")
        awayDefTD = str(int(sackStats.findAll("tr")[0].findAll("th")[7].get_text().strip().encode("latin-1")) - awayOffensiveFumbleReturns)
        sackStats = soup.findAll(text=re.compile(" Defensive"))[1].parent.parent.parent.next_sibling.next_sibling
        homeTackles = sackStats.findAll("tr")[0].findAll("th")[1].get_text().strip().encode("latin-1")
        homeSacks = sackStats.findAll("tr")[0].findAll("th")[3].get_text().strip().encode("latin-1")
        homeDefTD = str(int(sackStats.findAll("tr")[0].findAll("th")[7].get_text().strip().encode("latin-1")) - homeOffensiveFumbleReturns)
    homePtsAllowed = str(int(teaminfo[0].findAll("span")[0].get_text().strip().encode("latin-1")) - (int(awayDefTD) * 6)) # defensive TDs don't count as
    awayPtsAllowed = str(int(teaminfo[1].findAll("span")[0].get_text().strip().encode("latin-1")) - (int(homeDefTD) * 6)) # points allowed by opposing defense
    homeInsert = "(" + gameid + "," + str(teamDefensePIDs[teams.index(homeTeam)]) + ",'" + homeTeam + "','" + awayTeam + "','DST'," + \
                 homeTackles + "," + homeSacks + "," + homeInterceptions + "," + homeFumblesRec + "," + homeSafetyCnt + "," + homeDefTD + "," + homeReturnCnt + "," + homePtsAllowed + ")"
    awayInsert = "(" + gameid + "," + str(teamDefensePIDs[teams.index(awayTeam)]) + ",'" + awayTeam + "','" + homeTeam + "','DST'," + \
                 awayTackles + "," + awaySacks + "," + awayInterceptions + "," + awayFumblesRec + "," + awaySafetyCnt + "," + awayDefTD + "," + awayReturnCnt + "," + awayPtsAllowed + ")"
    defenseInsert = "INSERT INTO defenseTemp(gameid,playerID,team,opponent,position,tackles,sacks,interceptions,fumblesRecovered,safeties,defensiveTDs,returnTDs,ptsAllowed) " + \
                    "VALUES " + homeInsert + "," + awayInsert + ";"
    return defenseInsert


offensePoints = "UPDATE offense SET fantasyPoints = ((passYds / 25) + " + \
                                                        "(passTDs * 4) + " + \
                                                        "(passINT * -2) + " + \
                                                        "(rushYds / 10) + " + \
                                                        "(rushTDs * 6) + " + \
                                                        "(recYds / 10) + " + \
                                                        "(recTDs * 6) + " + \
                                                        "(fumblesReturned * 6) + " + \
                                                        "(fumblesLost * -2) + " + \
                                                        "(twoPointConvs * 2));"
kickingPoints = "UPDATE kicking SET fantasyPoints = ((madeXP) + " + \
                                                        "(made00_29 * 3) + " + \
                                                        "(made30_39 * 3) + " + \
                                                        "(made40_49 * 3) + " + \
                                                        "(made50_up * 5));"
defensePoints1 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) + " + \
                                                        "10) " + \
                "WHERE ptsAllowed = 0; " 
defensePoints2 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) + " + \
                                                        "7) " + \
                "WHERE ptsAllowed BETWEEN 1 AND 6; " 
defensePoints3 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) + " + \
                                                        "4) " + \
                "WHERE ptsAllowed BETWEEN 7 AND 13; " 
defensePoints4 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) + " + \
                                                        "1) " + \
                "WHERE ptsAllowed BETWEEN 14 AND 20; " 
defensePoints5 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) + " + \
                                                        "0) " + \
                "WHERE ptsAllowed BETWEEN 21 AND 27; " 
defensePoints6 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) - " + \
                                                        "1) " + \
                "WHERE ptsAllowed BETWEEN 28 AND 34; " 
defensePoints7 = "UPDATE defenseAndSpecialTeams SET fantasyPoints = ((sacks) + " + \
                                                        "(interceptions * 2) + " + \
                                                        "(fumblesRecovered * 2) + " + \
                                                        "(safeties * 2) + " + \
                                                        "(defensiveTDs * 6) + " + \
                                                        "(returnTDs * 6) - " + \
                                                        "4) " + \
                "WHERE ptsAllowed >= 35;"
