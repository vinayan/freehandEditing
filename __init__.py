def name():
  return "Freehand editing"

def description():
  return "Freehand line/polygon editing."

def version():
  return "0.2.5"

def qgisMinimumVersion():
  return "1.7"   
  
def authorName():
	return "Pavol Kapusta"

def icon():
	return "icon.png"

def classFactory(iface):
  from freehandediting import FreehandEditing
  return FreehandEditing(iface)
