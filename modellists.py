'''
Functions such as getting models list, details for livestreamer, etc.
'''
from config import *
from bs4 import BeautifulSoup
import re
import time, datetime
import signal, os
import subprocess
import psutil
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders

def Models_list(client):
	# Moving to followed models page
	try:
		logging.info("Redirecting to " + URL_follwed)
		r2 = client.get(URL_follwed)
	except Exception, e:
		logging.error('Some error during connecting to '+URL)
		logging.error(e)
		print ('error connecting to chaturbate')
		return ''
	soup = BeautifulSoup(r2.text)
	#logging.debug('Page Source for ' + URL_follwed + '\n' + r2.text)
	page_source = 'Page Source for ' + URL_follwed + '\n' + r2.text
	if Debugging == True:
		Store_Debug(page_source, "modellist.log")
	ul_list = soup.find('ul', class_="list")
	li_list = soup.findAll('li', class_="cams")
	#logging.debug(li_list)
	if Debugging == True:
		Store_Debug(li_list, "li_list.log")
	## Finding who is not offline
	online_models = []
	for n in li_list:
		if n.text != "offline":
			if n.parent.parent.parent.div.text == "IN PRIVATE":
				logging.warning(n.parent.parent.a.text[1:] + ' model is now in private mode')
			else:
				online_models.append(n.parent.parent.a.text[1:])
	logging.info('[Models_list] %s models are online: %s'  %(len(online_models),str(online_models)))
	return online_models

def Select_models(Models_list):
    # Select models that we need
    Wish_list = Wishlist()
    Model_list_approved = []
    logging.info('[Select_models] Which models are approved?')
    for model in Models_list:
    	if Disable_wishlist == False:
	        if model in Wish_list:
	            logging.info("[Select_models] " + model+ ' is approved')
	            Model_list_approved.append(model)
	else:
		logging.info("[Select_models] " + model+ ' is approved')
	        Model_list_approved.append(model)
    if len(Model_list_approved) == 0:
        logging.warning('[Select_models]  No models for approving')
    return Model_list_approved

def Compare_lists(ml, mlr):
    for model in mlr:
        if checkIfModelRecorded(model) == False:
            logging.debug("[Compare_lists CheckModelRecorded] Model " + model + " is supposed to be recording, but I could not find the process.")
            print ("[Compare_lists CheckModelRecorded] Model " + model + " is supposed to be recording, but I could not find the process.")
            try:
                mlr.remove(model)
            except ValueError:
                pass # Model was removed from the modellist WHILE we are iterating over it (recording process ended properly?)
    # Comparing old models list(Main list) to new(updated) models list
    # This loop is used for removing offline models from main list
    ml_new = []
    logging.info('[Compare_lists] Checking model list:')
    for model in ml:
    	if model in mlr:
    		logging.info("[Compare_lists] " + model + " is still being recorded")
    		logging.debug("[Compare_lists] Removing " + model + " model")
    	else:
    		logging.debug("[Compare_lists] " + model + " is online")
    		ml_new.append(model)
    logging.debug("[Compare_lists] List of models after comparing:" + str(ml_new))
    return ml_new

def checkIfModelRecorded(model):
	_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t
	for proc in psutil.process_iter():
		try:
			cmd = ' '.join(proc.cmdline())
			if _u(model) in _u(cmd):
				return True
		except (psutil.NoSuchProcess, psutil.AccessDenied):
			# Process we tried to look at vanished while iterating over the processlist
			# or we have no permissions to look at it's cmdline (maybe a superuser process?)
			pass
	return False

def sendMail(to, fro, subject, text, files=[],server="localhost"):
    assert type(to)==list
    assert type(files)==list
 
 
    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
 
    msg.attach( MIMEText(text) )
 
    smtp = smtplib.SMTP(server)
    smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

def addmodel(modelname):
    models_online
    # Checking that it's not already recording model
    if modelname in models_online:
        if checkIfModelRecorded(modelname) == False:
            print ("[CheckModelRecorded] Model " + modelname + " is supposed to be recording, but I could not find the process.")
            logging.debug("[CheckModelRecorded] Model " + modelname + " is supposed to be recording, but I could not find the process.")
            models_online.remove(modelname)
    if not modelname in models_online:
        logging.debug('emailEnable = '+emailEnable)
        if emailEnable == 'True':
            logging.info('sending email for '+modelname)
            sendMail(emailTo,emailFrom,"Recording Started","%s is now being recorded" % modelname)
        try:
            models_online.append(modelname)
            logging.info('Starting recording of ' + modelname)
            timestamp = time.strftime("%d-%m-%Y_%H-%M-%S")
            path = Video_folder+'/'+modelname+'/'+modelname+'_'+timestamp+'.mp4'
            if not os.path.exists(Video_folder+'/'+modelname):
                logging.info('creating directory ' + Video_folder+'/'+modelname)
                os.makedirs(Video_folder+'/'+modelname)
            # Starting livestreamer
            FNULL = open(os.devnull, 'w')
            modelname = str(modelname)
            subprocess.check_call([LIVESTREAMER, '-Q', '-o',path,'http://chaturbate.com/' + modelname, 'best'], stdout=FNULL, stderr=subprocess.STDOUT)
            #subprocess.check_call([LIVESTREAMER, '-Q', '--hls-segment-threads', '6','-o',path,'https://chaturbate.com/' + modelname, 'best'], stdout=FNULL, stderr=subprocess.STDOUT)
            # subprocess.check_call(['livestreamer.exe', '-Q', '--hls-segment-threads', '6','-o',path,'https://chaturbate.com/' + modelname, 'best'])
            models_online.remove(modelname)
        except Exception:
            logging.info('No stream on ' + modelname)
