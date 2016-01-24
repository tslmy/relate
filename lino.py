# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests, json, os, itertools
from multiprocessing.dummy import Pool as ThreadPool
#import language_check, pprint
userInputCache = {}
def wikiRequestWrapper(params):
	return requests.get('https://www.wikidata.org/w/api.php',params=params).json()
def wikidataSearch(userInput):
	'''这个函数完成的是这个功能：https://www.wikidata.org/w/api.php?action=wbsearchentities&language=zh-cn&search=%E9%9C%8D%E9%87%91&strictlanguage=1&limit=1'''
	if userInputCache.has_key(userInput):
		return userInputCache[userInput]
	else:
		result = wikiRequestWrapper({
			'action':'wbsearchentities',
			'search':userInput,
			'language':'zh-cn',
			'strictlanguage':1,
			'format':'json',
			'limit':1})
		try:
			result = result['search'][0]['title']
		except:
			result = ''
		userInputCache[userInput] = result
		return result
wikiLinkCache = {}
def getWikiLink(itemId):
	if wikiLinkCache.has_key(itemId):
		return wikiLinkCache[itemId]
	else:
		result = wikiRequestWrapper({
			'action':'wbgetentities',
			'ids':itemId,
			'props':'sitelinks',
			'format':'json'})
		if result['success']!=1:
			print 'WARNING: No match found.'
			return ''
		else:
			try:
				wikiLink = result['entities'][itemId]['sitelinks']['enwiki']['title']
			except KeyError:
				wikiLink = ''
			wikiLinkCache[itemId] = wikiLink
		return wikiLink
claimsCache = {}
def wikidataGetClaims(entityId):
	#print 'Retriving claims for',entityId
	if claimsCache.has_key(entityId):
		return claimsCache[entityId]
	else:
		claims = {}
		for propertyId,v in wikiRequestWrapper({
			'action':'wbgetclaims',
			'entity':entityId,
			'format':'json'
		})['claims'].items():
			itemIds = []
			for va in v:
				mainSnak = va['mainsnak']
				if mainSnak['datatype']=='wikibase-item':
					try:
						itemId = 'Q'+str(mainSnak['datavalue']['value']['numeric-id'])
					except KeyError:
						#print '[WARNING]No datavalue presented in',mainSnak
						continue
					else:
						itemIds.append(itemId)
			if itemIds!=[]:
				claims[propertyId]=itemIds
		claimsCache[entityId] = claims
		return claims

def wikidataGetEntityProp(entityId,prop='labels'):
	'''这个函数执行了这个功能：https://www.wikidata.org/w/api.php?action=wbgetentities&props=descriptions&ids=Q8747189327498172034312941&languages=zh-cn'''
	result = wikiRequestWrapper({
			'action':'wbgetentities',
			'props':prop,
			'ids':entityId,
			'languages':'zh-cn',
			'format':'json'
		})
	try:
		return result['entities'][entityId][prop]['zh-cn']['value']
	except:
		return

def naturallyDescribeWithClaims(claimsInList):
	result = ''
	pool = ThreadPool(200) # Sets the pool size
	results = pool.map(wikidataGetEntityLabel, itertools.chain(*claimsInList))
	pool.close()	#close the pool 
	pool.join()		#wait for the work to finish
	for propertyId,itemId in claimsInList:
		result = result + wikidataGetEntityLabel(propertyId)+' '+wikidataGetEntityLabel(itemId)+'. '
	return result
def convertClaimsFromIdsToLabels(claimsInList):
	result = []
	pool = ThreadPool(200) # Sets the pool size
	results = pool.map(wikidataGetEntityLabel, itertools.chain(*claimsInList))
	pool.close()	#close the pool 
	pool.join()		#wait for the work to finish
	for propertyId,itemId in claimsInList:
		result += [(wikidataGetEntityLabel(propertyId),
					wikidataGetEntityLabel(itemId))]
	return result
def expandClaimsForLooping(claimsInDict):
	claimsInList = []
	for propertyId,itemIds in claimsInDict.items():
		for itemId in itemIds:
			claimsInList.append((propertyId,itemId))
	return claimsInList
try:
	f = open('dump.txt','r')
	knownShortestPathsToTarget = json.loads(f.read())
	f.close()
except:
	print '[ERROR]Cannot read dump file; using Q336 ("science") by default.'
	knownShortestPathsToTarget = {'Q336':[('START','Q336')]}#actually this should be "END" but ...
def explore(testItemId):
	global shortestPaths, nodesOnNextLevel, nodesOnThisLevel, ifFoundAnswer, bestAnswer
	testItemClaims = expandClaimsForLooping(wikidataGetClaims(testItemId))
	#print testItemClaims
	for propertyId,itemId in testItemClaims:
		nodesOnNextLevel.update([itemId])
		newPath = shortestPaths[testItemId]+[(propertyId,itemId)]
		if itemId in knownShortestPathsToTarget.keys():
			print 'SUCCESS!'
			ifFoundAnswer = True
			knownShortestPathToTarget = knownShortestPathsToTarget[itemId]
			#knownShortestPathToTarget.reverse()
			newAnswer = newPath+knownShortestPathToTarget
			if len(bestAnswer)>len(newAnswer) or len(bestAnswer)==0:
				print 'Updating best answer from', bestAnswer, 'to', newAnswer,'.'
				bestAnswer = newAnswer
			return
			#this may NOT be the shortest, since not all nodes in this depth are checked.
		else: #sadly, we have to go on:
			if shortestPaths.has_key(itemId):
				lengthOfOldPath = len(shortestPaths[itemId])
			else:
				lengthOfOldPath = 99999
			lengthOfNewPath = len(newPath)
			#print 'lengthOfNewPath:',lengthOfNewPath
			if lengthOfOldPath>lengthOfNewPath:
				#then we gotta update it
				shortestPaths[itemId] = newPath
