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

def suggestMountain(riskCoeff, populationCoeff, geospatialCoeff, maxAccessibility, maxTravelTime, numSuggest = 1):
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

	mountainsCompleteList = []

	with open('data/userChecklist.csv') as checklistCSV:
		checklistCSV_read = csv.reader(checklistCSV, delimiter =',')
		for i in checklistCSV_read:
				mountainsCompleteList.append(i)

	mountainsCompleteList = mountainsCompleteList[0]
	del mountainsCompleteList[-1]
	mountainsComplete = len(mountainsCompleteList)
	mountainsCompleteStr = str(mountainsComplete) + ' of 58'

	suggestCol = [[sg.Button('Suggest a 14er for me', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'suggest')]]
	checklistCol = [[sg.Button('14er Checklist', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'checklist')]]
	coeffCol = [[sg.Button('Mountain Preferences', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'setCoeff')]]
	exitCol = [[sg.Button('Exit', button_color = ('white', backgroundColor), font=("Arial Black", 12), border_width= 0, key = 'exit')]]

	numComplete = [[sg.Text(mountainsCompleteStr, text_color = 'white', font=("Arial Black", 20), key = 'numComplete')]]
	ranges = [[sg.Listbox(values=['Front Range', 'Tenmile Range', 'Mosquito Range', 'Sawatch Range', 'Elk Mountains', 'San Juan Mountains', 'Sangre de Cristo Mountains'], size=(30, 10), key = 'ranges', enable_events = True),
			   sg.Listbox(values=['Select a mountain range'], size=(30, 10), key = 'mountains', enable_events = True)]]

	editMtnList = [[sg.Button('Add Mountain', size = (16, 1), key = 'addMtn', visible = False)], 
				[sg.Button('Remove Mountain', size = (16, 1), key = 'removeMtn', visible = False)]]

	riskText = 'No risk factor'
	populationText = 'No population factor'
	geospatialText = 'No geospatial factor'
	accessibilityText = 'Rough 2WD'
	maxTravelTimeText = '3 hours'

	coeffTextCol = [[sg.Text(riskText, justification='center', font=("Arial Black", 14), text_color = 'white', key = 'riskText', enable_events = True)], 
					[sg.Text(populationText, justification='center', font=("Arial Black", 14), text_color = 'white', key = 'populationText', enable_events = True)],
					[sg.Text(geospatialText, justification='center', font=("Arial Black", 14), text_color = 'white', key = 'geospatialText', enable_events = True)],
					[sg.Text(accessibilityText, justification='center', font=("Arial Black", 14), text_color = 'white', key = 'accessibilityText', enable_events = True)],
					[sg.Text(maxTravelTimeText, justification='center', font=("Arial Black", 14), text_color = 'white', key = 'maxTravelTimeText', enable_events = True)]]

	coeffSliderCol = [[sg.Slider(range = (-3, 3), key = 'riskCoeff', default_value = 0, disable_number_display = True, orientation = 'horizontal', enable_events = True, pad = ((0, 0), (6, 6)))], 
					[sg.Slider(range = (-3, 3), key = 'populationCoeff', default_value = 0, disable_number_display = True, orientation = 'horizontal', enable_events = True, pad = ((0, 0), (6, 6)))], 
					[sg.Slider(range = (-3, 3), key = 'geospatialCoeff', default_value = 0, disable_number_display = True, orientation = 'horizontal', enable_events = True, pad = ((0, 0), (6, 6)))], 
					[sg.Slider(range = (1, 6), key = 'maxAccessibility', default_value = 3, disable_number_display = True, orientation = 'horizontal', enable_events = True, pad = ((0, 0), (6, 6)))],
					[sg.Slider(range = (1, 8), key = 'maxTravelTime', default_value = 4, resolution = 0.2, disable_number_display = True, orientation = 'horizontal', enable_events = True, pad = ((0, 0), (6, 6)))]]

	homeLayout = [[sg.Text('Pocket Sherpa', size = (200, 1), justification='center', font=("Arial Black", 30), text_color = 'white', pad=((0,0),20))],
				[sg.Column(suggestCol, justification = 'center', element_justification = 'center', pad=((0,0),(40, 0)))],
				[sg.Column(checklistCol, justification = 'center', element_justification = 'center')],
				[sg.Column(coeffCol, justification = 'center', element_justification = 'center')],
				[sg.Column(exitCol, justification = 'center', element_justification = 'center')]]

	homeWindow = sg.Window('Pocket Sherpa v 0.1a', homeLayout, size=(400,350))


	while True:
		eventHome, valuesHome = homeWindow.read()

		if eventHome is 'checklist':
			homeWindow.Hide()

			checklistLayout = [  
				[sg.Text('14er Checklist', size = (200, 1), justification='center', font=("Arial Black", 30), text_color = 'white', pad=((0,0),20))],
				[sg.Column(numComplete, justification = 'center')],
				[sg.Column(ranges, justification = 'center')],
				[sg.Column(editMtnList, justification = 'center')] ]

			checklistWindow = sg.Window('Pocket Sherpa v 0.1a', checklistLayout, size=(600,420))

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

					checklistWindow.FindElement('addMtn').Update(visible = True)
					checklistWindow.FindElement('removeMtn').Update(visible = True)
					checklistWindow.FindElement('mountains').Update(values = currentRange)

					for i in currentRange:
						if i in mountainsCompleteList:
							currentRange.remove(i)
							currentRange.insert(0, i + ' --- ✔')
							checklistWindow.FindElement('mountains').Update(values = currentRange)

				if eventChecklist in ('addMtn', 'removeMtn'):
					selectMountain = valuesChecklist['mountains'][0]
					if (eventChecklist is 'addMtn') and (selectMountain not in mountainsCompleteList) and (' --- ✔' not in selectMountain):
						mountainsComplete += 1
						currentRange.remove(selectMountain)
						currentRange.insert(0, selectMountain + ' --- ✔')
						checklistWindow.FindElement('mountains').Update(values = currentRange)

						mountainsCompleteList.append(selectMountain)

					elif (eventChecklist is 'removeMtn') and (selectMountain.rstrip(' --- ✔') in mountainsCompleteList):
						mountainsComplete -= 1
						mountainsCompleteList.remove(selectMountain.rstrip(' --- ✔'))
						currentRange.remove(selectMountain)
						currentRange.insert(len(currentRange), selectMountain.rstrip(' --- ✔'))
						checklistWindow.FindElement('mountains').Update(values = currentRange)

					if mountainsComplete < 0:
						mountainsComplete = 0

					mountainsCompleteStr = str(mountainsComplete) + ' of 58'
					checklistWindow.FindElement('numComplete').Update(mountainsCompleteStr)

				if eventChecklist in (None, 'exit'):
					checklistWindow.close()
					
					with open('data/userChecklist.csv', 'w') as checklistCSV:
						for i in mountainsCompleteList:
								checklistCSV.write('%s,' % i)
					homeWindow.UnHide()
					break

		if eventHome is 'setCoeff':
			homeWindow.Hide()

			coeffLayout = [[sg.Text('Set Preference Profile', size = (200, 1), justification='center', font=("Arial Black", 20), text_color = 'white', pad=((0,0), 20))],
						[sg.Frame(title = '', layout = coeffTextCol, element_justification = 'right', border_width = 0, size = (200,300)), sg.Frame(title = '', layout = coeffSliderCol, element_justification = 'center', border_width = 0, size = (400,300))]]

			coeffWindow = sg.Window('Pocket Sherpa v 0.1a', coeffLayout, size=(600,420))

			while True:
				eventCoeff, valuesCoeff = coeffWindow.read()
				if eventCoeff in ('riskCoeff', 'populationCoeff', 'geospatialCoeff', 'maxAccessibility', 'maxTravelTime'):
					coeffMatrix = [valuesCoeff['riskCoeff'], valuesCoeff['populationCoeff'], valuesCoeff['geospatialCoeff'], valuesCoeff['maxAccessibility'], valuesCoeff['maxTravelTime']]

					riskTextArray = ['No risk', 'Risk adverse', 'Less risk', 'No risk factor', 'Some risk', 'Risk seeker', 'Risk lover']

					for i in range(7):
						if coeffMatrix[0] == i-3:
							riskText = riskTextArray[i]
							coeffWindow.FindElement('riskText').Update(riskText)

					populationTextArray = ['Hermit', 'Introvert', 'Less people', 'No population factor', 'Prefer people', 'Extrovert', 'Raging extrovert']

					for i in range(7):
						if coeffMatrix[1] == i-3:
							populationText = populationTextArray[i]
							coeffWindow.FindElement('populationText').Update(populationText)

					geospatialTextArray = ['Fast as possible', 'Quick jaunt', 'Less lengthy', 'No geospatial factor', 'Lengthier trip', 'An all day trek', 'Brutal endeavor']

					for i in range(7):
						if coeffMatrix[2] == i-3:
							geospatialText = geospatialTextArray[i]
							coeffWindow.FindElement('geospatialText').Update(geospatialText)

					accessibilityTextArray = ['Paved road', 'Easy 2WD', 'Rough 2WD', 'Easy 4WD', 'Rough 4WD', 'Extreme']

					for i in range(7):
						if coeffMatrix[3] == i:
							accessibilityText = accessibilityTextArray[i-1]
							coeffWindow.FindElement('accessibilityText').Update(accessibilityText)



					# maxTravelTimeText = coeffMatrix[4]
					# coeffWindow.FindElement('maxTravelTimeText').Update(str(maxTravelTimeText) + ' hours')

				if eventCoeff in (None, 'exit'):
					coeffWindow.close()
					homeWindow.UnHide()
					break

		if eventHome in (None, 'exit'):
			break

	homeWindow.close()

launchGUI()