#! /usr/bin/env python
# Usage: python dlc.py
# V1.0
# Requests a series to download and then downloads
# /mt/Status on the server
# Resources:
#  http://a.pomf.se/lvokcf.zip # XML files for download ids
#  http://a.pomf.se/ynvroo.zip # json data of XML files
#  http://a.pomf.se/cpvaki.zip # json data of XML files, lite edition
import os, re, sys, json, time, base64, ctypes, threading;
try:
	# 2.x
	py_input = raw_input;
	import Queue as queue;
	import thread;
	import urllib2 as urllib;
	urllib_Request = urllib.Request;
	urllib_urlopen = urllib.urlopen;
	py_v = 2;
except:
	# 3.x
	py_input = input;
	import queue;
	import _thread as thread;
	import urllib, urllib.request;
	urllib_Request = urllib.request.Request;
	urllib_urlopen = urllib.request.urlopen;
	py_v = 3;



# Info
class Info:
	@classmethod
	def set_title(cls, title):
		try:
			# Set the window title
			ctypes.windll.kernel32.SetConsoleTitleA(title.encode("utf-8"));
		except:
			# Not Windows
			pass;



# Downloader class
class Download:
	# Vars
	__url_user_agent = "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11";
	__url_request = base64.b64decode(b"aHR0cDovLzE0Ni4xODUuMTM3LjE5NS9tdC9Eb3dubG9hZFJhbmRvbVNlcmllcw==").decode("latin-1");
	__url_success = base64.b64decode(b"aHR0cDovLzE0Ni4xODUuMTM3LjE5NS9tdC9SZXBvcnRTdWNjZXNzLw==").decode("latin-1");
	__url_download = base64.b64decode(b"aHR0cDovL3d3dy5tYW5nYXRyYWRlcnMuY29tL2Rvd25sb2FkL2ZpbGUvezA6ZH0=").decode("latin-1");
	__url_cookie = base64.b64decode(b"UEhQU0VTU0lEPTNhNjA2OTM1YzY3NjFhMWJiYmYzYTllMzJiOTZkZjIwOyBTTUZDb29raWUyMzI9YSUzQTQlM0ElN0JpJTNBMCUzQnMlM0E2JTNBJTIyOTE2MTk1JTIyJTNCaSUzQTElM0JzJTNBNDAlM0ElMjIwODg5YzI0YzM1ZDZhMzAyODExOGFhZGM5Y2IzMDE3YzczNjA0OTliJTIyJTNCaSUzQTIlM0JpJTNBMTQwMTkyMzE3MSUzQmklM0EzJTNCaSUzQTAlM0IlN0Q7IG10LTIwMDgtMDEtMTM9MjA3MDU2MDJmZmZkNTE3MzJiNTk4NzMwYzk2OWYzYzE7IHBvcHVuZGVyPXllczsgcG9wdW5kcj15ZXM7IHNldG92ZXIxOD0x").decode("latin-1");

	__header_ua = "User-Agent";
	__header_cookie = "Cookie";
	__header_len = "Content-Length";
	__header_cd = "Content-Disposition";
	__re_cd_name = re.compile(r'filename="(.*)"', re.DOTALL);
	__re_remove_url_non_name = re.compile(r"([\?\#].*)?$", re.DOTALL);



	# Constructor
	def __init__(self):
		self.url = "";
		self.url_final = "";
		self.url_name = "";
		self.status = 0;
		self.response = None;
		self.cancel = False;



	# Request a download
	def request(self, url, headers={}, cb_progress=None):
		# Open request
		self.cancel = False;
		headers[self.__header_ua] = self.__url_user_agent;
		url_request = urllib_Request(url, headers=headers);
		self.response = urllib_urlopen(url_request);

		# Read headers
		info = self.response.info();
		bytes_total = int(info[self.__header_len], 10);
		bytes_complete = 0;
		chunk_size = 1024 * 50; # 50k
		chunks = [];

		# Read
		while (not self.cancel):
			# Get a chunk
			chunk = self.response.read(chunk_size);

			# Done
			if (len(chunk) == 0): break;

			# Update
			chunks.append(chunk);
			bytes_complete += len(chunk);

			# Callback
			if (cb_progress is not None):
				cb_progress(bytes_complete, len(chunk), bytes_total);



		# Done
		self.response.close();

		# Info
		self.status = self.response.getcode();
		self.url_final = self.response.geturl();
		self.url_name = os.path.split(self.__re_remove_url_non_name.sub("", self.url_final))[1];
		if (len(self.url_name) == 0):
			self.url_name = os.path.split(self.__re_remove_url_non_name.sub("", url))[1];
		if (self.__header_cd in info):
			content_disposition = info[self.__header_cd];
			match = self.__re_cd_name.search(content_disposition);
			if (match is not None):
				self.url_name = match.group(1);



		# Return chunks
		return chunks;



	# Download a release
	def download(self, download_id, cb_progress=None):
		# Open request
		url = self.__url_download.format(download_id);
		headers = {};
		headers[self.__header_cookie] = self.__url_cookie;

		return self.request(url, headers, cb_progress);



