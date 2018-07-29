# -*- coding: utf-8 -*-
import sys
import re
import ttk
import Tkinter as tk
import requests
import os
import errno
import glob
import StringIO
import ctypes
import json
from ctypes.wintypes import *

from PIL import Image

TARGET_PANEL=2
COMMS_PANEL=3
ROLE_PANEL=4
SYSTEMS_PANEL=1
SYSTEM_MAP=7
GALMAP=6


from config import applongname, appversion
import myNotebook as nb
from config import config

import ctypes
from ctypes.wintypes import *
from sys import platform

VK_F10 = 0x79
WM_KEYDOWN = 0x0100

EnumWindows            = ctypes.windll.user32.EnumWindows
EnumWindowsProc        = ctypes.WINFUNCTYPE(BOOL, HWND, LPARAM)

CloseHandle            = ctypes.windll.kernel32.CloseHandle

GetWindowText          = ctypes.windll.user32.GetWindowTextW
GetWindowText.argtypes = [HWND, LPWSTR, ctypes.c_int]
GetWindowTextLength    = ctypes.windll.user32.GetWindowTextLengthW
GetForegroundWindow 	   = ctypes.windll.user32.GetForegroundWindow



GetProcessHandleFromHwnd = ctypes.windll.oleacc.GetProcessHandleFromHwnd
FindWindow = ctypes.windll.user32.FindWindowW




this = sys.modules[__name__]
this.s = None
this.prep = {}



def debug(d):
	if this.vdebug.get() == "1":
		print '[Screenshot] '+str(d)


def plugin_start():
	"""
	Load Screenshot plugin into EDMC
	"""
	this.bmp_loc = tk.StringVar(value=config.get("BMP"))
	this.png_loc = tk.StringVar(value=config.get("PNG"))
	this.delete_org = tk.StringVar(value=config.get("DelOrg"))
	this.mkdir = tk.StringVar(value=config.get("Mkdir"))
	this.hideui = tk.StringVar(value=config.get("HideUI"))
	this.timer  = tk.StringVar(value=config.get("Timer"))
	this.vdebug  = tk.StringVar(value=config.get("Debug"))
	debug("plugin_start");
	return "Screenshot"


# Settings dialog dismissed
def prefs_changed():
	debug("prefs_changed");
	config.set("BMP", this.bmp_loc.get())
	config.set("PNG", this.png_loc.get())
	config.set("DelOrg", this.delete_org.get())
	config.set("Mkdir", this.mkdir.get())
	config.set("HideUI", this.hideui.get())
	config.set("Timer", this.timer.get())
	config.set("Debug", this.vdebug.get())
	debug_settings()
	display()
	
def debug_settings():
	debug("debug_settings");
	if this.vdebug.get() == "1":
		print "Source Directory "+this.bmp_loc.get()
		print "Target Directory "+this.png_loc.get()
		print "Delete Originals "+this.delete_org.get()
		print "Make System Directory "+this.mkdir.get()
		print "HideUI "+this.hideui.get()
		print "Timer "+this.timer.get()
		print "Debug "+this.vdebug.get()
	

def plugin_prefs(parent,cmdr,is_beta):  
	debug("plugin_prefs");
	frame = nb.Frame(parent)
	frame.columnconfigure(3, weight=1)

	bmp_label = nb.Label(frame, text="Screenshot Directory")
	bmp_label.grid(padx=10, row=0,column=0, sticky=tk.W)

	bmp_entry = nb.Entry(frame, textvariable=this.bmp_loc)
	bmp_entry.grid(padx=10, row=0, column=2,columnspan=2, sticky=tk.EW)

	png_label = nb.Label(frame, text="Conversion Directory")
	png_label.grid(padx=10, row=1, column=0, sticky=tk.W)

	png_entry = nb.Entry(frame, textvariable=this.png_loc)
	png_entry.grid(padx=10, row=1, column=2,columnspan=2, sticky=tk.EW)

	nb.Checkbutton(frame, text="Delete Original File", variable=this.delete_org).grid(padx=10, row=2, column=0, sticky=tk.EW)
	nb.Checkbutton(frame, text="Group files by system directory", variable=this.mkdir).grid(padx=10, row=3, column=0, sticky=tk.EW)
	nb.Checkbutton(frame, text="Hide The User Interface", variable=this.hideui).grid(padx=10, row=4, column=0, sticky=tk.EW)
	nb.Checkbutton(frame, text="Hide the timed capture button", variable=this.timer).grid(padx=10, row=5, column=0, sticky=tk.EW)
	nb.Checkbutton(frame, text="Enable Debugging", variable=this.vdebug).grid(padx=10, row=6, column=0, sticky=tk.EW)
	
	
	
	return frame


	
