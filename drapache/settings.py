#### Settings for Drapache
import drapache

### Degbu
DEBUG = True

### Dropbox Connection

# Your app key from developers.dropbox.com
DROPBOX_APP_KEY = ''

# Your app secret from developers.dropbox.com
DROPBOX_APP_SECRET = ''


### DROPBOX RESOLVING
### How to get OAUTH info for a given request. There are two resolvers built in
### they are SimpleResolver and SubdomainResolver
### SubdomainResolver requires more configuration as it needs a storage

## SimpleResolver settings:

# The OAUTH token
OAUTH_TOKEN = ''

# The OAUTH token secret
OAUTH_TOKEN_SECRET = ''


## SubdomainResolver settings:
## There are two backends built in for the SubdomainResolver,
## One using FlatFiles and the other using MySql.

# FlatFile just needs a location for the file
SUBDOMAIN_FLATFILE_FILENAME = ''

# Mysql needs a dictionary with HOST, USER, PASS, DB
SUBDOMAIN_MYSQL_PARAMS = {
                            'HOST' : '',
                            'USER' : '',
                            'PASS' : '',
                            'DB'   : ''
}
# and picking the Backend
SUBDOMAIN_RESOLVER_BACKEND = drapche.core.resolvers.subdomain.FlatFileSubdomainBackend


## Picking the actual resolver class!
DROPBOX_RESOLVER = drapache.core.resolvers.SimpleResolver


### DROPBOX PROXY SETTINGS
### These settings control how the proxy goes about going about
### handling requests to dropbox

# Set to False to allow paths with an underscore in them
HIDE_UNDERSCORES = True

# Set to True to show a 410 instead of a regular 404 in case of deleted file
REPORT_DELETED = False

# The tuple of installed Path Handlers
# The order matters - as the first handler
# to state that it can handle a path will be used
PATH_HANDLERS = (
                    #handles directory and indexes
                    drapache.core.pathhandlers.DirectoryHandler,
                    
                    #handles executing DBPY files
                    drapache.core.pathhandlers.DBPYHandler,
                    
                    #uncomment this line to add markdown rendering
                    #drapache.core.pathhandlers.MarkdownHandler,
                    
                    #handles the rest - serves as a static file
                    drapache.core.pathhandlers.StaticHandler,
)



### Ok now we need some path handler specific settings

## Directory Handler

# set the prefixes that should be combined with
# indexes to be automatically returned in a directory
INDEX_PREFIXES = (
                    'index',
)

# extensions that will be looked.
# it looks in the order
INDEX_EXTENSIONS = (
                    'dbpy',
                    'html',
                    'txt',
)



## DBPY Settings

# how long to let a DBPY script run
DBPY_TIMEOUT = 25

# the maximum amount of threads a script can spawn
DBPY_BACKGROUND_THREAD_LIMIT = 10

# whether to print exceptions or not
DBPY_PRINT_EXCEPTIONS = True

# debug?
DBPY_DEBUG = True