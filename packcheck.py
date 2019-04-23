#!/bin/env python
import base64
import time
import urllib2
import ssl
import json
import subprocess
import sys
from loaddictfromfile import *

runsync=False
try:
  runsync=sys.argv[1]
except:
  pass
  
score=0
relationship=file2dict("relationship.dict")
creds=file2dict("credentials.dict")
myparent=relationship["parent"]
mychild=relationship["child"]
debrel="http://"+myparent+"/pulp/deb/"
rpmrel="http://"+myparent+"/pulp/repos/"
def getPulp(myurl):
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  hostsan=myurl.split("//")[-1].split("/")[0].split('?')[0]
  username=creds[hostsan]["username"]
  password=creds[hostsan]["password"]
  request = urllib2.Request(myurl)
  base64string = base64.b64encode('%s:%s' % (username, password))
  request.add_header("Authorization", "Basic %s" % base64string)
  result = urllib2.urlopen(request, context=ctx)
  return result.read()

def runSync(id,mytype):
  mycmd="pulp-admin "+mytype+" repo sync run --f --bg --repo-id="+str(id)
  myresult=subprocess.check_output(mycmd.split(" "))
  return myresult

def createRepo(id,relurl, feed,repotype,localrepos):
  if id in localrepos:
    return id+" already exists. Skipping"
  mycmd="pulp-admin "+repotype+" repo create --repo-id="+str(id)+" --serve-http=true --relative-url="+relurl+" --feed="+feed
  myresult=subprocess.check_output(mycmd.split(" "))
  mycmd="pulp-admin "+repotype+" repo sync run --bg --repo-id="+str(id)
  myresult=myresult+subprocess.check_output(mycmd.split(" "))
  return myresult

# API queries require HTTPS
# get parent repos
myurl="https://"+myparent+"/pulp/api/v2/repositories/?detail=true"
myrepos=json.loads(getPulp(myurl))

# get local repos
mylocalurl="https://"+mychild+"/pulp/api/v2/repositories/?detail=true"
mylocalrepos=json.loads(getPulp(mylocalurl))
myownrepos=[]
zerotally=[]
missingtally=[]
mismatched=[]
for repo in myrepos:
  remotecount=0
  localcount=0
  repotype="unknown"
  repoid=str(repo["id"])
  content=repo["content_unit_counts"]
  worthit=False
  foundlocal=False
  try:
    for thing in content:
      remotecount=remotecount+content[thing]
  except Exception as e:
    print e
    pass
  try:
    for localrep in mylocalrepos:
      if localrep["id"]==repoid:
        foundlocal=True
        localcontent=lilpeep["content_unit_counts"]
  except Exception as e:
    print e
    print str(repoid)+" is missing locally"
    score=score+1
  try:
    for thing in localcontent:
      try:
        localcount=localcount+content[thing]
      except:
        pass
  except Exception as e:
    print e
    pass
  if localcount!=remotecount:
    worthit=True
    mismatched.append(repoid)
    score=score+1
  if not foundlocal:
     missingtally.append(repoid)
     score=score+1
  if localcount==0 and remotecount!=0:
    worthit=True
    zerotally.append(repoid)
    score=score+1
  if worthit:
    print "Problem repo: "+str(repoid)
    print str(repoid) + " (remote) content total: " + str(remotecount)
    print str(repoid) + " (local) content total: " + str(localcount)
    print "\n"
print "\n\nREPORT" 
print "Tally mismatch (remote count != local count): "+str(mismatched)
print "Local repos having zero tally (local count=0): "+str(zerotally)
print "Missing locals (local equivalent for remote repo not found): "+str(missingtally)
if runsync=="sync":
  print "'sync' was specified as argument 1. Syncing all mismatched repos"
  for repo in mismatched:
    # i got lazy here
    runSync(repo,"rpm")
    runSync(repo,"deb")
sys.exit(score)