# Archive helper data
class Archive:
	__zip = ".zip";
	__rar = ".rar";
	__headers = {};
	__headers[__zip] = "\x50\x4b\x03\x04";
	__headers[__rar] = "\x52\x61\x72\x21\x1A\x07\x00";

	@classmethod
	def get_type(cls, bytes_data):
		t = cls.__zip;
		if (bytes_data[:len(cls.__headers[t])] == cls.__headers[t]): return t;

		t = cls.__rar;
		if (bytes_data[:len(cls.__headers[t])] == cls.__headers[t]): return t;

		return None;



# String label class
class Label:
	__labels = ['b', 'kb', 'mb', 'gb'];

	# Convert a byte label string into bytes
	@classmethod
	def from_byte_count(cls, size):
		label_id = len(cls.__labels) - 1;
		for i in range(len(cls.__labels)):
			if (size < (1024 ** (i + 1))):
				label_id = i;
				break;

		return "{0:.2f}{1:s}".format((round(size / (1024 ** label_id) * 100.0) / 100.0), cls.__labels[label_id]);



# Directories
class Path:
	__re_punct = re.compile(r"[^a-zA-Z0-9\!\@\#\$\%\^\&\(\)\_\+\-\=\`\~\[\]\{\}\;\'\,\. ]");

	script_dir = os.path.dirname(os.path.realpath(__file__));



	@classmethod
	def normalize_name(cls, text):
		return cls.__re_punct.sub("", text);



