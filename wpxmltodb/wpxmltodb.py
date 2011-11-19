#!/usr/bin/python
# encoding: utf-8

"""
Copyright (C) 2007 Brazil, Inc. All rights reserved.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License, version 2,
as published by the Free Software Foundation.

You should have received a copy of the GNU General Public License
along with this file.  If not, write to the Free Software Foundation,
59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
"""

# Change True if debugging this script
DEBUG = False

import xml.sax as sax
import time
from datetime import datetime
from xml.sax.handler import ContentHandler
from sgmllib import SGMLParser
import htmlentitydefs
import sys

def printlog(str, debug = False):
  if debug and not DEBUG: return
  print >> sys.stderr, str

class DBRecorder:
  ci = {}      # connection infomation
  con = None   # connection
  cur = None   # cursor
  table = None # table name

  def __init__(self, db, table, host, port, user, password):
    # TODO: fix db name
    if db:
      self.ci['db'] = db
    else:
      self.ci['db'] = 'wikipedia_ja'

    # TODO: fix table name
    if table:
      self.table = table
    else:
      self.table = 'articles_test'

    if host:
      self.ci['host'] = host
    else:
      self.ci['host'] = 'localhost'

    if port: self.ci['port'] = port
    if user: self.ci['user'] = user
    if password: self.ci['passwd'] = password

  def insert(self, id, title, body, mdate, size):
    try:
      self.cur.execute("insert into %s (title, body, mdate, size) VALUES (%%s, %%s, %%s, 0)" % self.table,
                       (title, body, mdate))
    except:
      printlog('* insert error occur !\ntitle:%s\nbody:%s...\nmdate:%s\nsize:%d' %
               (title, body[:32], mdate, size))
      printlog(sys.exc_info()[0])