def findPath(ItemAId='Q7802'):#,ItemBId='Q336'):
	global shortestPaths, nodesOnNextLevel, nodesOnThisLevel, ifFoundAnswer, bestAnswer
	shortestPaths = {ItemAId:[('START',ItemAId)]}
	nodesOnThisLevel = set()
	nodesOnNextLevel = set()
	nodesOnNextLevel.update([ItemAId])
	bestAnswer = []
	ifFoundAnswer = False
	levelLimit = 10
	if knownShortestPathsToTarget.has_key(ItemAId):
		print 'Already in cache:',knownShortestPathsToTarget[ItemAId]
		bestAnswer = knownShortestPathsToTarget[ItemAId]
		return knownShortestPathsToTarget[ItemAId]
	else:
		while levelLimit>0 and len(nodesOnNextLevel)>0 and not ifFoundAnswer:
			levelLimit -= 1
			print '[DEBUG]Currently on level',levelLimit,'...'
			nodesOnThisLevel = nodesOnNextLevel
			nodesOnNextLevel = set()
			pool = ThreadPool(200) # Sets the pool size
			results = pool.map(explore, nodesOnThisLevel)
			pool.close()	#close the pool 
			pool.join()		#wait for the work to finish
			#print 'shortestPaths:',shortestPaths
		return [] #timed out :(
def DEBUGdumpTheBSide():
	global knownShortestPathsToTarget
	knownShortestPathsToTarget = {}
	findPath('Q133957')
	f = open('dump.txt','w+')
	f.write(json.dumps(shortestPaths, sort_keys=True))
	f.close()
answerCache = {}

#from flask import Flask, render_template, request, jsonify#, redirect, url_for, send_from_directory
#app = Flask(__name__)
#@app.route('/')
def index():
	global bestAnswer
	try:
		userInput = request.args.get('q', '')
		print 'userInput:',userInput
		userInputAsId = wikidataSearch(userInput)
		if userInputAsId=='': #no such thing!
			return jsonify(resultInIds=[], resultInLabels=[], wikiLinks=[], naturalDescription='No such thing.')
		else:
			print 'userInputAsId:',userInputAsId,
			if answerCache.has_key(userInputAsId):
				print ', which is already queried before.'
				bestAnswer = answerCache[userInputAsId]
			else:
				print ', which is a new search.'
				findPath(userInputAsId)
				answerCache[userInputAsId] = bestAnswer
			if bestAnswer==[]:
				return jsonify(resultInIds=[], resultInLabels=[], wikiLinks=[], naturalDescription='No relationship found.')
			else:
				print 'Finding Wikipedia links...'
				wikiLinks = {}
				pool = ThreadPool(200) # Sets the pool size
				pool.map(getWikiLink, [itemId for propertyId,itemId in bestAnswer])
				pool.close()	#close the pool 
				pool.join()		#wait for the work to finish
				for propertyId,itemId in bestAnswer:
					thisWikiLink = getWikiLink(itemId)
					if thisWikiLink!='':	#some maybe empty (due to cache)
						wikiLinks[itemId]=getWikiLink(itemId)
				return jsonify(resultInIds=bestAnswer, resultInLabels=convertClaimsFromIdsToLabels(bestAnswer), wikiLinks=wikiLinks, naturalDescription=naturallyDescribeWithClaims(bestAnswer))
	except:
		return jsonify(resultInIds=[], resultInLabels=[], wikiLinks=[], naturalDescription='Something went wrong.')






#For Lino AI

userInput = '水果' # FOR DEBUG
print '>'+userInput # FOR DEBUG
while userInput!='':
	try:
		userInputAsId = wikidataSearch(userInput)
		if userInputAsId=='':
			print '查无此物。'
			raise KeyError
		print '找到了最佳匹配项：',userInputAsId
		userInputAsLabel = wikidataGetEntityProp(userInputAsId,'labels')
		if userInput==userInputAsLabel:
			print '（完美匹配。）'
		elif userInputAsLabel==userInputAsId:
			print '无中文译文。'
			raise KeyError
		else:
			print '您要找的是不是“',userInputAsLabel,'”？'
		userInputAsDescription = wikidataGetEntityProp(userInputAsId,'descriptions')
		if userInputAsDescription!=None:
			print userInput,'是',userInputAsDescription,'。'
		else:
			print '然而并没有找到对应的描述。'
			raise KeyError
	except KeyError:
		print '（本次查询失败。提前进入下一轮。）'
	userInput = raw_input('>')