# Download thread
class DownloadThreadManager(threading.Thread):
	# Constructor
	def __init__(self, series_list, base_title):
		threading.Thread.__init__(self);
		self.tasks = queue.Queue();
		self.downloaders = [];
		self.series_list = series_list;
		self.series_total_count = len(self.series_list);
		self.base_title = base_title;
		self.complete = False;
		self.stop_status = "";

	# Add a task
	def add_task(self, *args):
		self.tasks.put(tuple(args));

	# Stop execution
	def stop(self):
		# Cancel the download
		self.tasks.put(( "stop" , ));
		for i in range(len(self.downloaders)):
			self.downloaders[i].stop();

	# Create downloaders
	def create_downloaders(self, count):
		for i in range(count):
			dlt = DownloadThread(len(self.downloaders), self);
			dlt.start();
			self.downloaders.append(dlt);
			self.add_task("start", dlt);

	# Stop functions
	def stop_after_current_series(self):
		self.stop_status = "after_series";
	def stop_after_current_downloads(self):
		self.stop_status = "after_downloads";

	# Join all threads
	def join_threads(self):
		for i in range(len(self.downloaders)):
			self.downloaders[i].join();
		self.join();

	# Update title
	def update_title(self):
		# Get download activity
		active_list = [];
		for i in range(len(self.downloaders)):
			if (self.downloaders[i].server is not None):
				active_list.append(( self.downloaders[i].server , "{0:s}: {1:.0f}%".format(self.downloaders[i].server, (self.downloaders[i].bytes_complete / max(1, self.downloaders[i].bytes_total)) * 100)));

		# Nothing
		if (len(active_list) == 0):
			title_str = "No active downloads";
		else:
			active_list.sort(key=lambda x: x[0]);
			title_str = " | ".join([ i[1] for i in active_list ]);

		# Apply
		title_str = "{0:s} [{1:s}]".format(self.base_title, title_str);
		Info.set_title(title_str);

	def print_info(self, series, download_data, series_count, series_id, series_dl_id):
		sys.stdout.write("    Downloading {0:d} of {1:d} ({2:s} on {3:s}): {4:s}\n".format(series_dl_id, series_count, Label.from_byte_count(download_data["size"]), download_data["server"], download_data["name"]));
		sys.stdout.flush();

	def print_series_start(self, series, series_count, series_id):
		total_series_size = 0;
		for server, entries in series["entries"].items():
			for entry in entries:
				total_series_size += entry["size"];

		sys.stdout.write("Downloading {0:d} of {1:d} ({2:s}): {3:s}\n".format(series_id, self.series_total_count, Label.from_byte_count(total_series_size), series["name"]));
		sys.stdout.flush();

	def print_series_completion(self, series, series_count, series_id):
		sys.stdout.write("\n");
		sys.stdout.flush();

	def print_completion(self):
		sys.stdout.write("All series downloaded\n");
		sys.stdout.flush();

	def get_series_size(self, series):
		count = 0;
		for server, entries in series["entries"].items():
			count += len(entries);
		return count;

	# Get a series to download
	def __get_series_to_download(self, series):
		# Get active servers
		active_servers = {};
		for i in range(len(self.downloaders)):
			if (self.downloaders[i].server is not None):
				active_servers[self.downloaders[i].server] = True;

		# Search for a series entry that can be downloaded
		download_data = None;
		for server, entries in series["entries"].items():
			if (server in active_servers):
				continue; # Server is already active
			if (len(entries) > 0):
				download_data = entries.pop(0);
				break;

		# Done
		return download_data;

	# Thread execution
	def run(self):
		# Start loading series
		series = self.series_list[0];
		series_count = self.get_series_size(series);
		series_id = 1;
		series_dl_id = 0;
		self.print_series_start(series, series_count, series_id);

		# Loop
		while (not self.complete):
			# Wait for a task
			task = self.tasks.get();

			# Task type
			if (task[0] == "stop"):
				# Done
				break;
			elif (task[0] == "progress"):
				# Download progress
				self.update_title();
			elif (task[0] == "complete" or task[0] == "start"):
				# Download complete
				if (len(self.series_list) > 0):
					while (True):
						# Find active
						active = 0;
						for i in range(len(self.downloaders)):
							if (self.downloaders[i].server is not None):
								active += 1;
							else:
								if (self.stop_status != "after_downloads"):
									download_data = self.__get_series_to_download(series);
								else:
									download_data = None;
								if (download_data is not None):
									# Begin download
									active += 1;
									series_dl_id += 1;
									self.downloaders[i].give_request(download_data, series);

									# Info
									self.print_info(series, download_data, series_count, series_id, series_dl_id);

						# Nothing to be done, and nothing being done
						if (active == 0):
							# Series is complete
							self.print_series_completion(series, series_count, series_id);
							self.series_list.pop(0);
							if (len(self.series_list) == 0 or self.stop_status != ""):
								# Everything is complete
								self.print_completion();
								self.complete = True;
								thread.interrupt_main();
								break;
							else:
								# Next series
								series = self.series_list[0];
								series_count = self.get_series_size(series);
								series_id += 1;
								series_dl_id = 0;
								self.print_series_start(series, series_count, series_id);
						else:
							# Something is being done
							break;

				# Update title
				self.update_title();


		# Done
		return 0;

