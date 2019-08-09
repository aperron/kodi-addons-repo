# *
# *  Copyright (C) 2012-2013 Garrett Brown
# *  Copyright (C) 2010      j48antialias
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  Based on code by j48antialias:
# *  https://anarchintosh-projects.googlecode.com/files/addons_xml_generator.py
 
""" addons.xml generator """

import csv, sys, os, shutil, zipfile, xmltodict
from jinja2 import Environment, FileSystemLoader
from urllib.request import urlopen

class Generator:
	"""
		Generates a new addons.xml file from each addons addon.xml file
		and a new addons.xml.md5 hash file. Must be run from the root of
		the checked-out repo. Only handles single depth folder structure.
	"""
	def __init__( self ):
		
		# start
		addons = {}

		# read csv & load information from github
		with open('github_repos.csv', 'r') as csvFile:
			reader = csv.reader(csvFile)
			for row in reader:
				url = "https://raw.githubusercontent.com/%s/master/addon.xml" % row[0]
				file = urlopen(url)
				data = file.read()
				file.close()

				addons[row[0]] = data
		csvFile.close()


		self._generate_addons_file(addons)
		self._generate_md5_file()
		self._generate_downloader(addons)
		# notify user
		print("Finished updating addons xml and md5 files")

	def _generate_addons_file( self, addons ):

		# final addons text
		addons_xml = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n"
		# loop thru and add each addons addon.xml file
		for addon in addons:
			try:
				# split lines for stripping
				xml_lines = addons[addon].splitlines()
				# new addon
				addon_xml = ""
				# loop thru cleaning each line
				for line in xml_lines:
					# skip encoding format line
					line = line.decode()
					if ( line.find( "<?xml" ) >= 0 ): continue
					# add line
					addon_xml += line.rstrip() + "\n"
				# we succeeded so add to our final addons.xml text
				addons_xml += addon_xml.rstrip() + "\n\n"
			except Exception as e:
				# missing or poorly formatted addon.xml
				print("Excluding %s: %s" % ( addon,  e ))
		# clean and add closing tag
		addons_xml = addons_xml.strip() + "\n</addons>\n"
		# save file
		self._save_file( addons_xml.encode( "UTF-8" ), file="build/addons.xml" )

	def _generate_md5_file( self ):
		# create a new md5 hash
		try:
			import md5
			m = md5.new( open( "build/addons.xml", "r" ).read() ).hexdigest()
		except ImportError:
			import hashlib
			m = hashlib.md5( open( "build/addons.xml", "r", encoding="UTF-8" ).read().encode( "UTF-8" ) ).hexdigest()

		# save file
		try:
			self._save_file( m.encode( "UTF-8" ), file="build/addons.xml.md5" )
		except Exception as e:
			# oops
			print("An error occurred creating addons.xml.md5 file!\n%s" % e)

	def _generate_downloader( self, addons ):
		repoPath = 'build/repo/'

		if(os.path.isdir(repoPath)):
			shutil.rmtree(repoPath)
		os.mkdir(repoPath)

		for addon in addons:
			add = xmltodict.parse(addons[addon])
			
			zipFolderPath = repoPath + add['addon']['@id'] + '/'
			zipFilePath = zipFolderPath + add['addon']['@id'] + '-' + add['addon']['@version'] + '.zip'

			os.mkdir(zipFolderPath)
			
			# download github repo
			filedata = urlopen('https://github.com/' + addon +'/archive/master.zip')
			datatowrite = filedata.read()
			with open(zipFilePath, 'wb') as f:
				f.write(datatowrite)

			# extract
			folderRoot = ''
			with zipfile.ZipFile(zipFilePath, 'r') as zip_ref:
				folderRoot = zip_ref.namelist()[0]
				zip_ref.extractall(zipFolderPath)
				zip_ref.close()
			
			# rename root Folder
			os.rename(zipFolderPath + folderRoot, zipFolderPath + add['addon']['@id']) # + '-' + add['addon']['@version'])

			#zip
			self._zipdir(zipFolderPath + add['addon']['@id'], add['addon']['@id'] + '-' + add['addon']['@version'] + '.zip')
			shutil.rmtree(zipFolderPath + add['addon']['@id'])

	def _zipdir(self, folder, filename):
		rootDir = '/'.join(folder.split('/')[:-1])
		zipf = zipfile.ZipFile(rootDir + '/' + filename, 'w', zipfile.ZIP_DEFLATED)
		for root, dirs, files in os.walk(folder):
			for file in files:
				path = root + '/' + file
				zipf.write(path, path.replace(rootDir, ''))
		zipf.close()

	def _save_file( self, data, file ):
		try:
			# write data to the file (use b for Python 3)
			open( file, "wb" ).write( data )
		except Exception as e:
			# oops
			print("An error occurred saving %s file!\n%s" % ( file, e ))


class GeneratorAddonRepo:

	TEMPLATE='addon-repo/repo.xml.j2'
	ICON='addon-repo/icon.png'

	def __init__( self, githubRepo ):

		self.githubUser = githubRepo.split('/')[0]
		self.githubRepo = githubRepo.split('/')[1]

		self.render()

	def render( self ):
		env = Environment(loader=FileSystemLoader('.'))
		template = env.get_template(GeneratorAddonRepo.TEMPLATE)
		output_from_parsed_template = template.render(repo=self.githubRepo, user = self.githubUser)

		tempDir = 'repository.' + self.githubUser

		#clean temp dir
		if(os.path.isdir(tempDir)):
			shutil.rmtree(tempDir)
		os.mkdir(tempDir)

		# to save the results
		with open(tempDir + "/addon.xml", "w") as fh:
			fh.write(output_from_parsed_template)

		shutil.copy(GeneratorAddonRepo.ICON, tempDir + '/icon.png')

		zipf = zipfile.ZipFile('build/repository.' + self.githubUser + '.zip', 'w', zipfile.ZIP_DEFLATED)
		zipf.write(tempDir + "/addon.xml")
		zipf.write(tempDir + "/icon.png")
		zipf.close()

		shutil.rmtree(tempDir)


if ( __name__ == "__main__" ):
	if len(sys.argv) == 1:
		print("no github repo in arg. Just regenerate addons.xml")
		Generator()
	else:
		Generator()
		GeneratorAddonRepo(sys.argv[1])