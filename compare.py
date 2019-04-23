#!/bin/env python
import base64
import time
import urllib2
import ssl
import json
import subprocess
from loaddictfromfile import *


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

def runSync(id):
  mycmd="pulp-admin rpm repo sync run --bg --repo-id="+str(id)
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
for myrepo in mylocalrepos:
  myownrepos.append(str(myrepo["repo_id"]))
for repo in myrepos:
  myid=repo["repo_id"]
  myrelurl=repo["config"]["relative_url"]
  repotype="unknown"
  if str(repo["last_publish"])!="None":
    #print myid+" is worth syncing "+str(repo["last_publish"])+". Do we have one?"
    if myid in myownrepos:
      mylocalurla="https://"+mychild+"/pulp/api/v2/repositories/"+myid+"/distributors/"
      mylocalrepoinfo=json.loads(getPulp(mylocalurla))
      for thing in mylocalrepoinfo:
        if "deb_distributor" in str(thing) or "yum_distributor" in str(thing):
          try:
            print myid+" my last sync: "+thing["last_publish"]
          except:
            print myid+" has never synced. Fixing this..."
            runSync(myid)
            continue
          print " VS remote last sync:"+repo["last_publish"]
          localdate = time.strptime(thing["last_publish"].split("T")[0], "%Y-%m-%d")
          remotedate= time.strptime(repo["last_publish"].split("T")[0], "%Y-%m-%d")
          if remotedate>localdate:
            print myid+" needs to sync"
            runSync(myid)