class DownloadThread(threading.Thread):
	# Constructor
	def __init__(self, id, manager):
		threading.Thread.__init__(self);

		self.executing = True;

		self.tasks = queue.Queue();
		self.download = Download();
		self.manager = manager;

		self.bytes_complete = 0;
		self.bytes_in_last_update = 0;
		self.bytes_total = 0;

		self.id = id;
		self.server = None;
		self.active = False;

	# Download progress update
	def __update_progress(self, bytes_complete, bytes_in_last_update, bytes_total):
		self.bytes_complete = bytes_complete;
		self.bytes_in_last_update = bytes_in_last_update;
		self.bytes_total = bytes_total;

		# New task
		self.manager.add_task("progress", self);


	# Thread execution
	def run(self):
		# Loop
		while (self.executing):
			# Wait for a task
			task = self.tasks.get();
			if (not self.executing): break; # End

			# Check task
			if (task[0] == "download"):
				# Download
				file_name_dir = os.path.join(Path.script_dir, "dls");
				file_name_dir = os.path.join(file_name_dir, Path.normalize_name(task[2]["name"]));
				file_name_base = Path.normalize_name(task[1]["name"]);
				if (
					os.path.exists(os.path.join(file_name_dir, file_name_base + ".zip")) or
					os.path.exists(os.path.join(file_name_dir, file_name_base + ".rar"))
				):
					# File is already done
					pass;
				else:
					# Download
					self.server = task[1]["server"];
					self.bytes_complete = 0;
					self.bytes_in_last_update = 0;
					self.bytes_total = 0;
					chunks = self.download.download(task[1]["id"], cb_progress=(lambda bc, bl, bt: self.__update_progress(bc, bl, bt)));

					if (chunks is not None and not self.download.cancel):
						file_name_ext = os.path.splitext(self.download.url_name)[1].lower();
						file_name = os.path.join(file_name_dir, file_name_base + file_name_ext);

						# Output
						try:
							os.makedirs(file_name_dir);
						except:
							pass;
						f = open(file_name, "wb");
						for chunk in chunks:
							f.write(chunk);
						f.close();


				# Signal done event
				self.server = None;
				self.manager.add_task("complete", self);

		# Done
		return 0;

	# Give a download request
	def give_request(self, download_data, series):
		"""
			cb_progress called as
				cb_progress(ytes_complete, bytes_in_last_update, bytes_total);
			cb_done called as:
				cb_done(download_instance, returned_chunks);
		"""
		# Set task
		self.server = download_data["server"];
		self.tasks.put(( "download" , download_data , series ));

	# Stop any downloads and the thread
	def stop(self):
		# Cancel the download
		self.download.cancel = True;
		self.executing = False;
		self.tasks.put(( "stop" , ));



