#!/usr/bin/env python

#
# Get Blogger Linked Images
# Python 3
#
# Iterates over all posts on a Blogspot blog.
# Within each post, looks for images that are
# links to another image. Downloads the targeted link image.
# Attempts to continue following any links
# that are actually HTML pages containing another image.
#
# Uses the Blogger JSON API.
# Requires an API key, obtainable for free from Google.

# Usage: get_blogger_linked_images.py http://myblog.blogspot.com <API Key>
#        prints the list of linked image URLs to the console
#
#        get_blogger_linked_images.py http://myblog.blogspot.com <API Key> <Destination Directory>
#        downloads the linked images to the destination directory
#     
# Written by James Alan Preiss
# October 2012
#

import urllib.request
import json
from html.parser import HTMLParser
import os

API_URL_BASE = "https://www.googleapis.com/blogger/v3"

# downloads a HTTP GET request and parses to JSON
def call_json(url):
	response = urllib.request.urlopen(url)
	str_response = response.readall().decode('utf8', 'ignore')
	return json.loads(str_response)

# gets the integer blog ID from the blog URL
def get_blog_id(url, api_key):
	url = API_URL_BASE + "/blogs/byurl?url={0}&key={1}".format(url, api_key)
	data = call_json(url)
	id_str = data["id"]
	return id_str

# gets all the posts for a blog (passed by integer ID).
# traverses the Blogger API's paginated results
# to get all posts. Returns an array of JSON objects.
def get_all_posts(blog_id, api_key):
	url = API_URL_BASE + "/blogs/{0}/posts?key={1}".format(blog_id, api_key)
	data = call_json(url)
	items = data["items"]
	has_more = True
	while has_more:
		try:
			token = data["nextPageToken"]
			url = API_URL_BASE + "/blogs/{0}/posts?key={1}&pageToken={2}".format(blog_id, api_key, token)
			data = call_json(url)
			items += data["items"]
		except KeyError:
			has_more = False
	return items

# utility
def is_image_filename(string):
	extensions = ["png", "gif", "jpg", "jpeg"]
	return [string.endswith(ext) for ext in extensions]

# finds all values with a given key
# in an interable [(key, value), (key, value), ...]
def find_key(list_kvpairs, search):
	return [value for key, value in list_kvpairs if key == search]

# HTML Parser to find all images in a page
class ImageSearcher(HTMLParser):
	def __init__(self):
		super(ImageSearcher, self).__init__()
		self.image_sources = []
	def handle_starttag(self, tag, attrs):
		if tag == 'img':
			src = find_key(attrs, "src")
			self.image_sources.append(src[0])

# utility function to find the <img> sources in a page
def images_in_html(html_bytes):
	parser = ImageSearcher()
	encoded = html_bytes.decode('utf8', 'ignore')
	parser.feed(encoded)
	return parser.image_sources

# HTML parser to find all images that link to another image
# Output is the URLs of the images that are linked to
# <a href="image.jpg"><img src="..."/></a>
# i.e. above, the output would be ["image.jpg"]
# Output is available in self.images after calling self.feed(data)
# This implementation is not robust!
# It would also find an image inside a div, list, etc...
class ImageLinkSearcher(HTMLParser):
	def __init__(self):
		super(ImageLinkSearcher, self).__init__()
		self.linkstack = []
		self.images = []
	def handle_starttag(self, tag, attrs):
		if tag == 'a':
			hrefs = find_key(attrs, "href")
			if hrefs:
				self.linkstack.append(hrefs[0])
		if tag == 'img':
			if self.linkstack:
				link = self.linkstack[-1]
				if is_image_filename(link):
					self.images.append(link)
	def handle_endtag(self, tag):
		if tag == 'a':
			self.linkstack.pop()

# utility function to use ImageLinkSearcher, descirbed above
def find_link_images(html):
	parser = ImageLinkSearcher()
	parser.feed(html)
	return parser.images

# flattens a list of iterables one level
def flatten_once(iterable_of_iterables):
	for iterable in iterable_of_iterables:
		for item in iterable:
			yield item

# follows image links that are actually HTML
# with another image embedded
def follow_image_embeds(url):
	response = urllib.request.urlopen(url)
	content_type = response.info()["Content-Type"]
	if content_type.startswith("image"):
		return url
	else:
		html = response.read()
		return images_in_html(html)[0]

# main funciton - see file description
def linked_image_urls(blog_url, api_key):
	blog_id = get_blog_id(blog_url, api_key)
	posts = get_all_posts(blog_id, api_key)
	contents = (post["content"] for post in posts)
	lists_of_links = (find_link_images(post) for post in contents)
	all_links = flatten_once(lists_of_links)
	return (follow_image_embeds(link) for link in all_links)

# downloads the resource at a URL to the directory,
# using the resource's name as the filename.
# returns the number of bytes downloaded.
def download_url_to_directory(url, directory):
	response = urllib.request.urlopen(url)
	data = response.read()
	firstslash = url.rfind('/')
	name = url[(firstslash + 1):]
	outpath = os.path.join(directory, name)
	outfile = open(outpath, 'wb')
	outfile.write(data)
	outfile.close()
	return len(data)

def prettyprint_size(num_bytes):
	units = ["bytes", "Kb", "Mb", "Gb"]
	factor = 1
	for unit in units:
		if num_bytes / factor < 1000:
			return "{0:.2f} {1}".format(num_bytes/factor, unit)
		factor *= 1000
	unit = "Tb"
	return "{0:.2f} {1}".format(num_bytes/factor, unit)

# see command line argument descriptions at top of file
def main():
	import sys
	blog_url = sys.argv[1]
	api_key = sys.argv[2]

	image_links = linked_image_urls(blog_url, api_key)

	if len(sys.argv) > 3:
		destination = sys.argv[3]
		if not os.path.isdir(destination):
			os.makedirs(destination)
		for url in image_links:
			size = download_url_to_directory(url, destination)
			print(url, ":", prettyprint_size(size))
	else:
		for url in image_links:
			print(url)


if __name__ == "__main__":
	main()
