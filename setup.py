#!/usr/bin/env python

from distutils.core import setup
from subprocess import *
import os
import glob

DFEET_VERSION='0.1.6'

#Create an array with all the locale filenames
I18NFILES = []
for filepath in glob.glob("locale/*/LC_MESSAGES/*.mo"):
    targetpath = os.path.dirname(os.path.join("share/", filepath))
    I18NFILES.append((targetpath, [filepath]))

#Create an array with all the help documents (docbook)
HELPDOCS = []
for filepath in glob.glob("help/dfeet/*/*.xml"):
    targetpath = os.path.dirname(os.path.join("share/gnome/", filepath))
    HELPDOCS.append((targetpath, [filepath]))


#Create an array with all the help images
HELPIMAGES = []
for filepath in glob.glob("help/dfeet/*/figures/*.png"):
    targetpath = os.path.dirname(os.path.join("share/gnome/", filepath))
    HELPIMAGES.append((targetpath, [filepath]))
    
#Check if scrollkeeper is available
OMFFILES = []
omfdir = None
try:
    process = Popen(args=["scrollkeeper-config", "--omfdir"], stdout=PIPE)
except OSError:
    #Not available. Skip the registration.
    pass
else:
    #Obtain the OMF repository directory to install and register the help files
    omfdir = os.path.join(process.stdout.read().strip(), "dfeet")
    OMFFILES.append((omfdir, glob.glob("help/dfeet/*.omf")))
        
dist = setup(name='d-feet',
    version=DFEET_VERSION,
    author='John (J5) Palmieri',
    author_email='johnp@redhat.com',
    maintainer='John (J5) Palmieri',
    maintainer_email='johnp@redhat.com',
    description='D-Bus debugger',
    long_description='D-Feet is a powerful D-Bus debugger',
    url='http://hosted.fedoraproject.org/projects/d-feet/',
    download_url='https://hosted.fedoraproject.org/projects/d-feet/',
    license='GNU GPL',
    platforms='linux',
    scripts=['d-feet'],
    packages=['dfeet', 'dfeet/_ui'],
    data_files=[
        ('share/dfeet', glob.glob("ui/*.ui")),
        ('share/icons/hicolor/48x48/apps', ['ui/dfeet-icon.png']),
        ('share/applications', ['ui/dfeet.desktop']),
        ]+I18NFILES+HELPDOCS+HELPIMAGES+OMFFILES
)

#Non-documented way of getting the final directory prefix
installCmd = dist.get_command_obj(command="install_data")
installdir = installCmd.install_dir
installroot = installCmd.root

if not installroot:
    installroot = ""

if installdir:
    installdir = os.path.join(os.path.sep,
            installdir.replace(installroot, ""))

# Update the real URL attribute inside the OMF files
# and register them with scrollkeeper
if omfdir != None and installdir != None and dist != None:
    
    #Create an array with the docbook file locations
    HELPURI = []
    for filepath in glob.glob("help/dfeet/*/dfeet.xml"):
        targeturi = os.path.join(installdir, "share/gnome/", filepath)
        HELPURI.append(targeturi)
    
    #Replace the URL placeholder inside the OMF files
    installedOmfFiles = glob.glob(installroot + omfdir + "/*.omf")
    for fileNum in range(0, len(installedOmfFiles)):
        call(["scrollkeeper-preinstall", HELPURI[fileNum],
            installedOmfFiles[fileNum], installedOmfFiles[fileNum]])
        
    #Update the scrollkeeper catalog
    if os.geteuid() == 0:
        print "Updating the scrollkeeper index..."
        call(["scrollkeeper-update", "-o", installroot + omfdir])

print "\nInstallation finished! You can now run d-feet by typing 'd-feet' or through your applications menu icon."
    
## To uninstall manually delete these files/folders:
## /usr/bin/d-feet
## /usr/share/dfeet/
## /usr/share/gnome/help/dfeet/
## /usr/icons/hicolor/48x48/apps/dfeet-icon.png
## /usr/share/locale/*/LC_MESSAGES/dfeet.mo
## /usr/share/pixmaps/dfeet-icon.png
## /usr/share/applications/dfeet.desktop
## /usr/lib/python2.X/site-packages/dfeet/
## omfdir/dfeet/*.omf
