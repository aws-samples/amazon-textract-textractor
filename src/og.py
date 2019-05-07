import json
from helper import FileHelper
from ta import TextAnalyzer, TextMedicalAnalyzer, TextTranslater
from trp import *

class OutputGenerator:
    def __init__(self, response, fileName, forms, tables):
        self.response = response
        self.fileName = fileName
        self.forms = forms
        self.tables = tables

        self.document = Document(self.response)

    def _outputWords(self, page, p):
        csvData = []
        for line in page.lines:
            for word in line.words:
                csvItem  = []
                csvItem.append(word.id)
                if(word.text):
                    csvItem.append(word.text)
                else:
                    csvItem.append("")
                csvData.append(csvItem)
        csvFieldNames = ['Word-Id', 'Word-Text']
        FileHelper.writeCSV("{}-page-{}-words.csv".format(self.fileName, p), csvFieldNames, csvData)

    def _outputText(self, page, p):
        text = page.text
        FileHelper.writeToFile("{}-page-{}-text.txt".format(self.fileName, p), text)

        textInReadingOrder = page.getTextInReadingOrder()
        FileHelper.writeToFile("{}-page-{}-text-inreadingorder.txt".format(self.fileName, p), textInReadingOrder)

    def _outputForm(self, page, p):
        csvData = []
        for field in page.form.fields:
            csvItem  = []
            if(field.key):
                csvItem.append(field.key.text)
                csvItem.append(field.key.confidence)
            else:
                csvItem.append("")
                csvItem.append("")
            if(field.value):
                csvItem.append(field.value.text)
                csvItem.append(field.value.confidence)
            else:
                csvItem.append("")
                csvItem.append("")
            csvData.append(csvItem)
        csvFieldNames = ['Key', 'KeyConfidence', 'Value', 'ValueConfidence']
        FileHelper.writeCSV("{}-page-{}-forms.csv".format(self.fileName, p), csvFieldNames, csvData)

    def _outputTable(self, page, p):

        csvData = []
        for table in page.tables:
            csvRow = []
            csvRow.append("Table")
            csvData.append(csvRow)
            for row in table.rows:
                csvRow  = []
                for cell in row.cells:
                    csvRow.append(cell.text)
                csvData.append(csvRow)
            csvData.append([])
            csvData.append([])

        FileHelper.writeCSVRaw("{}-page-{}-tables.csv".format(self.fileName, p), csvData)

    def run(self):

        if(not self.document.pages):
            return

        FileHelper.writeToFile("{}-response.json".format(self.fileName), json.dumps(self.response))

        print("Total Pages in Document: {}".format(len(self.document.pages)))

        p = 1
        for page in self.document.pages:

            FileHelper.writeToFile("{}-page-{}-response.json".format(self.fileName, p), json.dumps(page.blocks))

            self._outputWords(page, p)

            self._outputText(page, p)

            if(self.forms):
                self._outputForm(page, p)

            if(self.tables):
                self._outputTable(page, p)

            p = p + 1

    def _insights(self, start, subText, sentiment, syntax, entities, keyPhrases, ta):
        # Sentiment
        dsentiment = ta.getSentiment(subText)
        dsentimentRow = []
        dsentimentRow.append(dsentiment["Sentiment"])
        sentiment.append(dsentimentRow)

        # Syntax
        dsyntax = ta.getSyntax(subText)
        for dst in dsyntax['SyntaxTokens']:
            dsyntaxRow = []
            dsyntaxRow.append(dst["PartOfSpeech"]["Tag"])
            dsyntaxRow.append(dst["PartOfSpeech"]["Score"])
            dsyntaxRow.append(dst["Text"])
            dsyntaxRow.append(int(dst["BeginOffset"])+start)
            dsyntaxRow.append(int(dst["EndOffset"])+start)
            syntax.append(dsyntaxRow)

        # Entities
        dentities = ta.getEntities(subText)
        for dent in dentities['Entities']:
            dentitiesRow = []
            dentitiesRow.append(dent["Type"])
            dentitiesRow.append(dent["Text"])
            dentitiesRow.append(dent["Score"])
            dentitiesRow.append(int(dent["BeginOffset"])+start)
            dentitiesRow.append(int(dent["EndOffset"])+start)
            entities.append(dentitiesRow)

        # Key Phrases
        dkeyPhrases = ta.getKeyPhrases(subText)
        for dkphrase in dkeyPhrases['KeyPhrases']:
            dkeyPhrasesRow = []
            dkeyPhrasesRow.append(dkphrase["Text"])
            dkeyPhrasesRow.append(dkphrase["Score"])
            dkeyPhrasesRow.append(int(dkphrase["BeginOffset"])+start)
            dkeyPhrasesRow.append(int(dkphrase["EndOffset"])+start)
            keyPhrases.append(dkeyPhrasesRow)

    def _medicalInsights(self, start, subText, medicalEntities, phi, tma):
        # Entities
        dentities = tma.getMedicalEntities(subText)
        for dent in dentities['Entities']:
            dentitiesRow = []
            dentitiesRow.append(dent["Text"])
            dentitiesRow.append(dent["Type"])
            dentitiesRow.append(dent["Category"])
            dentitiesRow.append(dent["Score"])
            dentitiesRow.append(int(dent["BeginOffset"])+start)
            dentitiesRow.append(int(dent["EndOffset"])+start)
            medicalEntities.append(dentitiesRow)


        phi.extend(tma.getPhi(subText))

    def _generateInsightsPerDocument(self, page, p, insights, medicalInsights, translate, ta, tma, tt):

        maxLen = 2000

        text = page.text

        start = 0
        sl = len(text)

        sentiment = []
        syntax = []
        entities = []
        keyPhrases = []
        medicalEntities = []
        phi = []
        translation = ""

        while(start < sl):
            end = start + maxLen
            if(end > sl):
                end = sl

            subText = text[start:end]

            if(insights):
                self._insights(start, text, sentiment, syntax, entities, keyPhrases, ta)

            if(medicalInsights):
                self._medicalInsights(start, text, medicalEntities, phi, tma)

            if(translate):
                translation = translation + tt.getTranslation(subText) + "\n"

            start = end

        if(insights):
            FileHelper.writeCSV("{}-page-{}-insights-sentiment.csv".format(self.fileName, p),
                            ["Sentiment"], sentiment)
            FileHelper.writeCSV("{}-page-{}-insights-entities.csv".format(self.fileName, p),
                            ["Type", "Text", "Score", "BeginOffset", "EndOffset"], entities)
            FileHelper.writeCSV("{}-page-{}-insights-syntax.csv".format(self.fileName, p),
                            ["PartOfSpeech-Tag", "PartOfSpeech-Score", "Text", "BeginOffset", "EndOffset"], syntax)
            FileHelper.writeCSV("{}-page-{}-insights-keyPhrases.csv".format(self.fileName, p),
                            ["Text", "Score", "BeginOffset", "EndOffset"], keyPhrases)

        if(medicalInsights):
            FileHelper.writeCSV("{}-page-{}-medical-insights-entities.csv".format(self.fileName, p),
                            ["Text", "Type", "Category", "Score", "BeginOffset", "EndOffset"], medicalEntities)

            FileHelper.writeToFile("{}-page-{}-medical-insights-phi.json".format(self.fileName, p), json.dumps(phi))

        if(translate):
            FileHelper.writeToFile("{}-page-{}-text-translation.txt".format(self.fileName, p), translation)

    def generateInsights(self, insights, medicalInsights, translate, awsRegion):

        print("Generating insights...")

        if(not self.document.pages):
            return

        ta = TextAnalyzer('en', awsRegion)
        tma = TextMedicalAnalyzer(awsRegion)

        tt = None
        if(translate):
            tt = TextTranslater('en', translate, awsRegion)

        p = 1
        for page in self.document.pages:
            self._generateInsightsPerDocument(page, p, insights, medicalInsights, translate, ta, tma, tt)
            p = p + 1