class MySQLRecorder(DBRecorder):
  def __init__(self, db, table, host, port, user, password):
    import MySQLdb
    DBRecorder.__init__(self, db, table, host, port, user, password)
    self.ci['charset'] = 'utf8'

    self.con = MySQLdb.connect(**self.ci)
    self.cur = self.con.cursor()

    self.cur.execute('SET NAMES utf8')
  def truncate(self):
    # delete and create table
    self.cur.execute('drop table if exists %s' % self.table)
    self.cur.execute("""create table %s (
                          id     int unsigned auto_increment not null, PRIMARY KEY(id),
                          title  varchar(255) not null,
                          body   mediumtext,
                          mdate  datetime,
                          size   int unsigned not null,
                          FULLTEXT ft_title USING NGRAM (title),
                          FULLTEXT ft_body  USING NGRAM (body),
                          INDEX bt_mdate (mdate),
                          INDEX bt_size  (size)
                        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.table)

  def search_title(self, query):
    # TODO: implement !!
    print "Not supported..."

  def search_body(self, query):
    # TODO: implement !!
    print "Not supported..."

class PgRecorder(DBRecorder):
  def __init__(self, db, table, host, port, user, password):
    # TODO: implement !!
    pass

  def truncate(self):
    # TODO: implement !!
    pass

  def search_title(self, query):
    # TODO: implement !!
    print "Not supported..."

  def search_body(self, query):
    # TODO: implement !!
    print "Not supported..."

class TextRecorder:
  def __init__(self, db, table, host, port, user, password):
    # table, host, port, user, password are ignored
    if db:
      import codecs
      self.out = codecs.getwriter('utf-8')(file(db, 'wb'))
    else:
      self.out = sys.stdout

  def truncate(self):
    pass

  def insert(self, id, title, body, mdate, size):
    self.out.write('%s\t%s\t%s\t%d\n' % (title, body, mdate, size))

  def search_title(self, query):
    print "Not supported..."

  def search_title(self, query):
    print "Not supported..."

class SennaRecorder:
  import sennactx
  db = None
  client = None
  use_load = True

  def __init__(self, db, table, host, port, user, password):
    """ connect senna server and defines classes and slots.
    """
    if db:
      self.db = self.sennactx.Db.open(db)
      self.client = self.db.ctx_open(self.sennactx.CTX_USEQL)
    else:
      if not host:
        host = 'localhost'
      if not port:
        port = 10041
      self.client = self.sennactx.Context.connect(host, port,
                                                  self.sennactx.CTX_USEQL)
    if not self.client:
      printlog('cannot connect senna server !')
    if not table:
      table = 'Articles'
    self.table = table

  def truncate(self):
    table = self.table
    # TODO: drop db if exists
    # define document class
    if not self.db:
      self.db = self.sennactx.Db.create('wikipedia.db', 0, self.sennactx.ENC_UTF8)
      self.client = self.db.ctx_open(self.sennactx.CTX_USEQL)

    self.command("(<db> ::new '<%s>)" % table)
    self.command('(<%s> ::add :title <text>)' % table)
    self.command('(<%s> ::add :body <longtext>)' % table)
    self.command('(<%s> ::add :mdate <int>)' % table)
    self.command('(<%s> ::add :size <int>)' % table)
    # define term class
    self.command("(<db> ::new '<%s_Terms> :ngram :utf-8)" % table)
    self.command("(<%s_Terms> ::add :i_title <%s> :index '(title))" % (table, table))
    self.command("(<%s_Terms> ::add :i_body <%s> :index '(body))" % (table, table))
    if self.use_load:
      # load mode
      self.command('(<%s> ::load :title :body :mdate :size)' % table)

  def __del__(self):
    self.command('\n')
    self.client.close()
    if self.db:
      self.db.close()

  def command(self, sendbuf, flags = 0):
    rc = self.client.send(sendbuf.encode('utf-8'), flags)
    if rc:
      printlog('senna send error !')
      return ''

    buf = []
    for i in xrange(0, 100):
      (rc, recvbuf, flags) = self.client.recv()
      if rc:
        printlog('senna recv error !')
        return ''
      if recvbuf:
        buf.append(recvbuf.decode('utf-8'))
      if not (flags & self.sennactx.CTX_MORE):
        return buf
    printlog('senna recv: too many times !!!')

  def insert(self, id, title, body, mdate, size):
    """ Insert record to Senna
    """
    # FIXME: now senna cannot accept '\n', '\t'
    body_ = body.replace('\t', ' ').replace('\n', ' ')
    mepoch = int(time.mktime(time.strptime(mdate, '%Y-%m-%dT%H:%M:%SZ')))
    if self.use_load:
      self.command(u'%d\t%s\t%s\t%d\t%d' % (id, title, body_, mepoch, size))
    else:
      self.command(u'(<%s> ::new "%s" :title ? :body ? :mtime ? :size ?)' % (self.table, id))
      self.command(title)
      self.command(body_)
      self.command(str(mepoch))
      self.command(str(size))

  def search(self, slot, query):
    qstr = "(sen-output ((<%s_Terms> :%s) ::index-select ?) '(:title))" % (self.table, slot)
    rc = self.command(qstr)
    res = self.command(query)
    printlog("Hits : %s" % res.pop(0))
    for title in res:
      printlog(title)

  def search_title(self, query):
    self.search('i_title', query)

  def search_body(self, query):
    self.search('i_body', query)

class MWXMLHandler(ContentHandler):
  def __init__(self, rec):
    self.count = 0
    self.buf = u''

    # for siteinfo
    self.namespace_key = None
    self.namespaces = {}

    # for articles
    self.id = None
    self.title = None
    self.timestamp = None

    # for record
    self.rec = rec

    # internal mode
    self.in_revision = False

  def startElement(self, name, attrs):
    if name == 'namespace':
      self.namespace_key = attrs['key']
    elif name == 'revision':
      self.in_revision = True
    self.buf = ''

  def endElement(self, name):
    if name == 'text':
      if self.buf == None: return None
      # * check namespace of title
      if not (self.id and self.title): return
      nsi = self.title.find(':')

      if nsi != -1:
        ns = self.title[:nsi]
        if ns in self.namespaces:
          # TODO: search with specific namespace
          printlog('article with namespace')
          return
        title = self.title[nsi+1:]
      else:
        title = self.title

      printlog('* parse id: %d title: %s mdate: %s' %
               (self.id, self.title, self.timestamp))
      starttime = datetime.now()
      (i, out) = (None, None)
      if DEBUG:
        (i, out) = self.parse_mediawiki(self.buf, 0, len(self.buf))
      else:
        try:
          (i, out) = self.parse_mediawiki(self.buf, 0, len(self.buf))
        except:
          pass
      if i != -1:
        endtime = datetime.now()
        printlog('parse time: %s' % (endtime - starttime))
        self.rec.insert(self.id, title, out, self.timestamp, len(out))
      else:
        printlog('redirect')
    elif name == 'title':
      self.title = self.buf
    elif name == 'id':
      if not self.in_revision:
        try:
          self.id = int(self.buf)
        except ValueError:
          pass
    elif name == 'timestamp':
      self.timestamp = self.buf
#      try:
#        self.timestamp = datetime(*time.strptime(self.buf, '%Y-%m-%dT%H:%M:%SZ')[:6])
#      except ValueError:
#        printlog('cannot get timestamp')
    elif name == 'namespace':
      # lookup key from namespace string
      self.namespaces[self.buf] = int(self.namespace_key)
    elif name == 'revision':
      self.in_revision = False

    self.buf = None

  def characters(self, char):
    if self.buf == None: return
    self.buf += char

  def parse_template(self, text, i, ts):
  # TODO: support magic words http://meta.wikimedia.org/wiki/Help:Magic_words
  # TODO: support {{fullurl:}}
  # TODO: support {{#}}
    i += 2
    first = True
    obuf = u''
    while i < ts:
      (i, out) = self.parse_mediawiki(text, i, ts, 'intmpl')
      if first:
        # template name is chopped
        first = False
      else:
        obuf += out
      if i >= ts:
        printlog('* warning: template close is not found !!', True)
        break
      elif text[i:i+2] == '}}':
        obuf += '\n'
        i += 2
        break
      elif text[i] == '|':
        obuf += ' '
        i += 1
      else:
        obuf += '\n'
        printlog('* error: invalid template end !!')
        i += 1
    return (i, obuf)

  def parse_interlink(self, text, i, ts):
    image = False

    i += 2
    ne = text.find(':', i)
    if ne != -1:
      ns = text[i:ne]
      # check image namespace
      if ns.lower() == 'image' or self.namespaces.get(ns, 0) == 6:
        image = True

    # link text for image appeared last normally,
    # but some data regulated
    out = u''
    while i < ts:
      e = text.find('|', i)
      d = 1
      if e == -1:
        e = text.find(']]', i)
        d = 2
      if e == -1:
        printlog('delimiter of interlink cannot be found')
        break
      elm = text[i:e].strip()
      if image:
        if (elm in ('thumb', 'left', 'right', 'none', 'center', 'framed',
                    'baseline', 'sub', 'super',
                    'top', 'text-top', 'middle', 'bottom', 'text-bottom') or \
            elm[-2:] == 'px'):
          i = e + d
          continue
      (i, out) = self.parse_mediawiki(text, i, ts, 'inlink')
      if i >= ts:
        printlog('* warning: interlink close is not found !!', True)
        break
      elif text[i:i+2] == ']]':
        out += '\n'
        i += 2
        break
      elif text[i] == '|':
        out += ' '
        i += 1
      else:
        out += '\n'
        printlog('* error: invalid interlink end !!')
        i += 1
    return (i, out)

  def parse_outerlink(self, text, i, ts):
    e = text.find(']', i+1)
    if e == -1:
      printlog('* warning: outerlink close is not found !!', True)
      e = ts

    # find ' '
    p = text.rfind(' ', i+1, e)
    if p != -1:
      linktext = text[p:e]
    else:
      linktext = text[i+1:e]
    return (min(e + 1, ts), linktext)

  def parse_heading(self, text, i, ts):
    # TODO: handle heading on last line
    e = text.find('\n', i)
    if e != -1:
      return (e + 1, text[i:e].strip('= ') + '\n')
    else:
      # TODO: handle end
      printlog('* error: heading needs linefeed')
      return (i + 1, '=')

  def parse_mediawiki(self, text, i, ts, env = None):
    # * check redirect
    if text[:9] == '#redirect' or text[:9] == '#REDIRECT':
      # TODO: search with redirect title
      return (-1, 'redirect')

    # * parse wiki-formatted text
    out = u''
    mode = {'table': False, 'start': 0}
    while i < ts:
      if i == 0 or text[i-1] == '\n':
        prei = i
        if mode['table']:
          if text[i] == '|':
            i += 1
            if i < ts:
              if text[i] == '+':
                # title
                i += 1
                continue
              elif text[i] == '-':
                # new row
                out += '\n'
                # skip styles
                e = text.find('\n', i+1)
                if e == -1:
                  i += 1
                else:
                  i = e + 1
                continue
              elif text[i] == '}':
                mode['table'] = False
                i += 1
                continue
              else:
                # column
                mode['table'] = 'column'
                mode['start'] = len(out)
                continue
          elif text[i] == '!':
            # caption
            mode['table'] = 'caption'
            mode['start'] = len(out)
            i += 1
            continue
          elif text[i:i+2] == '{|':
            printlog('invalid table in table', True)
            i += 2
            continue
        if text[i] == '\n':
          while i < ts and text[i] == '\n':
            i += 1
          out += '\n'
        elif text[i:i+4] == '----':
          i += 4
        elif text[i] in ['*', '#', ':']:
          while i < ts and text[i] in ['*', '#', ':']:
            i += 1
        elif text[i] == ';':
          i += 1
          # TODO: handle ':'
        elif text[i] == '=':
          # TODO: use senna section
          (i, tmp) = self.parse_heading(text, i, ts)
          out += tmp
        elif text[i] == ' ':
          # pre
          e = text.find('\n', i)
          if e == -1:
            out += text[i:ts]
            i = ts
          else:
            out += text[i:e+1]
            i = e + 1
        # check linestart styles increment cursor
        if prei != i:
          continue
      c = text[i]

      # in link
      if env:
        if c == '|':
          break
        if text[i:i+2] == ']]' and env == 'inlink':
          break
        if text[i:i+2] == '}}' and env == 'intmpl':
          break

      # table separators
      if mode['table'] == 'caption':
        if c == '|':
          # style/content separator
          out = out[:mode['start']]
          i += 1
          continue
        elif text[i:i+2] == '!!':
          # caption separator
          out += ' '
          mode['start'] = len(out)
          i += 2
          continue
      elif mode['table'] == 'column':
        if c == '|':
          if c[i+1:i+2] == '|':
            # column separator
            out += ' '
            mode['start'] = len(out)
            i += 2
          else:
            # style/content separator
            out = out[:mode['start']]
            i += 1
          continue

      # table starter is normally appeared on linestart
      if text[i:i+2] == '{|':
        mode['table'] = True
        # skip styles
        e = text.find('\n', i+2)
        if e == -1:
          i += 2
        else:
          i = e + 1
      # anywhere
      elif text[i:i+3] == '~~~':
        i += 3
        while text[i] == '~':
          i += 1
      elif c == '[':
        if (i+1) < ts and text[i+1] == '[':
          (i, tmp) = self.parse_interlink(text, i, ts)
          out += tmp
        else:
          (i, tmp) = self.parse_outerlink(text, i, ts)
          out += tmp
      elif c == "'":
        if text[i:i+5] == "'''''":
          i += 5
        elif text[i:i+3] == "'''":
          i += 3
        elif text[i:i+2] == "''":
          i += 2
        else:
          out += "'"
          i += 1
      elif c == '{':
        if (i+1) < ts and text[i+1] == '{':
          (i, tmp) = self.parse_template(text, i, ts)
          out += tmp
        else:
          # raw '{'
          out += '{'
          i += 1
      elif c == '<':
        # html comment
        if text[i+1:i+4] == '!--':
          e = text.find('-->', i+4)
          if e != -1:
            i = e + 3
          else:
            printlog('* warning: cannot find comment close')
            out += '<'
            i += 1
          continue

        s = text.find('>', i+1, i+513) # limit
        if s == -1:
          printlog('* warning: cannot find >: %s' % text[i:i+16], True)
          out += '<'
          i += 1
          continue

        tag = text[i+1:s].strip('/ ').split(' ')[0].lower()
        # nowiki
        if tag == 'nowiki':
          e = text.find('</nowiki>', s+1)
          if e != -1:
            out += text[s+1:e].replace('\n', '')
            i = e + 9
          else:
            out += '<'
            i += 1
        # pre open
        elif tag == 'pre':
          e = text.find('</pre>', s+1)
          if e != -1:
            out += text[s+1:e]
            i = e + 6
          else:
            out += '<'
            i += 1
        # math is handled same as pre
        elif tag == 'math':
          e = text.find('</math>', s+1)
          if e != -1:
            out += text[s+1:e]
            i = e + 7
          else:
            out += '<'
            i += 1
        # html
        elif tag == 'html':
          e = text.find('</html>', s+1)
          if e != -1:
            out += text[s+1:e]
            i = e + 7
          else:
            out += '<'
            i += 1
        # TODO: gallery
        # TODO: onlyinclude/noinclude/includeonly
        # ref
        elif text[i+1:i+4] == 'ref':
          e = text.find('</ref>', s+1)
          if e != -1:
            out += text[s+1:e]
            i = e + 6
          else:
            out += '<'
            i += 1
        # other html tags or raw '<'
        else:
          # TODO: performance up
          # check if allowed
          if tag in ('b', 'del', 'i', 'ins', 'u', 'font','big', 'small', 'sub', 'sup',
                     'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'cite', 'code', 'em', 's',
                     'strike', 'strong', 'tt', 'var', 'div', 'center', 'blockquote',
                     'ol', 'ul', 'dl', 'table', 'caption', 'pre',
                     'ruby', 'rt' , 'rb' , 'rp', 'p', 'span', 'u',
                     'br', 'hr', 'li', 'dt', 'dd', 'td', 'th', 'tr'):
            # newline
            if tag in ('br', 'hr'):
              out += '\n'
          i = s + 1
      elif c == '&':
        if (i+1) >= ts:
          out += '&'
          i += 1
        else:
          e = text.find(';', i+1, i+17) # limit
          if e != -1:
            ent = text[i+1:e]
            if ent[0:1] == '#':
              try:
                if ent[1:2] == 'x':
                  # hex
                  out += unichr(int(ent[2:], 16))
                else:
                  # decimal
                  out += unichr(int(ent[1:]))
              except ValueError:
                printlog('numerical ref lookup error')
            else:
              if ent in htmlentitydefs.entitydefs:
                out += unicode(htmlentitydefs.entitydefs[ent], 'iso-8859-1')
              else:
                printlog('unknown ref &%s;' % ent[:16])
            i = e + 1
          else:
            # some data contains raw '&'
            printlog('raw &: %s' % text[i:i+16], True)
            out += '&'
            i += 1
      elif c == '\n':
        i += 1
        out += ' '
      else:
        i += 1
        out += c
    return (i, out)

def main(argv):
  import getopt, codecs
  sys.stdout = codecs.getwriter(sys.getfilesystemencoding())(sys.stdout)
  sys.stderr = codecs.getwriter(sys.getfilesystemencoding())(sys.stderr)
  def usage():
    print """usage: %s [options] dumpfile.xml
options:
  == mode ==
    default         : parse Wikipedia dump xml
    -q query-string : print titles of articles selected(title)
    -b query-string : print titles of articles selected(body)
  == output mode ==
    -c or --text  : output text to stdout (default)
    -m or --mysql : store to mysql
    -s or --senna : store to senna with SQTP
  == mode option ==
    -d or --database database-name : database name/file name
    -t or --table table-name       : table name
    -h or --host host-name         : hostname of database server
    -n or --port port-number       : port number of database
    -u or --user user-name         : username of database
    -p or --password password      : password of database"""
    return 1

  try:
    opts, args = getopt.getopt(argv[1:], 'q:b:cmsd:t:h:n:u:p:',
      longopts=('query=', 'bodyquery=', 'text', 'mysql', 'senna',
                'database=', 'table=',
                'host=', 'port=', 'user=', 'password='))
  except getopt.GetoptError:
    return usage()

  (query, bodyquery, mode, database, table, host, port, user, password) = \
    [None] * 9
  for (opt, val) in opts:
    if opt in ('-q', '--query'):
      query = val
    if opt in ('-b', '--bodyquery'):
      bodyquery = val
    if opt in ('-c', '--text'):
      mode = 'text'
    elif opt in ('-m', '--mysql'):
      mode = 'mysql'
    elif opt in ('-s', '--senna'):
      mode = 'senna'
    elif opt in ('-d', '--database'):
      database = val
    elif opt in ('-t', '--table'):
      # FIXME: check safe string or not on Recorder
      table = val
    elif opt in ('-h', '--host'):
      host = val
    elif opt in ('-n', '--port'):
      try:
        port = int(val)
      except ValueError:
        printlog('port number must be number')
        return 2
    elif opt in ('-u', '--user'):
      user = val
    elif opt in ('-p', '--password'):
      password = val
    else:
      printlog("invalid option '%s'", opt)

  rec = None
  if not mode or mode == 'text':
    rec = TextRecorder(database, table, host, port, user, password)
  elif mode == 'mysql':
    rec = MySQLRecorder(database, table, host, port, user, password)
  elif mode == 'senna':
    rec = SennaRecorder(database, table, host, port, user, password)
  else:
    printlog('invalid mode !')

  if query:
    rec.search_title(query)
  elif bodyquery:
    rec.search_body(bodyquery)
  else:
    if len(args) != 1:
      return usage()
    rec.truncate()
    h = MWXMLHandler(rec)
    sax.parse(args[0], h)

if __name__ == '__main__': sys.exit(main(sys.argv))
