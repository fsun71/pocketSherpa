import pandas as pd
import numpy as np
import csv
import PySimpleGUI as sg

pd.set_option('display.max_columns', None)

peakData = pd.read_csv("data/masterPeakData.csv")
peakData = peakData[['Route', 'riskQuotient', 'populationQuotient', 'geospatialQuotient', 'accessibilityQuotient', 'travelQuotient']]
peakData.set_index('Route')
#print(peakQuotients.head(5))

elk = ['Castle Peak', 'Maroon Peak', 'Capitol Peak', 'Snowmass Mountain', 'Conundrum Peak', 'Pyramid Peak', 'North Maroon Peak']
front = ['Grays Peak', 'Torreys Peak', 'Mt. Evans', 'Longs Peak', 'Mt. Bierstadt']
tenmile = ['Quandary Peak']
mosquito = ['Mt. Lincoln', 'Mt. Cameron', 'Mt. Bross', 'Mt. Democrat', 'Mt. Sherman']
sanJuan = ['Uncompahgre Peak', 'Mt. Wilson', 'El Diente Peak', 'Mt. Sneffels', 'Windom Peak', 'Mt. Eolus', 'Sunlight Peak', 'Handies Peak', 'North Eolus', 'Redcloud Peak', 'Wilson Peak', 'Wetterhorn Peak', 'San Luis Peak', 'Sunshine Peak']
sangreDeCristo = ['Blanca Peak', 'Crestone Peak', 'Crestone Needle','Kit Carson Peak', 'Challenger Point', 'Humboldt Peak', 'Culebra Peak', 'Ellingwood Point', 'Mt. Lindsey', 'Little Bear Peak']
sawatch = ['Mt. Elbert', 'Mt. Massive', 'Mt. Harvard', 'La Plata Peak', 'Mt. Antero', 'Mt. Shavano', 'Mt. Princeton', 'Mt. Belford', 'Mt. Yale', 'Tabeguache Peak', 'Mt. Oxford', 'Mt. Columbia', 'Missouri Mountain', 'Mt. of the Holy Cross', 'Huron Peak']

def suggestMountain(riskCoeff, populationCoeff, geospatialCoeff, maxAccessibility, maxTravelTime, numSuggest = 5):
	#Perhaps introduce some sort of quadrative/bell curveish stuff idk
	filterMatrix = [maxAccessibility, maxTravelTime]
	coeffMatrix = [riskCoeff, -populationCoeff, geospatialCoeff]
	utility = 0

	peakDataFiltered = peakData.loc[((peakData['accessibilityQuotient'] * 6) <= filterMatrix[0]) & ((peakData['travelQuotient'] / 3600) <= filterMatrix[1])]
	peakDataFilteredMatrix = peakDataFiltered[['riskQuotient', 'populationQuotient', 'geospatialQuotient']]

	for i in range(3):
		utility = utility + (coeffMatrix[i] * peakDataFilteredMatrix.iloc[:,i])

	routeUtilityMatrix = []

	for routeUtilPair in range(118):
		routeUtilityMatrix.append([peakData['Route'][routeUtilPair], utility [routeUtilPair]])

	routeUtilityDF = pd.DataFrame(routeUtilityMatrix)
	routeUtilityDF.rename(columns = {0:'Route', 1:'Utility'}, inplace = True)

	bestRoute = routeUtilityDF.loc[routeUtilityDF['Utility'].idxmax()]
	worstRoute = routeUtilityDF.loc[routeUtilityDF['Utility'].idxmin()]
	routeUtilityMatrixDF = pd.DataFrame(routeUtilityMatrix)
	routeUtilitySorted = routeUtilityMatrixDF.sort_values(by = [1])

	return routeUtilitySorted[-numSuggest:][0].to_string(index = False)

def launchGUI():
	backgroundColor = '#4266a1'
	sg.SetOptions(background_color = backgroundColor, element_background_color = backgroundColor)

	col1 = [[sg.Button('Suggest a 14er for me', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'suggest')]]
	col2 = [[sg.Button('14er Checklist', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'checklist')]]
	col3 = [[sg.Button('Exit', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'exit')]]

	numComplete = [[sg.Text('0/58', text_color = 'white', font=("Arial Black", 20), key = 'numComplete')]]
	ranges = [[sg.Listbox(values=['Front Range', 'Tenmile Range', 'Mosquito Range', 'Sawatch Range', 'Elk Mountains', 'San Juan Mountains', 'Sangre de Cristo Mountains'], size=(30, 10), key = 'ranges', enable_events = True),
			   sg.Listbox(values=[], size=(30, 10), key = 'mountains', enable_events = True)]]

	homeLayout = [  [sg.Text('Pocket Sherpa', size = (200, 1), justification='center', font=("Arial Black", 30), text_color = 'white', pad=((0,0),20))],
				#[sg.Text(suggestMountain(1, 1, 1, 6, 10, 1), size = (200, 1), justification='center', font=("Arial Black", 16), text_color = 'white')],
	            [sg.Column(col1, justification = 'center', element_justification = 'center', pad=((0,0),(30, 10)))],
	            [sg.Column(col2, justification = 'center', element_justification = 'center')],
	            [sg.Column(col3, justification = 'center', element_justification = 'center')] ]

	homeWindow = sg.Window('Pocket Sherpa v 0.1a', homeLayout, size=(600,400), grab_anywhere = True)

	while True:
	    eventHome, valuesHome = homeWindow.read()

	    if eventHome is 'checklist':
	    	#homeWindow.Hide()

	    	checklistLayout = [  
	    		[sg.Text('14er Checklist', size = (200, 1), justification='center', font=("Arial Black", 30), text_color = 'white', pad=((0,0),20))],
	    		[sg.Column(numComplete, justification = 'center')],
	    		[sg.Column(ranges, justification = 'center')] ]

	    	checklistWindow = sg.Window('Pocket Sherpa v 0.1a', checklistLayout, size=(600,400), grab_anywhere = True)

	    	while True:
	    		eventChecklist, valuesChecklist = checklistWindow.read()
	    		if eventChecklist is 'ranges':
	    			selectRange = valuesChecklist['ranges'][0]
	    			currentRange = ''

	    			if(selectRange == 'Front Range'):
	    				currentRange = front
	    			elif(selectRange == 'Tenmile Range'):
	    				currentRange = tenmile
	    			elif(selectRange == 'Mosquito Range'):
	    				currentRange = mosquito
	    			elif(selectRange == 'Sawatch Range'):
	    				currentRange = sawatch
	    			elif(selectRange == 'Elk Mountains'):
	    				currentRange = elk
	    			elif(selectRange == 'San Juan Mountains'):
	    				currentRange = sanJuan
	    			elif(selectRange == 'Sangre de Cristo Mountains'):
	    				currentRange = sangreDeCristo

	    			checklistWindow.FindElement('mountains').Update(currentRange)

	    		if eventChecklist is 'mountains':
	    			selectMountain = valuesChecklist['mountains'][0]
	    			print(selectMountain)

	    		if eventChecklist in (None, 'exit'):
	    			checklistWindow.close()
	    			#homeWindow.UnHide()
	    			break

	    if eventHome in (None, 'exit'):
	        break

	homeWindow.close()

launchGUI()