from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
import re
import MySQLdb as mdb

def getPlayerID(playername, gameid, team):
    con = mdb.connect('pigskin.psych.indiana.edu','dba',
                      'somepig','pigskin')
    with con:
        cur = con.cursor()
        cur.execute("SELECT CAST(playerid AS CHAR), fullname, position " + \
                    "FROM players " + \
                    "WHERE fullname LIKE '%" + playername + "%';")
        easyresults = cur.fetchall()
        if len(easyresults) == 1:
            return [easyresults[0][0],easyresults[0][1],easyresults[0][2]]
        else:
            # there's no 100% clear way to assign the TD from a name only. first dry your tears.
            # let's start by seeing if there's just one player with that name who played in the game
            playerIDs = "1" # not present
            if type(gameid) is int:
                gameid = str(gameid)
            else:
                gameid = gameid
            gameFilename = "C:\\Users\\bmotz\\Documents\\SCRAPING\\html\\boxscore_" + gameid + ".html"
            f = open(gameFilename,"r")
            html = f.readlines()
            f.close()
            soup = BeautifulSoup(str(html))
            allPlayerLinks = soup.find_all(href=re.compile("http://espn.go.com/nfl/player/_/id/.*"))
            for i in allPlayerLinks:
                playerURL = i.get("href")
                playerID = re.findall("\d+",playerURL)[0]
                playerIDs = playerIDs + ", " + playerID
            cur.execute("SELECT CAST(playerid AS CHAR), fullname, position " + \
                        "FROM players " + \
                        "WHERE fullname LIKE '%" + playername + "%'" + \
                        "AND playerid IN (" + playerIDs + ");")
            hardresults = cur.fetchall()
            if playername == 'Joshua Morgan' and gameid == '321203028':
                return ['11408','Josh Morgan','WR']
            elif len(hardresults) > 1 or len(hardresults) == 0:
                print "ERROR FINDING " + playername + "'s PLAYERID. CANNOT PROCEED. SORRY."
            else:
                return [hardresults[0][0],hardresults[0][1],hardresults[0][2]]
            
