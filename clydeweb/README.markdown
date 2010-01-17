Clyde - Sometimes you can't hack
================================

Clyde is a barebones web app to make editing & creating posts using Hyde.

## Requirements

1. [Facebook Tornado](http://github.com/facebook/tornado) - This now exists as a git submodule in the lib directory. You can init and setup right from the lib directory.
2. A branch for drafts and a branch for production for each of the hyde sites you
want to maintain with Clyde.

## Setup

Right now the only thing that you need to do is to modify sites.yaml in the root directory.

## Run Clyde

You can start clyde by simply executing `python clyde.py` from the hyde directory.
                                                     
-----------------------------------------------------

## Next Steps

1. Create commands(sets) for `markitup` editor for Hyde specific commands
2. Add client side scripts for better file detection and `markitup` initialization
3. Allow generating the site for preview
4. The site right now is unresponsive - No feedback, no indicators and no error messages.
5. Allow uploading and replacing media files










