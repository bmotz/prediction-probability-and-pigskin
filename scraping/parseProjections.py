from bs4 import UnicodeDammit
from bs4 import BeautifulSoup
from mechanize import Browser
from collections import Counter
from datetime import datetime
import time
import re
import os
import sys
import MySQLdb as mdb

con2 = mdb.connect('pigskin.psych.indiana.edu','dba','somepig','pigskin')

#thefile = 'C:/Users/bmotz/Documents/SCRAPING/html/projection_2011_17_RB.html'

dstNames = ['49ers D/ST',
            'Bears D/ST',
            'Bengals D/ST',
            'Bills D/ST',
            'Broncos D/ST',
            'Browns D/ST',
            'Buccaneers D/ST',
            'Cardinals D/ST',
            'Chargers D/ST',
            'Chiefs D/ST',
            'Colts D/ST',
            'Cowboys D/ST',
            'Dolphins D/ST',
            'Eagles D/ST',
            'Falcons D/ST',
            'Giants D/ST',
            'Jaguars D/ST',
            'Jets D/ST',
            'Lions D/ST',
            'Packers D/ST',
            'Panthers D/ST',
            'Patriots D/ST',
            'Raiders D/ST',
            'Rams D/ST',
            'Ravens D/ST',
            'Redskins D/ST',
            'Saints D/ST',
            'Seahawks D/ST',
            'Steelers D/ST',
            'Texans D/ST',
            'Titans D/ST',
            'Vikings D/ST']

dstTeams = ['78','56','57','54','60','58','80','51','76','66','64','59','67','74','52','71','65','72','61','62','55','69',
            '73','79','53','82','70','77','75','63','81','68']

def parseProjections(thefile):
    f = open(thefile,"r")
    html = f.readlines()
    f.close()
    soup = BeautifulSoup(str(html))
    table = soup.findAll("table","playerTableTable")[0]
    filename = thefile.split("/")[len(thefile.split("/"))-1]
    position = thefile.split("_")[3][0:thefile.split("_")[len(filename.split("_"))-1].index(".")]
    week = thefile.split("_")[2]
    season = thefile.split("_")[1]
    rows = table.findAll("tr")
    projectionInsert = "INSERT INTO weeklyprojections(gameid,week,season,playerid,fullname,team,position,projectedpoints,positionrank) VALUES "
    for i in range(2,len(rows)):
        cols = rows[i].findAll("td")
        playerid = cols[0].find("a").attrs['playerid']
        fullname = cols[0].find("a").get_text().strip().encode("latin-1")
        messyDetails = cols[0].find("a").nextSibling.strip().encode("latin-1")
        with con2:
            cur2 = con2.cursor()
            if position == 'DST':
                playerid = dstTeams[dstNames.index(fullname)]
                query = "SELECT CAST(team AS CHAR), CAST(fullname AS CHAR) FROM defenseandspecialteams WHERE playerid = " + playerid + " LIMIT 0,1;"
                cur2.execute(query)
                results = cur2.fetchall()
                team = results[0][0]
                fullname = results[0][1]
            else:
                team = messyDetails[2:messyDetails.index('\xa0')].upper()
            query = "SELECT CAST(gameid AS CHAR) FROM games WHERE season = " + \
                    season + " AND week = " + week + " AND (homeTeam = '" + team + "' OR awayTeam = '" + team + "');"
            cur2.execute(query)
            results = cur2.fetchall()
            if len(results) > 0:
                gameid = results[0][0]
            else:
                gameid = '0'
        projectedPoints = cols[11].get_text().strip().encode("latin-1")
        projectedRank = str(i-1)
        if (projectedPoints == "--") | (gameid == '0'):
            projectionInsert = projectionInsert + ""
        else:
            projectionInsert = projectionInsert + "(" + gameid +","+ week +","+ season +","+ \
                               playerid +",'"+ fullname +"','"+ team +"','"+ position +"',"+ \
                               projectedPoints +","+ projectedRank + "),"
    projectionInsert = projectionInsert[:len(projectionInsert)-1]
    return projectionInsert
    
