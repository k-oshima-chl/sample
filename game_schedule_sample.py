#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import re
from bs4 import BeautifulSoup

import random
import time

import datetime
import copy

import MySQLdb
import os

import calendar


interval_count = 12

# host= os.environ['HOST']
# port= os.environ['PORT']

# database = os.environ['DATABASE']
# username = os.environ['USERNAME']
# password = os.environ['PASSWORD']
# charset = os.environ['CHARSET']

def insert_mysql(players_list):

	connection = MySQLdb.connect(host=host,
								port=port,
								db=database,
								user=username,
								passwd=password,
								charset=charset)
	cursor = connection.cursor()

	for player in players_list:

		print "-------------------------------------"

		string = 'NULL,'
		size = len(player)
		for s in player:
			string +=  '"' +str(s)+'"'
			print string
			
			size -= 1
			if size == 0:
				break
			else:
				string += ','

		sql = 'insert into game_schedule values(%s)'%(string)
		print "sql = [%s]"%(sql)

		cursor.execute(sql)

	connection.commit()
	cursor.close()
	connection.close()


def date_revise(date):

	#月,日を格納
	mon_day = str(date[0])
	index = mon_day.find("/")
	mon = mon_day[4:index]

	day = ""
	for i in range(2):

		if mon_day[index+1+i].isdigit() == False:
			break

		day += mon_day[index+1+i] 

	mon = int(mon)
	day = int(day)

	#時間
	time = list(str(date[1]))

	
	str_hour = ""
	minute = ""
	for i in range(2):
		
		str_hour += time[i]
		minute += time[i+3]

	hour = int(str_hour)
	# minute = int(str_minute)


	#もし時間が24時以降なら日にちを一日上げる
	if int(hour) >= 24:
		hour = int(hour) - 24
		
		day += 1

	#月,日が実際に存在するか確認
	try:
		day_of_week = calendar.weekday(2016,mon,day)
	except:
		mon += 1
		day = 1

	#月+日+時間+分
	mon_day_time = str(mon)+"-"+str(day)+","+str(hour)+"-"+str(minute)
	# print mon_day_time


	return mon_day_time


def time_convert(text):

	number = int(re.compile(r'\d+').search(text).group())

	index = text.find(u"前")

	if -1 >= index:
		index = text.find(u"後")
		#後半
		
		goal_time = 45 + number

	else:
		index = text.find(u"前")
		#前半

		goal_time = number
		
	return goal_time


def foul_convert(text):

	#0がイエロー,1がレッド
	color_type = ''
	if text.span.text == u'警告':
		color_type = '0'
	
	else:
		#レッドカード
		color_type = '1'

	return color_type


#選手名、ホーム・アウェイ、html本体
def player_to_number_convert(name,side,game_soup):
	#先発メンバー
	# for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[0].findAll("tr"):
	for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[side].findAll("tr"):

		t_count = 0
		for t in tr.findAll("td"):

			if t_count == 0:
				player_number = t.text.strip()

			if t_count == 1 and (t.text.strip() == name):
				
				# h_goaler.append(player_number+"-"+str(goal_time))
				return player_number

			t_count += 1


	#ベンチ入り選手
	# for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[0].findAll("tr"):
	for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[side].findAll("tr"):

		# print tr

		t_count = 0
		for t in tr.findAll("td"):

			if t_count == 0:
				player_number = t.text.strip()

			if t_count == 1 and (t.text.strip() == name):

				# h_goaler.append(player_number+"-"+str(goal_time))
				return player_number

			t_count += 1


