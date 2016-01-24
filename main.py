# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests, json, os, itertools, time
from multiprocessing.dummy import Pool as ThreadPool
timeLimit = 60
userInputCache = {}
def multithreadWrapper(function, parameter):
	pool = ThreadPool(200) # Sets the pool size
	results = pool.map(function, parameter)
	pool.close()	#close the pool 
	pool.join()		#wait for the work to finish
	return results
def wikiRequestWrapper(params):
	return requests.get('https://www.wikidata.org/w/api.php',params=params).json()
def wikidataSearch(userInput):
	'''This function translates user input to Wikidata Id.'''
	if userInputCache.has_key(userInput):
		return userInputCache[userInput]
	else:
		result = wikiRequestWrapper({
			'action':'wbsearchentities',
			'search':userInput,
			'language':'en',
			'format':'json',
			'limit':'1'})
		if result['success']!=1:
			#DEBUG# print 'WARNING: No match found.'
			result = ''
		try:
			result = result['search'][0]['title']
		except:
			result = ''
		userInputCache[userInput] = result
		return result
claimsCache = {}
def wikidataGetClaims(entityId):
	'''Retrives claims for entity by id.'''
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
def expandClaims(claimsInDict):
	'''This makes 
	{"P123":["Q1","Q2"],
	 "P200":["Q55"]}
	  -> 
	[("P123","Q1"),
	 ("P123","Q2"),
	 ("P200","Q55")], for the sake of easier looping.'''
	claimsInList = []
	for propertyId,itemIds in claimsInDict.items():
		for itemId in itemIds:
			claimsInList.append((propertyId,itemId))
	return claimsInList
def explore(testItemId):
	global pathsTo, nodesOnNextLevelFor, ifFoundAnswer, bestAnswer
	for propertyId,itemId in expandClaims(wikidataGetClaims(testItemId)):
		if not (propertyId in ['P1343'] or itemId in ['Q4167836']): #BLACKLIST
			nodesOnNextLevelFor[A].update([itemId])
			newPath = pathsTo[A][testItemId]+[(propertyId,itemId)]
			if itemId in pathsTo[B].keys():
				#print 'SUCCESS!'
				ifFoundAnswer = True
				knownShortestPathToTarget = pathsTo[B][itemId]
				knownShortestPathToTarget.reverse()
				newAnswer = newPath+knownShortestPathToTarget
				knownShortestPathToTarget.reverse()
				if len(bestAnswer)>len(newAnswer) or len(bestAnswer)==0: #this may NOT be the shortest, since not all nodes in this depth are checked.
					#DEBUG# print '[UPDATE]Updating best answer from', bestAnswer, 'to', newAnswer,'.' #This is rare if happened. 
					bestAnswer = newAnswer
				return #just to halt the procedure.
			else: #sadly, we have to go on:
				if pathsTo[A].has_key(itemId):
					lengthOfOldPath = len(pathsTo[A][itemId])
				else:
					lengthOfOldPath = 99999
				lengthOfNewPath = len(newPath)
				#print 'lengthOfNewPath:',lengthOfNewPath
				if lengthOfOldPath>lengthOfNewPath:
					#then we gotta update it
					pathsTo[A][itemId] = newPath
	if time.time() - startTime > timeLimit:
		nodesOnNextLevelFor[A] = set() #Empty this set, so that the next round can barely continue.

pathsTo = {}
def main(userInputA = 'phitsanulok', userInputB = 'lollipop'):
	global pathsTo, nodesOnNextLevelFor, ifFoundAnswer, bestAnswer, A, B, startTime
	#convert user raw input into wikidata id's:
	startTime = time.time()
	A = wikidataSearch(userInputA)
	B = wikidataSearch(userInputB)
	bestAnswer = []
	if not (A == '' or B == '' or A == B):
		#DEBUG# print 'Finding relation between "'+userInputA+'" ('+A+') and "'+userInputB+'" ('+B+') ...'
		if pathsTo.has_key(A) and pathsTo[A].has_key(B):
			#DEBUG# print '[CACHE]Found result from previous searches!'
			bestAnswer = pathsTo[A][B]
		elif pathsTo.has_key(B) and pathsTo[B].has_key(A):
			#DEBUG# print '[CACHE]Found result from previous searches!'
			bestAnswer = pathsTo[B][A]
		else:
			if not pathsTo.has_key(A): pathsTo[A] = {A:[('TERMINAL',A)]}
			if not pathsTo.has_key(B): pathsTo[B] = {B:[('TERMINAL',B)]}
			nodesOnThisLevelFor = {A:set(),B:set()} #stores a backup of nodesOnNextLevelFor[A] on every single level.
			nodesOnNextLevelFor = {A:set([A]),B:set([B])} #This set describes all the nodes that we want to look into at the next round of looping.
			ifFoundAnswer = False
			levelLimit = 10
			while levelLimit>0 and len(nodesOnNextLevelFor[A])+len(nodesOnNextLevelFor[B])>0 and not ifFoundAnswer:
				levelLimit -= 1
				#DEBUG# print '[DEPTH]Currently on level',levelLimit,'...'
				#DEBUG# print '[SWITCH]First, look at A side...'
				nodesOnThisLevelFor[A] = nodesOnNextLevelFor[A] #back it up. By "it", I mean "nodesOnNextLevelFor[A]".
				nodesOnNextLevelFor[A] = set() #Empty this set. We wait for child-threads to update this set.
				results = multithreadWrapper(explore, nodesOnThisLevelFor[A])
				#DEBUG# print '[SWITCH]Switching side to B...'
				temp = B
				B = A
				A = temp
				nodesOnThisLevelFor[A] = nodesOnNextLevelFor[A] #back it up. By "it", I mean "nodesOnNextLevelFor[A]".
				nodesOnNextLevelFor[A] = set() #Empty this set. We wait for child-threads to update this set.
				results = multithreadWrapper(explore, nodesOnThisLevelFor[A])
				#DEBUG# print '[SWITCH]Switching back to prepare for next level...'
				temp = B
				B = A
				A = temp
	print '===== Best answer:', bestAnswer #timed out :( or success :)
	return bestAnswer#print '===== Best answer:', pathBeautifier(convertClaimsFromIdsToLabels(bestAnswer)) #timed out :( or success :)
#DEBUG# print main()
from flask import Flask, render_template, request, jsonify#, redirect, url_for, send_from_directory
app = Flask(__name__)
@app.route('/')
def s():
	return render_template('index.html')
@app.route('/run', methods=['POST'])
def run():
	return jsonify(r=main(userInputA = request.form['a'], 
		 				  userInputB = request.form['b']))
if __name__=='__main__':
	app.run(host="0.0.0.0",port=int("80"))#,debug=True)#,threaded=True)