# Scraper for Prediction-Probability-and-Pigskin
Scripts written to scrape football data from ESPN pages, circa Fall 2014
These scripts are no longer functional, as ESPN has updated the structure of pages since last update.

## weeklyUpdate.py
Start by looking at weeklyUpdate.py.  This is the script that I would run weekly to update the database.  Comments in the code should provide a rough approximation of what's going on.  In summary, the basic method was: Go to ESPN.com, find the games that’ve been played in the past week, download (and save) the HTML pages for each game’s box score and play-by-play (which was totally legal; ESPN’s terms of use provided the visitor a license to make one local copy of any visited page on the site), then let loose my scraper on the local copies (so that I wasn’t taxing their server).  I also did this for the week prior, because stats corrections happen occasionally.

## I apologize for everything else being poorly commented.  Sincerely.
getGameStats.py and getPlayerStats.py provided helper functions that did, um, exactly what their filenames suggest.  I do regret that I didn't comment these scripts as well as I commented the weeklyUpdate.py script.
