#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Oleg Zubak <c4point@gmail.com>. All Rights Reserved.
# Based on the script for KeepassX by Juhamatti Niemelä <iiska@iki.fi>.
# This file is licensed under the GPLv2+. Please see COPYING for more information.
#
# Usage:
# ./keepass2pass.py -f export.xml
# By default, takes the name of the root element and puts all passwords in there, but you can disable this:
# ./keepass2pass.py -f export.xml -r ""
# Or you can use another root folder:
# ./keepass2pass.py -f export.xml -r foo
#
# Features:
# * This script can handle duplicates and will merge them.
# * Besides the password also the fields 'UserName', 'URL' and 'Notes' (comment) will be inserted.
# * You get a warning if an entry has no password, but it will still insert it.
# This script was updated by Oleg Zubak for working on Python3, because it not worksed on  new version of python

import getopt, sys
from subprocess import Popen, PIPE
from xml.etree import ElementTree


def pass_import_entry(path, data):
    """ Import new password entry to password-store using pass insert command """
    proc = Popen(['pass', 'insert', '--multiline', path], stdin=PIPE, stdout=PIPE)
    proc.communicate(data.encode('utf8'))
    proc.wait()
    

def get_value(elements, node_text):
    for element in elements:
        for child in element.findall('Key'):
            if child.text == node_text:
                return element.find('Value').text
    return ''        

def path_for(element, path=''):
    """ Generate path name from elements title and current path """
    if element.tag == 'Entry':
        title = get_value(element.findall("String"), "Title")
    elif element.tag == 'Group':
        title = element.find('Name').text
    else: title = ''
    
    if path == '': return title
    else: return '/'.join([path, title])

def password_data(element, path=''):
    """ Return password data and additional info if available from password entry element. """
    data = ""
    password = get_value(element.findall('String'), 'Password')
    if password is not None: data = password + "\n"
    else:
        print ("No password: %s" % path_for(element, path))
    
    for field in ['UserName', 'URL', 'Notes']:
        value = get_value(element, field)
        if value is not None and not len(value) == 0:
            data = "%s%s: %s\n" % (data, field, value)
    return data

def import_entry(entries, element, path=''):
    element_path = path_for(element, path) 
    if element_path in entries:
        print ("[INFO] Duplicate needs merging: %s" % element_path)
        existing_data = entries[element_path]
        data = "%s---------\nPassword: %s" % (existing_data, password_data(element))
    else:
        data = password_data(element, path)
        
    entries[element_path] = data

def import_group(entries, element, path=''):
    """ Import all entries and sub-groups from given group """
    npath = path_for(element, path)
    for group in element.findall('Group'):
        import_group(entries, group, npath)
    for entry in element.findall('Entry'):
        import_entry(entries, entry, npath)

def import_passwords(xml_file, root_path=None):
    """ Parse given Keepass2 XML file and import password groups from it """
    print ("[>>>>] Importing passwords from file %s" % xml_file)
    print ("[INFO] Root path: %s" % root_path)
    entries = dict()
    with open(xml_file) as xml:
        text = xml.read()
        xml_tree = ElementTree.XML(text)
        root = xml_tree.find('Root')
        root_group = root.find('Group')
        import_group(entries,root_group,'')
        if root_path is None: root_path = root_group.find('Name').text
        groups = root_group.findall('Group')
        for group in groups:
            import_group(entries, group, root_path)
        password_count = 0
        for path, data in sorted(entries.items()):
            sys.stdout.write("[>>>>] Importing %s ... " % path.encode("utf-8"))
            pass_import_entry(path, data)
            sys.stdout.write("OK\n")
            password_count += 1
            
        print ("[ OK ] Done. Imported %i passwords." % password_count)


def usage():
    """ Print usage """
    print ("Usage: %s -f XML_FILE" % (sys.argv[0]))
    print ("Optional:")
    print (" -r ROOT_PATH    Different root path to use than the one in xml file, use \"\" for none")


def main(argv):
    try:
        opts, args = getopt.gnu_getopt(argv, "f:r:")
    except getopt.GetoptError as err:
        print (str(err))
        usage()
        sys.exit(2)
    
    xml_file = None
    root_path = None
    
    for opt, arg in opts:
        if opt in "-f":
            xml_file = arg
        if opt in "-r":
            root_path = arg
    
    if xml_file is not None:
        import_passwords(xml_file, root_path)
    else:
        usage()
        sys.exit(2)
    
if __name__ == '__main__':
    main(sys.argv[1:])