def plugin_app(parent):
	debug("plugin_app");
	this.parent = parent
	this.container = tk.Frame(parent)
	this.container.columnconfigure(2, weight=1)
	this.label = tk.Label(this.container, text="Screenshot:")
	this.status = tk.Label(this.container, anchor=tk.W, text="Ready")
	this.images = tk.Frame(this.container)
	this.images.grid(row=1,column=0,columnspan=2,sticky=tk.W)
	this.images.columnconfigure(2, weight=1)
	
	this.screenshot = tk.Label(this.images, anchor=tk.W)
	this.screenshot.grid(padx=10, row=0,column=0,columnspan=1, sticky=tk.W)
	this.screenshot.grid_remove()
	this.screenshot.bind("<Button-1>",save_screenshot)  
	this.cropped  = tk.Label(this.images, anchor=tk.W)
	this.cropped.grid(padx=10, row=0,column=1,columnspan=1, sticky=tk.W)
	this.cropped.bind("<Button-1>",save_crop)  
	this.cropped.grid_remove()
	this.label.grid(row=0,column=0, sticky=tk.W)
	this.status.grid(padx=10, row=0,column=1, sticky=tk.W)
	debug_settings()
	display()
	return (this.container)


def display():
	debug("display: "+this.hideui.get())
	if this.hideui.get() == "1":
		debug("Hide Display")
		this.container.grid_remove()
		#this.status.grid_remove()
	else:
		#this.label.grid()
		this.container.grid()
		
def getInputDir():
	debug(this.bmp_loc.get())
	return this.bmp_loc.get()
	
def getOutputDir(system):
	debug("eh"+this.png_loc.get())
		
	if this.mkdir.get() == "1":
		make_sure_path_exists(this.png_loc.get()+'/'+system)
		return this.png_loc.get()+'/'+system
	else:
		return this.png_loc.get()
	
def isHighRes(source):
	if source[0:7] == "HighRes":
		return True
	else:
		return False
	
def getFileMask(source,system,body,cmdr):
	#This will be updated to allow different file mask formats
	#selected from teh front end
	
	sequencemask="[0123456789][0123456789][0123456789][0123456789][0123456789]"
	
	
	mask=system+'('+body+')_'+sequencemask+'.png' 	
	
	# We want to distinguish high res could make this optional
	if isHighRes(source):
		mask='HighRes_'+mask
	
	return mask

def getFilename(source,system,body,cmdr):
	dir = getOutputDir(system)
	debug("Output Directory: "+dir)
	mask = getFileMask(source,system,body,cmdr)
	debug("Output Mask: "+mask)
	
	files = glob.glob(dir+'/'+mask)
	
	
	# This is not very elegant. Is there a better way?
	# counting won't work if there ar gaps in the sequence because of deletions
	n = []
	for elem in files:
		try:  
			n.append(int(elem[-9:-4]))
			debug("elem: "+elem)
		except:
			debug(elem)
		
	if not n:
		n = [0]
			
	
	sequencemask="[0123456789][0123456789][0123456789][0123456789][0123456789]"
	sequence = format(int(max(n))+1, "05d")
	
	fname = dir+'/'+mask.replace(sequencemask,sequence)
	debug("getFileMask: "+fname)
	
	return fname
	
def getBmpPath(source):
    # remove the ED Screenshot part of the name
	bmpfile=source[13:]
	return this.bmp_loc.get()+"\\"+bmpfile
	
def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
	
