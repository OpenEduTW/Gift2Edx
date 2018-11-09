import os
from flask import Flask, render_template, request, url_for, redirect, session,send_from_directory
from lxml import etree
import re
from functools import wraps
from werkzeug import secure_filename

from flask_uploads import UploadSet, configure_uploads, TEXT,patch_request_class

app = Flask(__name__)
app.config['UPLOADED_FILE_DEST'] = os.getcwd()
app.config['UPLOADED_FILE_ALLOW'] = TEXT


texts = UploadSet('FILE')
configure_uploads(app, texts)
patch_request_class(app)




@app.route('/', methods=['GET', 'POST'])
def index(data=None):
	if request.method == "POST" and 'file' in request.files:
		filename = texts.save(request.files['file'])
		file_url = texts.url(filename)
		data = gift2edx(texts.path(filename))
		return render_template('items/index.html', data=data)
	else:
		return render_template('items/index.html', data=data)



def gift2edx(file):
	f = open(file,'r', encoding="utf-8")
	lines = f.readlines()

	#例外 生成txt
	def show(myList):
		for x in range(len(myList)):
			print(x,myList[x],end="")



	for x in range(len(lines)):
		lines[x]=re.sub(':.*.:\Dhtml\D',"",lines[x])
		lines[x]=lines[x].replace('\=','=')
		lines[x]=lines[x].replace('\:',':')
		lines[x]=lines[x].replace('\{','{')
		lines[x]=lines[x].replace('\}','}')
		lines[x]=lines[x].replace('\#',' #')
		lines[x]=lines[x].replace('\\n','<br/>')
		lines[x]=lines[x].replace('&lt;','<')
		if re.match('//.*',lines[x])!= 'None':
			lines[x] = re.sub('// question.*', '', lines[x])
			lines[x] = re.sub('[$].*','',lines[x])
		if len(lines[x])==1:
			lines[x] = lines[x].replace("\n","")
	lines = [e for e in lines if e]


	for x in range(len(lines)):
		if len(lines[x])==1:
			lines[x] = lines[x].replace("\n","")

	show(lines)#印出簡化過後的版本

	#計算總題目數量
	total = 0
	for x in range(len(lines)):
		if(lines[x][0] == '<'):
			total= total+1
	print('\n')
	#print('總題數',total)


	#以下判斷加入XML格式

	#題目root tag 設為<problem>
	root = etree.Element("problem")

	def Multiple_choice_question(q_n,index,element,lines):
		print (index+1,".it is a Multiple_choice_question",lines[element])
		q_response = etree.SubElement(root, "multiplechoiceresponse") 
		label = etree.SubElement(q_response, "label")
		
		q_group = etree.SubElement(q_response, "choicegroup")
		q_group.set("type","MultipleChoice")
		str1 = lines[element]
		
		c = element
		
		ll = lines[element]
		str3 = ll[0:len(ll)-2]
		str3 = str3.replace("<p>","")
		str3 = str3.replace("</p>","")
		str3 = (".\n"+str3)
		index = index+1
		label.text = ("Q")+str(index)+str3+("<br/>")
		
		for i in range(1,q_n):
			if(lines[element + i][1] == '='):
				choice_T = etree.SubElement(q_group,"choice")
				choice_T.set("correct","true")
				str1 = lines[element + i]
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
				choice_T.text = str1[2:len(str1)]
			else:
				if(lines[element + i][2] =='#')&(lines[element + i][3] =='#'):
						lines[element] = re.sub('[*]','',lines[element])
						break
				choice_F = etree.SubElement(q_group,"choice")
				choice_F.set("correct","false")
				str2 = lines[element + i]
				str2 = str2.replace("<p>","")
				str2 = str2.replace("</p>","")
				choice_F.text = str2[2:len(str2)]
				
	def Multiple_selection_question(q_n,index,element,lines):
		print (index+1,".it is a Multiple_selection_question",lines[element])
		
		q_response = etree.SubElement(root, "choiceresponse") 
		label = etree.SubElement(q_response, "label")
		
		q_group = etree.SubElement(q_response, "checkboxgroup")
		str1 = lines[element]
		
		c = element
		
		ll = lines[element]
		str3 = ll[0:len(ll)-2]
		str3 = (".\n"+str3)
		str3 = str3.replace("<p>","")
		str3 = str3.replace("</p>","")
		index = index+1
		label.text = ("Q")+str(index)+str3+("<br/>")

		for i in range(1,q_n):
			if(lines[element + i][3] != '-'):
				if(lines[element + i][2] == '%'):
					choice_T = etree.SubElement(q_group,"choice")
					choice_T.set("correct","true")
					str1 = lines[element + i]
					str1 = str1.replace("<p>","")
					str1 = str1.replace("</p>","")
					str1 = re.sub('[~][%][0-9][0-9][0-9][%]','',str1)
					str1 = re.sub('[~][%][0-9][0-9][%]','',str1)
				
					choice_T.text = str1[1:len(str1)]
				else:
					choice_F = etree.SubElement(q_group,"choice")
					choice_F.set("correct","false")
					str2 = lines[element + i]
					str2 = str2.replace("<p>","")
					str2 = str2.replace("</p>","")
					str2 = re.sub('[~][%][-][0-9][0-9][%]','',str2)
					str2 = re.sub('[~]','',str2)
					choice_F.text = str2[1:len(str2)]
			else:
				choice_F = etree.SubElement(q_group,"choice")
				choice_F.set("correct","false")
				str2 = lines[element + i]
				str2 = str2.replace("<p>","")
				str2 = str2.replace("</p>","")
				#str2 = str2.replace("^~%\-|0-9][0-9]%","")#^[\-|0-9][0-9]* 
				str2 = re.sub('[~][%][-][0-9][0-9][%]','',str2)
				str2 = re.sub('[~]','',str2)
				choice_F.text = str2[1:len(str2)]
				
				
		
	def Short_answer_question(q_n,index,element,lines):
		print (index+1,".it is a Short_answer_question",lines[element])
		q_response = etree.SubElement(root, "stringresponse") 
		label = etree.SubElement(q_response, "label")
		
		#q_response.set("answer",str)
		
		#q_group.set("answer",str)
		
		textline = etree.SubElement(q_response,"textline")
		textline.set("size","20")
		str1 = lines[element]
		c = element
		ll = lines[element]
		str3 = ll[0:len(ll)-2]
		str3 = (".\n"+str3)
		str3 = str3.replace("<p>","")
		str3 = str3.replace("</p>","")
		index = index+1
		#str3 = str3.replace('&amp;gt;','>')
		#str3 = str3.replace('&amp;lt;','<')
		label.text = ("Q")+str(index)+str3+("<br/>")
		#label.text = label.text.replace('&amp;lt;','<')

		for i in range(1,q_n):
			if(lines[element + i][2] =='#')&(lines[element + i][3] =='#'):
				lines[element] = re.sub('[*]','',lines[element])
			if(lines[element + i][3] == '1')&(q_n == 2):
				str1 = lines[element + i]
				str1 = re.sub('[=][%][0-9][0-9][0-9][%]','',str1)
				str1 = str1[1:len(str1)-2]
				q_response.set("answer",str1)
				break
			elif(lines[element + i][3] == '1')&(q_n > 2):
				if i == 1:
					str1 = lines[element + i]
					str1 = re.sub('[=][%][0-9][0-9][0-9][%]','',str1)
					str1 = str1[1:len(str1)-2]
					q_response.set("answer",str1)
					#q_group.set("answer",str1)\
				else:
					str1 = lines[element + i]
					if(lines[element + i][2] =='#')&(lines[element + i][3] =='#'):
						break
					str1 = re.sub('[=][%][0-9][0-9][0-9][%]','',str1)
					str1 = str1[1:len(str1)-2]
					#q_response.set("answer",str1)
					q_group = etree.SubElement(q_response, "additional_answer")
					q_group.set("answer",str1)
				
				
		

	def Matching_question(q_n,index,element,lines):
		print (index+1,".it is a Matching_question ,edx doesn't support",lines[element])
		print("")

	def TF_question(i,a,myList):
		#print (i+1,".it is a TF_question",myList[a])
		str1 = myList[a]
		
		q_response = etree.SubElement(root, "multiplechoiceresponse") 
		label = etree.SubElement(q_response, "label")
		q_group = etree.SubElement(q_response, "choicegroup")
		q_group.set("type","MultipleChoice")

		if (str1.find("{TRUE}")!= -1)|str1.find("T")!= -1:
			choice_T = etree.SubElement(q_group,"choice")
			choice_T.set("correct","true")
			choice_T.text = 'True'
			
			choice_F = etree.SubElement(q_group,"choice")
			choice_F.set("correct","false")
			choice_F.text = 'False'
			if (str1.find("{TRUE}")!= -1):
				str1 = str1.replace('{TRUE}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
			else:	
				str1 = str1.replace('{T}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")

		else:
			choice_T = etree.SubElement(q_group,"choice")
			choice_T.set("correct","false")
			choice_T.text = 'True'
			
			choice_F = etree.SubElement(q_group,"choice")
			choice_F.set("correct","true")
			choice_F.text = 'False'
			if (str1.find("{FALSE}")!= -1):
				str1 = str1.replace('{FALSE}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
			else:	
				str1 = str1.replace('{F}',"")
				str1 = str1.replace("<p>","")
				str1 = str1.replace("</p>","")
		i = i+1
		str1 = (".\n"+ str1)
		label.text = ("Q")+str(i)+str1+("<br/>")#放題目 需要先做處理
		


	top = len(lines) #list長度
	def collect(a,myList):
		while myList[a][len(myList[a])-2] != '}':
				a = a+1
		return a+1


	b = 0 #題目位於lines第幾格
	numlist = [0]
	for i in range(total):
		#print('題目編號=',i,',起始欄位:',b)#看題目位於哪個位置
		if b<top-1:
			b = collect(b,lines) #回傳下一個題目位置
			numlist.append(b)#收集題目起始位置放入list

	for index, element in enumerate(numlist):
		
		if element<top:
			if (lines[element][len(lines[element])-2] == '}')|(lines[element][len(lines[element])-1] == '}'):
				TF_question(index,element,lines)
			else:
				count = 0
				count2 = 0
				q_n = 0 #有幾個選項
				c = element
				while lines[c][0] != '}':
					if (lines[c][1]) == '=':
						count = count + 1
					if (lines[c][2]) == '%':
						count2 = count2 + 1
					c = c + 1
					q_n = q_n + 1
				count2 = count2 #計算＃有幾個
				#print("count = ",count,"count2 = ",count2)
				if count == 0:
					Multiple_selection_question(q_n,index,element,lines)
				elif count == 1 & (count2 == 0):
					Multiple_choice_question(q_n,index,element,lines)
				elif count == count2:
					#print (".it is a Short_answer_question")
					Short_answer_question(q_n,index,element,lines)
				elif count == (q_n - 1) :
					Matching_question(q_n,index,element,lines)
		else:
			break
		




	x = etree.tostring(root, encoding='unicode', method = 'xml',pretty_print=True)
	x = x.replace('&amp;lt;','&lt;')
	x = x.replace('&amp;gt;','&gt;')

	with open("output.txt", "w", encoding="utf-8") as output_file:
		   output_file.write(x)





	#--------*關檔---------
	f.close()
	output_file = open("output.txt", "r", encoding="utf-8")
	text = output_file.read()
	output_file.close
	#--------------------
	return text

if __name__ == "__main__":
    app.run(debug='on')