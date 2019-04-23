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
myparent=relationship["parent"]
mychild=relationship["child"]
creds=file2dict("credentials.dict")


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
  mycmd="pulp-admin "+mytype+" repo sync run --bg --repo-id="+str(id)
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
myurl="https://"+myparent+"/pulp/api/v2/distributors/search/"
myrepos=json.loads(getPulp(myurl))

# get local repos
mylocalurl="https://"+mychild+"/pulp/api/v2/distributors/search/"
mylocalrepos=json.loads(getPulp(mylocalurl))
myownrepos=[]
zerotally=[]
missingtally=[]
mismatched=[]
allgood=True
for repo in myrepos:
  remotecount=0
  localcount=0
  repotype="unknown"
  localurl="unknown"
  remoteurl="unknown"
  remoteurl=str(repo["config"]["relative_url"])
  for item in mylocalrepos:
    if str(item["repo_id"])==str(repo["repo_id"]):
      localurl=item["config"]["relative_url"]
  if localurl!=remoteurl:
    allgood=False
    print "A repo's URL mismatches!"
    print "Repo id: " + str(repo["repo_id"])
    print "Remote URL: " + str(remoteurl)
    print "Local URL: " + str(localurl)
    print "\n\n"
if allgood:
  print "URLs between parent and child match." 
else:
  sys.exit(10)
