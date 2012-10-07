get-blogspot-linked-images
==========================

Tries to download the full-size images linked from posts in a Blogger site.
Uses the Blogger JSON API.
Requires an API key, obtainable for free from Google.

Usage
-----

    get_blogger_linked_images.py http://myblog.blogspot.com <API Key>
prints the list of linked image URLs to the console.

    get_blogger_linked_images.py http://myblog.blogspot.com <API Key> <Destination Directory>
downloads the linked images to the destination directory.
       

Details
-------

Iterates over all posts on a Blogspot blog.
Within each post, looks for images that are links to another image. Downloads the targeted link image.
Blogspot spoofs some image links and serves an HTML page that contains another image.
In this case, the script will attempt to follow and list the desired, real image.


Author
------
    
Written by James Alan Preiss.
October 2012
