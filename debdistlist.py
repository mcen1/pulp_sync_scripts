#!/bin/env python
import base64
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

def createRepo(id,relurl, feed,repotype,localrepos):
  if id in localrepos:
    return id+" already exists. Skipping"
  mycmd="pulp-admin "+repotype+" repo create --repo-id="+str(id)+" --serve-http=true --relative-url="+relurl+" --feed="+feed
  myresult=subprocess.check_output(mycmd.split(" "))
  mycmd="pulp-admin "+repotype+" repo sync run --bg --repo-id="+str(id)
  myresult=myresult+subprocess.check_output(mycmd.split(" "))
  return myresult

def createDebReleases(id,relurl, feed,repotype,localrepos,releases,arches):
  if id in localrepos:
    return id+" already exists. Skipping"
  mycmd="pulp-admin "+repotype+" repo create --repo-id="+str(id)+" --serve-http=true --relative-url="+relurl+" --feed="+feed
  if len(arches)>2:
    mycmd=mycmd+" --architectures="+arches
  if len(releases)>2:
    mycmd=mycmd+" --releases="+releases
  print mycmd
  myresult=subprocess.check_output(mycmd.replace("  "," ").split(" "))
  mycmd="pulp-admin "+repotype+" repo sync run --bg --repo-id="+str(id)
  myresult=myresult+subprocess.check_output(mycmd.split(" "))
  print mycmd
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
  if "yum" in repo["distributor_type_id"]:
    continue
  elif "deb" in repo["distributor_type_id"]:
    mypulpurl=debrel+myrelurl
    repotype="deb"
    myurl2="https://"+myparent+"/pulp/api/v2/repositories/"+myid+"/?details=true"
    myjunk=json.loads(getPulp(myurl2))
    try:
      print myid
      myreleases=" "
      myarches=" "
      try:
        myarches=myjunk["importers"][0]["config"]["architectures"]
      except:
        pass
      try:
        myreleases=myjunk["importers"][0]["config"]["releases"]
      except:
        pass
      try:
        if len(myarches)<2:
          if "metadesc-arches" in myjunk["description"]:
            myarches=myjunk["description"].split(":metadesc-arches:")[1]
      except:
        pass
      try:
        if len(myreleases)<2:
          if "metadesc-releases" in myjunk["description"]:
            myreleases=myjunk["description"].split(":metadesc-releases:")[1]
      except:
        pass
      print createDebReleases(myid,myrelurl,mypulpurl,repotype,myownrepos,myreleases,myarches)
    except Exception as e:
      print e
      pass
  else:
    continue
