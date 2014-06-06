import os, sys, json;


def bytes_to_label(size):
	labels = ['b', 'kb', 'mb', 'gb'];
	label_id = len(labels) - 1;
	for i in range(len(labels)):
		if (size < (1024 ** (i + 1))):
			label_id = i;
			break;

	return str(round(size / (1024 ** label_id) * 100.0) / 100.0) + labels[label_id];


f = open("all.json", "rb");
data = json.load(f);
f.close();


dl_servers = {};


for series in data:
	for entry in series["entries"]:
		if (entry["server"] in dl_servers):
			dl_servers[entry["server"]] += entry["size"];
		else:
			dl_servers[entry["server"]] = entry["size"];


dl_servers_list = [];
for server,size in dl_servers.items():
	dl_servers_list.append((server, size));
dl_servers_list.sort(key = lambda x: x[0]);



for i in range(len(dl_servers_list)):
	sys.stdout.write("Server {0:s} content: {1:s}\n".format(dl_servers_list[i][0], bytes_to_label(dl_servers_list[i][1])));