def leage_schedule(leage_number,start_section):

	schedule_url = "http://soccer.yahoo.co.jp/ws/schedule/"


	section = start_section

	schedule = []
	while True:

		html = urllib2.urlopen(schedule_url+leage_number+"?class="+str(section))

		soup = BeautifulSoup(html,"html.parser")

		main_body = soup.find("div",{"class":"sn-table"})
		table = main_body.find("table")
		tbody = table.find("tbody")

		print "section %d"%(section)
		if 1 >= len(tbody.find("td")):
			print "section = %d"%(section)

			break

		game_day = []

		counter = 0

		for tr in tbody.findAll("tr"):

			game_day.append(int(leage_number))

			
			date = str(tr.findAll("td")[0]).split("<br>")
			date = date_revise(date)

			game_day.append(date)

			game_day.append(section)
			
			home = (tr.findAll("td")[1].a.string).encode('utf-8')
			away = (tr.findAll("td")[5].a.string).encode('utf-8')
			
			game_day.append(home)
			game_day.append(away)

			old_match = 0
			if tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a != None:
				old_match = 1


			#ここから下はゲーム内容のページにスクレイピング
			
			score = ""

			# if tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a != None:
			if old_match == 1:

				game_url = tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a.attrs['href']
				game_html = urllib2.urlopen("http://soccer.yahoo.co.jp"+game_url)
				game_soup = BeautifulSoup(game_html,"html.parser")
				game_main = game_soup.find("div",{"class":"sn-table--gameSummary"}).find("tbody")


				#まだ試合が始まっていないのなら
				# if game_main.findAll("tr")[0].findAll("td")[3].text != None:
				if game_soup.find("div",{"class":"sn-modGameSummary__status"}).text != u"試合前":


					fist_half_goal = game_main.findAll("tr")[0].findAll("td",{"class":"sn-table__itemTd--split"})
					
					#home
					if 2 > len(re.sub(r'[\D]+','',(str(fist_half_goal[0])))):
						home_goal = "0"+re.sub(r'[\D]+','',(str(fist_half_goal[0])))
					else:
						home_goal = re.sub(r'[\D]+','',(str(fist_half_goal[0])))

					#away
					if 2 > len(re.sub(r'[\D]+','',(str(fist_half_goal[1])))):
						away_goal = "0"+re.sub(r'[\D]+','',(str(fist_half_goal[1])))
					else:
						away_goal = re.sub(r'[\D]+','',(str(fist_half_goal[1])))

					#後半が始まっている場合は処理する。
					if len(game_main.findAll("tr")) == 2:
						second_half_goal = game_main.findAll("tr")[1].findAll("td",{"class":""})

						#Home
						if 2 > len(re.sub(r'[\D]+','',(str(second_half_goal[0])))):
							home_goal += "0"+re.sub(r'[\D]+','',(str(second_half_goal[0])))
						else:
							home_goal += re.sub(r'[\D]+','',(str(second_half_goal[0])))

						#Away
						if 2 > len(re.sub(r'[\D]+','',(str(second_half_goal[1])))):
							away_goal += "0"+re.sub(r'[\D]+','',(str(second_half_goal[1])))
						else:
							away_goal += re.sub(r'[\D]+','',(str(second_half_goal[1])))
					else:
						home_goal += "00"
						away_goal += "00"


					score = home_goal + "-"+away_goal
				
				else:
					score = ""


				print "score = %s"%(score)

			game_day.append(score)

			# if tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a != None:


			# if old_match == 1:
				# game_main = game_soup.find("div",{"class":"sn-table--statsGame"}).find("tbody")
				# print game_main

			# print tr


			#ゴールした人を登録
			goal_true = 0
			goaler_tbody = ""

			#ファールした人を登録
			foul_true = 0
			fouler_tbody = ""

			# print 
			# print "[] tr %s"%(tr)
			# print "[][][] %s"%(tr.find("td",{"class":"sn-table__itemTd--gameStatus"}))
			


			# if tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a != None:
			if old_match == 1:

				# print "clear"

				for g in game_soup.findAll("section"):
					if g.find("header").h1.text == u'得点':
						goaler_tbody = g.find("tbody")

						#ゴールがある試合なら1
						goal_true = 1

				for g in game_soup.findAll("section"):
					if g.find("header").h1.text == u'警告・退場':
						fouler_tbody = g.find("tbody")

						#ファールがある試合なら1
						foul_true = 1

			print "%s %s"%(home,away)

			h_goaler = []
			a_goaler = []

			if goal_true == 1:

				goaler_count = 0
				for goaler_td in goaler_tbody.findAll("td"):

					# aタグがあるということは、ゴールをしているプレイヤー
					if goaler_td.find("a") != None:

						if goaler_tbody.findAll("td")[goaler_count] == goaler_td:


							#偶数はホーム側、奇数はアウェイ側
							if goaler_count % 2 == 0:

								# print "<------------------------------------------------->"
								# print "homegoal"
								goal_player_name = goaler_td.a.string.strip()

								goal_time = time_convert(goaler_td.text)

								print "game_soup.findAll %s"%(game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0])
								#先発メンバー
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[0].findAll("tr"):
								
									t_count = 0
									for t in tr.findAll("td"):

										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == goal_player_name):
											# print t.text,player_number

											h_goaler.append(player_number+"-"+str(goal_time))

										t_count += 1

								#ベンチ入り選手
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[0].findAll("tr"):

									# print tr
									t_count = 0
									for t in tr.findAll("td"):

										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == goal_player_name):
											# print t.text,player_number
											
											h_goaler.append(player_number+"-"+str(goal_time))

										t_count += 1

							else:

								# print "<------------------------------------------------->"
								# print "away goal"
								goal_player_name = goaler_td.a.string.strip()

								goal_time = time_convert(goaler_td.text)

								#先発メンバー
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[1].findAll("tr"):
									
									t_count = 0
									for t in tr.findAll("td"):
		
										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == goal_player_name):
											
											# print t.text,player_number
											a_goaler.append(player_number+"-"+str(goal_time))

										t_count += 1

								#ベンチ入り選手
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[1].findAll("tr"):
								
									t_count = 0
									for t in tr.findAll("td"):

										# print "goal_player_name = %s"%(goal_player_name)
										
										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == goal_player_name):
											
											# print t.text,player_number
											a_goaler.append(player_number+"-"+str(goal_time))

										t_count += 1

					goaler_count += 1
				
			#ホーム側のゴールした選手を格納
			h_goaler_size = len(h_goaler)
			p_count = 1
			home_goaler = ""
			for p in h_goaler:
				
				home_goaler += p

				if p_count != h_goaler_size:
					home_goaler += ","

				p_count += 1

			game_day.append(home_goaler)



			#アウェイ側のゴールした選手の格納
			a_goaler_size = len(a_goaler)
			p_count = 1
			away_goaler = ""
			for p in a_goaler:
				
				away_goaler += p

				if p_count != a_goaler_size:
					away_goaler += ","

				p_count += 1

			game_day.append(away_goaler)



			#以下はファールした人を格納する処理
			#
			#
			#
			h_fouler = []
			a_fouler = []


			if foul_true == 1:
		
				fouler_count = 0
				for fouler_td in fouler_tbody.findAll("td"):
					# aタグがあるということは、ゴールをしているプレイヤー
					if fouler_td.find("a") != None:

						if fouler_tbody.findAll("td")[fouler_count] == fouler_td:

							# #偶数はホーム側、奇数はアウェイ側
							if fouler_count % 2 == 0:

								foul_player_name = fouler_td.a.string.strip()
								foul_time = time_convert(fouler_td.text)
								foul_color = foul_convert(fouler_td)

								#先発メンバー
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[0].findAll("tr"):
								
									t_count = 0
									for t in tr.findAll("td"):

										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == foul_player_name):
											# print t.text,player_number

											h_fouler.append(player_number+"-"+str(foul_time)+"-"+foul_color)

										t_count += 1

								#ベンチ入り選手
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[0].findAll("tr"):

									t_count = 0
									for t in tr.findAll("td"):

										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == foul_player_name):
											
											h_fouler.append(player_number+"-"+str(foul_time)+"-"+foul_color)

										t_count += 1

							else:

								foul_player_name = fouler_td.a.string.strip()
								foul_time = time_convert(fouler_td.text)
								foul_color = foul_convert(fouler_td)

								#先発メンバー
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[1].findAll("tr"):
									
									t_count = 0
									for t in tr.findAll("td"):

										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == foul_player_name):
											
											# print t.text,player_number
											a_fouler.append(player_number+"-"+str(foul_time))

										t_count += 1

								#ベンチ入り選手
								for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[1].findAll("tr"):
								
									t_count = 0
									for t in tr.findAll("td"):
										
										if t_count == 0:
											player_number = t.text.strip()

										if t_count == 1 and (t.text.strip() == foul_player_name):
											
											# print t.text,player_number
											a_fouler.append(player_number+"-"+str(foul_time))

										t_count += 1

					fouler_count += 1

			#ホーム側のファールした選手を格納
			h_fouler_size = len(h_fouler)
			p_count = 1
			home_fouler = ""
			for p in h_fouler:

				home_fouler += p

				if p_count != h_fouler_size:
					home_fouler += ","

				p_count += 1

			game_day.append(home_fouler)


			#アウェイ側のファールした選手の格納
			a_fouler_size = len(a_fouler)
			p_count = 1
			away_fouler = ""
			for p in a_fouler:
				
				away_fouler += p

				if p_count != a_fouler_size:
					away_fouler += ","

				p_count += 1

			game_day.append(away_fouler)


			#交代選手枠の格納
			#
			#
			h_rotation = []
			a_rotation = []

			# print 
			# print "[] %s"%(tr)
			# print "[][][] %s"%(tr.find("td",{"class":"sn-table__itemTd--gameStatus"}))

			# if tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a != None:
			if old_match == 1:

				# print "clear"

				for g in game_soup.findAll("section"):
					if g.find("header").h1.text == u'試合経過':
						
						for tr in g.find("tbody").findAll("tr"):

							for td in tr.findAll("td"):

								if td.find("span",{"class":"sn-icon--change"}):

									if td.attrs['class'][0] == u'sn-table__itemTd--textR':
									
										time = str(time_convert(tr.th.span.text))

										a_count = 0
										for a in td.findAll("a"):
											h_rotation_player = player_to_number_convert(a.text.strip(),0,game_soup)
											# print "%s"%(a.text.strip())
											# print "home %s"%(h_rotation_player)

											if a_count % 2 == 0:
												before_rotation = str(h_rotation_player)

											if a_count % 2 == 1:

												# print "/-----------------------/"
												after_rotation = str(h_rotation_player)

												h_rotation.append(time+"-"+before_rotation+"-"+after_rotation)

											a_count += 1

										# print "h_rotation %s"%(h_rotation)

									if td.attrs['class'][0] == u'sn-table__itemTd--textL':
									
										time = str(time_convert(tr.th.span.text))
										
										a_count = 0
										for a in td.findAll("a"):
											a_rotation_player = player_to_number_convert(a.text.strip(),1,game_soup)
											# print "%s"%(a.text.strip())
											# print "away %s"%(a_rotation_player)
											
											if a_count % 2 == 0:
												before_rotation = str(a_rotation_player)

											if a_count % 2 == 1:

												print "/-----------------------/"
												after_rotation = str(a_rotation_player)

												a_rotation.append(time+"-"+before_rotation+"-"+after_rotation)

											a_count += 1
									
										# print "a_rotation %s"%(a_rotation)

									# print "<<<<<<<<<<<<<<<<<<<<<<<<<<<"


			#ホーム側の交代選手を格納
			h_rotation_size = len(h_rotation)
			p_count = 1
			home_rotation = ""

			# print "h_rotation = %s"%(h_rotation)

			for p in h_rotation:

				home_rotation += p

				if p_count != h_rotation_size:
					home_rotation += ","

				p_count += 1

			game_day.append(home_rotation)

			#アウェイ側の交代した選手の格納
			a_rotation_size = len(a_rotation)
			p_count = 1
			away_rotation = ""
			# print "a_rotation = %s"%(a_rotation)
			for p in a_rotation:
				
				away_rotation += p

				if p_count != a_rotation_size:
					away_rotation += ","

				p_count += 1

			game_day.append(away_rotation)



			#先発メンバーとサブメンバーの登録
			staring_member = [""]
			sub_member = [""]

			# if tr.find("td",{"class":"sn-table__itemTd--gameStatus"}).a != None:
			if old_match == 1:

				for m in range(2):

					if m == 1:
						staring_member[0] += ","

					for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[0].findAll("div",{"class","sn-table--memberDouble__item"})[m].findAll("tr"):
					
						if tr.td != None:
							# print tr.td
							staring_member[0] += tr.td.text+"-"
							# print staring_member[0]

					print "-----------------------------------------"

					#ベンチ入り選手
					if m == 1:
						sub_member[0] += ","

					for tr in game_soup.findAll("div",{"class":"sn-table--memberDouble"})[1].findAll("div",{"class","sn-table--memberDouble__item"})[m].findAll("tr"):

						# print tr.td
						if tr.td != None:
							sub_member[0] += tr.td.text+"-"
							# print sub_member

				print "-----------------------------------------"

			game_day.append(staring_member[0])
			game_day.append(sub_member[0])

			
			print game_day
			# print len(game_day)


			schedule.append(game_day)

			game_day = []
			print "--------------------------------------------------------------------"

			
			# デバッグ用
			# if counter == 3:
			# 	break

			# counter += 1

		section += 1

		if section >= 16:
			break

	return schedule

