import sys, base64;

f = open(sys.argv[1], "rb");
s = f.read().splitlines();
f.close();

f = open(sys.argv[1] + ".b64", "wb");
for line in s:
	f.write(base64.b64encode(line.strip()) + "\n");
f.close();
