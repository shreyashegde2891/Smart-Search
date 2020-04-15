# pythonspot.com
from flask import Flask, render_template, flash, request, Markup
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, SelectField
import glob
import os 
import subprocess
import sys
from JIRA_tfidf import tf_idf
from jira import JIRA

# Import the email modules
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

import datetime
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging 
logging.basicConfig(filename="search.log", 
                    format='%(asctime)s %(message)s', 
                    filemode='w') 
logger=logging.getLogger()
logger.setLevel(logging.INFO) 

#from Jira_createModel import tidif_createModel
# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'


	
def getModelList(path):
	files = [os.path.basename(f) for f in glob.glob(path + "**/*.pkl", recursive=True)]
	res = [(val, val) for val in files]
	return res

class ReusableForm(Form):
	name = TextField('UserName:', validators=[validators.required()])
	password = TextField('Password:', validators=[validators.required(), validators.Length(min=3, max=35)])
	issue = TextField('Issue:', validators=[validators.required()])
	model = SelectField('Model:',choices=getModelList("C:\\JIRA-Similar-Issue-Finder-App-master\\Models"))
	#email = SelectField('Recieve an Email?:',choices=[("yes","yes"),("no","no")])

class createForm(Form):
	name = TextField('UserName:', validators=[validators.required()])
	password = TextField('Password:', validators=[validators.required(), validators.Length(min=3, max=35)])
	filter = TextField('Filter:', validators=[validators.required()])
	modelName = TextField('ModelName:', validators=[validators.required()])
	#model = SelectField('Model:',choices=getModelList("C:\\JIRA-Similar-Issue-Finder-App-master\\Models"))
 
 
@app.route("/", methods=['GET', 'POST'])
def modelQuery():
	form = ReusableForm(request.form)
	form.model.choices=getModelList("C:\\JIRA-Similar-Issue-Finder-App-master\\Models")
    
	print (form.errors)
	if request.method == 'POST':
	
		name=request.form['name']
		password=request.form['password']
		issue=request.form['issue']
		model=request.form['model']
		#email=request.form['email']
		print (name, " ", issue, " ", model)
		logger.info("New Request Recieved : " + name + " " + issue + " " + model) 
 
		if form.validate():
			flash(Markup('<b>Thanks for trying the tool. Please find your results below.</b>'))
			flash(Markup('<br>'))
			jira_url = <Enter your jira URL>
			authed_jira = JIRA(jira_url,auth=(name, password))
			logger.info("Authed Jira Object " + str(authed_jira))
			logger.info("-----------------------------------------------------------------------------------------------------------------------------")
			#similar_issue_list=tf_idf(name,password,model,issue)
			similar_issue_list=tf_idf(authed_jira,model,issue)
			for items in similar_issue_list:
				issue = authed_jira.issue(items)
				url=<Enter your jira URL>+items
				
				try:
					fixField = issue.raw['fields']['customfield_11114']['value']
				except Exception as e:
					fixField = "Not Available"
				
				try:
					resField = issue.raw['fields']['resolution']['name']
				except Exception as e:
					resField = "Not Available"
				
				flash(Markup('<a href="' + url +'" target="_blank" rel="noopener noreferrer">' + url + '</a>'))
				flash(Markup('<u>Summary: </u>' + issue.raw['fields']['summary']))
				flash(Markup('<u>Resolution: </u>' + resField))
				flash(Markup('<u>Fix Area: </u>' + fixField))
				flash(Markup('<br>'))
				#flash("\n")
				
		else:
			flash('Error: All the form fields are required. ')
 
	return render_template('search.html', form=form)

@app.route("/create", methods=['GET', 'POST'])
def createModel():
	form = createForm(request.form)
 
	print (form.errors)
	if request.method == 'POST':
	
		name=request.form['name']
		password=request.form['password']
		filter=request.form['filter']
		modelName=request.form['modelName']
		
		print (name, " ", filter, " ", password , " ", modelName)
 
		if form.validate():
			flash("Your model might take some time. The model should be available in the list within the next hour.")
			#exec_cmd = "python Jira_createModel.py " + name + " " + password + " '" + filter + "' " + "'" + modelName + "'"
			#subprocess.Popen(exec_cmd)
			subprocess.Popen(['python','Jira_createModel.py',name, password, filter, modelName])
			email_subject = "Jira Similar Issue Finder Tool: Your Model Request"
			email_message = "Hi " + name + ",\n\n" + "Your Request for Creating a new model for the below Jira Filter has been succesfully received.\n\n" + filter + "\n\n" + "Your Model should be available in the list within the next hour\n"
			email_recipients = <email recepients>
			msg = MIMEMultipart('alternative')
			msg['Subject'] = email_subject
			msg['From'] = <email id>
			msg['To'] = email_recipients
			msg['Cc'] = <email id>
			part1 = MIMEText(email_message, 'plain')
			msg.attach(part1)
			smtpMailObj = smtplib.SMTP(<smtp host>)
			smtpMailObj.sendmail(<email id>, email_recipients, msg.as_string())
			
				
		else:
			flash('Error: All the form fields are required. ')
 
	return render_template('create.html', form=form)
 
if __name__ == "__main__":
    app.run(host='0.0.0.0')