def process_time_print(time):

	print "----------------------------------"
	print 
	print 
	print 
	print 
	print "time :{0}"+time+"[sec]"
	print 
	print 
	print 
	print 
	print "----------------------------------"


if __name__ == '__main__':

	puremia = "52"
	bundes = "56"
	spain = "67"
	serie_a = "53"
	leage_an = "54"
	oranda = "2"
	
	print "Test start"

	start = time.time()
	puremia_list = leage_schedule(puremia,1)
	print puremia_list
	elapsed_time = time.time() - start
	process_time_print(format(elapsed_time))


	start = time.time()
	bundes_list = leage_schedule(bundes,1)	
	print bundes_list
	elapsed_time = time.time() - start
	process_time_print(format(elapsed_time))	


	start = time.time()
	spain_list = leage_schedule(spain,1)
	print spain_list
	elapsed_time = time.time() - start
	process_time_print(format(elapsed_time))


	start = time.time()
	serie_a_list = leage_schedule(serie_a,1)
	print serie_a_list
	elapsed_time = time.time() - start
	process_time_print(format(elapsed_time))


	start = time.time()
	leage_an_list = leage_schedule(leage_an,1)
	print leage_an_list
	elapsed_time = time.time() - start
	process_time_print(format(elapsed_time))


	start = time.time()		
	oranda_list = leage_schedule(oranda,1)
	print oranda_list
	elapsed_time = time.time() - start
	process_time_print(format(elapsed_time))