# Main
def main():
	# Set title
	base_title = "Manga Traders Downloader"
	Info.set_title(base_title);



	# Load json
	f = open("all.json", "rb");
	json_source = f.read();
	json_data = json.loads(json_source.decode("latin-1"));
	json_source = None;
	f.close();

	# Sort based on servers
	server_counts = {};
	json_data_sorted_server = [];
	for series in json_data:
		# Collect data
		entries_servers = {};
		for entry in series["entries"]:
			# Ensure server exists
			if (entry["server"] not in entries_servers):
				entries_servers[entry["server"]] = [];
			if (entry["server"] not in server_counts):
				server_counts[entry["server"]] = 1;
			else:
				server_counts[entry["server"]] += 1;

			# Copy
			entries_servers[entry["server"]].append(entry);

		# Update data
		json_data_sorted_server.append({
			"id": series["id"],
			"name": series["name"],
			"entries": entries_servers,
		});

		# Clear
		entries_servers = None;




	# Vars
	server_count_str = None;
	download_filter_str = None;

	# Number of servers to connect to
	if (server_count_str is None):
		sys.stdout.write("Enter the number of servers you want to connect to? (1 - {0:d})\n".format(len(server_counts.keys())));
		server_count_str = py_input("> ");
		sys.stdout.write("\n");
	server_count_str = server_count_str.strip();
	try:
		server_count = int(server_count_str, 10);
	except ValueError:
		server_count = 1;
	server_count = max(1, min(len(server_counts.keys()), server_count));

	# Method of downloading
	if (download_filter_str is None):
		sys.stdout.write("Enter the download filter you want to use:\n");
		sys.stdout.write('    "A" for first series starting with the letter A\n');
		sys.stdout.write('    "A-C" for first series starting with the letter A through C\n');
		sys.stdout.write('    "0" for anything starting with a number 0\n');
		sys.stdout.write('    "0-9" for anything starting with any number\n');
		sys.stdout.write('    "*" for anything else (things starting with symbols)\n');
		sys.stdout.write('    "all" for everything\n');
		sys.stdout.write('    "server" for requesting series to download from the server\n');
		download_filter_str = py_input("> ");
		sys.stdout.write("\n");
	download_filter_str = download_filter_str.strip().lower();

	# Server or local
	from_server = (download_filter_str == "server");
	if (from_server):
		# Not ready yet
		sys.stderr.write("Not implemented\n");
		return -1;
	else:
		# Filter method regex
		re_filter_method = re.compile(r"^([a-z])\s*-\s*([a-z])|([0-9])\s*-\s*([0-9])|([a-z0-9])|(\*)|(all)$");
		match = re_filter_method.match(download_filter_str);
		if (match is None):
			sys.stderr.write("Invalid download filter\n");
			return -1;

		# Filter method
		if (match.group(1) is not None):
			# Letter range
			download_filter = ( "range" , ord(match.group(1)) , ord(match.group(2)) );
		elif (match.group(3) is not None):
			# Number range
			download_filter = ( "range" , ord(match.group(3)) , ord(match.group(4)) );
		elif (match.group(5) is not None):
			# Single number or letter
			download_filter = ( "range" , ord(match.group(5)) , ord(match.group(5)) );
		elif (match.group(6) is not None):
			# Symbols
			download_filter = ( "symbols" , 0 , 0 );
		else:
			# Everything
			download_filter = ( "all" , 0 , 255 );
		download_filter = ( download_filter[0] , min(download_filter[1], download_filter[2]) , max(download_filter[1], download_filter[2]) );



	# Filter download targets
	filtered_series = [];
	re_symbol = re.compile(r"^[^a-zA-Z0-9]");
	for series in json_data_sorted_server:
		series_name = series["name"].strip().lower();
		add = False;
		if (download_filter[0] == "all"):
			add = True;
		elif (download_filter[0] == "range"):
			c = ord(series_name[0]);
			add = (c >= download_filter[1] and c <= download_filter[2]);
		elif (download_filter[0] == "symbols"):
			add = (re_symbol.search(series_name[0]) is not None);

		if (add):
			filtered_series.append(series);

	#filtered_series = [ json_data_sorted_server[0] ]; # For debugging


	# Start
	sys.stdout.write("Starting downloads of {0:d} series\n".format(len(filtered_series)));
	sys.stdout.write("    (CTRL+C to stop)\n");



	# Manager
	dtm = DownloadThreadManager(filtered_series, base_title);
	dtm.start();
	dtm.create_downloaders(server_count);

	# Manage command line through CTRL+C stuff
	ctrl_c_count = 0;
	while (True):
		try:
			time.sleep(24 * 60 * 60); # Wait a day
		except KeyboardInterrupt:
			# Complete
			if (dtm.complete): break;

			# Stop
			ctrl_c_count += 1;
			if (ctrl_c_count == 1):
				# Stop after current series
				sys.stdout.write("Downloads will stop after the current series has completed\n");
				sys.stdout.write("    (CTRL+C 2 more times to stop)\n");
				sys.stdout.flush();
				dtm.stop_after_current_series();
			elif (ctrl_c_count == 2):
				# Stop after current files
				sys.stdout.write("Downloads will stop after the current downloads have completed\n");
				sys.stdout.write("    (CTRL+C 1 more time to stop)\n");
				sys.stdout.flush();
				dtm.stop_after_current_downloads();
			else: # if (ctrl_c_count >= 3):
				sys.stdout.write("Stopping\n");
				sys.stdout.flush();
				dtm.stop();
				break;



	# Done
	dtm.stop();
	dtm.join_threads();
	return 0;



# Execute
if (__name__ == "__main__"): sys.exit(main());

# Ctrl+C: Stop downloading after series has completed
# x2: Stop downloading after release has completed
# x3: now