def thumbnail(img,size,xy):
	temp= img.copy()

	if xy == "x":
		newwidth = size
		newheight = newwidth * (float(temp.size[0])/float(temp.size[1]))
	else:
		newheight = size
		newwidth = size * (float(temp.size[0])/float(temp.size[1]))
		
	
	resize = newwidth, newheight
	
	temp.thumbnail(resize, Image.ANTIALIAS)
	
	cbuf= StringIO.StringIO()
	temp.save(cbuf, format= 'GIF')
	return cbuf.getvalue()	
	
def getGuiFocus():
	status=os.path.expandvars("%userprofile%\Saved Games\Frontier Developments\Elite Dangerous\status.json")
	debug(status)
	with open(status) as json_file:  
		data = json.load(json_file)
	debug(data["GuiFocus"])
	return data["GuiFocus"]
	
def save_screenshot(event):
	if this.crop_status:
		this.im.save(this.converted,"PNG");
		this.status['text'] = "Full Screen Saved"
	
def save_crop(event):
	if this.crop_status:
		this.crop.save(this.converted,"PNG");
		this.status['text'] = "Crop Saved"
	
# Detect journal events
def journal_entry(cmdr, system, station, entry):
	
	display()
	
	if entry['event'] == 'Screenshot':
		#we can set status to error because it wont be shown unless we fail
		this.status['text'] = 'error'	
		focus=getGuiFocus()
		
		original = getBmpPath(entry['Filename'])
		converted = getFilename(entry['Filename'][13:],entry['System'],entry['Body'],cmdr)
		this.converted=converted
		
		#open the image and save it as PNG
		this.im = Image.open(original)
		this.im.save(converted,"PNG");
		
		#create a thumbnail
		this._IMG_THUMB = tk.PhotoImage(data=thumbnail(this.im,75,"y"))
		this.screenshot["image"]=this._IMG_THUMB
		this.screenshot.grid()
			
		
		crop = True
		if focus == TARGET_PANEL:
			debug("TARGET")
			this.crop= this.im.crop((850,279,1306,538))
		elif focus == COMMS_PANEL:
			this.crop= this.im.crop((406,123,919,832))
		elif focus == ROLE_PANEL:
			this.crop= this.im.crop((451,270,1460,837))
		elif focus == SYSTEMS_PANEL:
			this.crop= this.im.crop((451,270,1460,837))	
		else:
			crop = False
		
		if crop and not isHighRes(entry['Filename'][13:]):
			this.crop_status=True;
			debug("Cropping")
			this._IMG_CROP = tk.PhotoImage(data=thumbnail(this.crop,75,"y"))
			this.cropped["image"]=this._IMG_CROP
			this.cropped.grid()
		else:	
			this.crop_status = False
			this.cropped.grid_remove()
		
			
		
		if this.delete_org.get() == "1":
			os.remove(original)
		
				
		this.status['text'] = os.path.basename(converted)

def sendKyePress():
	if game_running():
		running=True
	
	if EliteInForeground():
		this.status['text'] = "Transponder Active"		
		#key.PressKey(VK_F10)
		#sendKeyDown(this.game,VK_F10)
	else:
		this.status['text'] = "Transponder Suspended"
		this.parent.after(1000,transponder)

	

def GetWindowName(h):
	b = ctypes.create_unicode_buffer(255)
	GetWindowText(h,b,255)
	return b.value

def game_running():

	if platform == 'darwin':
		for app in NSWorkspace.sharedWorkspace().runningApplications():
			if app.bundleIdentifier() == 'uk.co.frontier.EliteDangerous':
				return True
	elif platform == 'win32':

		def WindowTitle(h):
			if h:
				l = GetWindowTextLength(h) + 1
				buf = ctypes.create_unicode_buffer(l)
				if GetWindowText(h, buf, l):
					return buf.value
				return None
				
		def callback(hWnd, lParam):
			name = WindowTitle(hWnd)
			if name and name.startswith('Elite - Dangerous'):
				handle = GetProcessHandleFromHwnd(hWnd)
				if handle:	# If GetProcessHandleFromHwnd succeeds then the app is already running as this user
					CloseHandle(handle)
					this.game=hWnd
					return False	# stop enumeration
			return True

		return not EnumWindows(EnumWindowsProc(callback), 0)

	return False
		
def EliteInForeground():
	active = GetForegroundWindow()
	name = GetWindowName(active)
	if name and name.startswith('Elite - Dangerous'):
		return True
	return False