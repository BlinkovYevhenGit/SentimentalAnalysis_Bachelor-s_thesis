import time

from LSTM import LSTM
from CNN import CNN
from CNN_LSTM import CNN_LSTM
from MongoManager import deleteAllModels
from NaiveBayesClassifier import NaiveBayesClassifier
from DataLoader import loadData
from DataLoader import loadBayesData
import matplotlib
import os
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from LSTM_Config import LSTMConfiguration
from CNN_Config import CNNConfiguration
from CNN_LSTM_Config import CNN_LSTMConfiguration


class Estimator:

    def estimate(self, top_words, review_len, Bayes_Input, LSTM_Config, CNN_Config, CNN_LSTM_Config, userText):
        #deleteAllModels()
        test_x, test_y, train_x, train_y=[],[],[],[]
        accList = dict()
        lossList = dict()

        histories = ["","",""]
        predictions=list()
        time_results=[None,None,None,None]
        text_results = ["", "", "",""]
        textTones = ["", "", "",""]
        definedClasses = ["", "", "",""]
        if Bayes_Input=="useBayes" or len(CNN_LSTM_Config)!=0 or len(CNN_Config)!=0 or len(LSTM_Config)!=0:
            test_x, test_y, train_x, train_y = loadData(top_words, review_len)

        else:return histories,lossList,accList,predictions,text_results, []
        if Bayes_Input=="useBayes":
            bayes_test_x, bayes_test_y, bayes_train_x, bayes_train_y=loadBayesData(top_words,review_len,test_x, test_y, train_x, train_y )
            start_time = time.time()
            bayesResults,results, acc,bayesPrediction,classTone,definedClass  = self.estimateBayes(top_words, review_len, userText,bayes_test_x, bayes_test_y, bayes_train_x, bayes_train_y)
            start_time = -start_time+time.time()
            time_results[0]=start_time
            accList.update({"Naive Bayes": bayesResults / 100})
            predictions.append(bayesPrediction)
            text_results[0] = bayesPrediction
            textTones[0] = "{:.3f}".format(classTone)
            definedClasses[0] = definedClass
        if len(CNN_LSTM_Config)!=0:
            start_time = time.time()

            historyCNN_LSTM, evalCNN_LSTM,cnn_lstmPrediction,classTone, definedClass  = self.estimateCNN_LSTM(top_words, review_len, CNN_LSTM_Config, userText,test_x, test_y, train_x, train_y )
            start_time = -start_time + time.time()
            time_results[1] = start_time
            histories[0]=tuple(("CNN_LSTM", historyCNN_LSTM))
            lossList.update({"CNN_LSTM": evalCNN_LSTM[0]})
            accList.update({"CNN_LSTM": evalCNN_LSTM[1]})
            predictions.append(cnn_lstmPrediction)
            text_results[1] = cnn_lstmPrediction
            textTones[1] = "{:.3f}".format(classTone)
            definedClasses[1] = definedClass

        if len(CNN_Config) != 0:
            start_time = time.time()
            historyCNN, evalCNN,cnnPrediction,classTone, definedClass  =  self.estimateCNN(top_words, review_len, CNN_Config, userText,test_x, test_y, train_x, train_y )
            start_time = -start_time + time.time()
            time_results[2] = start_time
            histories[1]=tuple(("CNN", historyCNN))
            lossList.update({"CNN": evalCNN[0]})
            accList.update({"CNN": evalCNN[1]})
            predictions.append(cnnPrediction)
            text_results[2] = cnnPrediction
            textTones[2] = "{:.3f}".format(classTone)
            definedClasses[2] = definedClass
        if len(LSTM_Config) != 0:
            start_time = time.time()

            historyLSTM, evalLSTM,LSTM_Prediction,classTone, definedClass  = self.estimateLSTM(top_words, review_len, LSTM_Config, userText,test_x, test_y, train_x, train_y )
            start_time = -start_time + time.time()
            time_results[3] = start_time
            histories[2]=tuple(("LSTM", historyLSTM))
            lossList.update({"LSTM": evalLSTM[0]})
            accList.update({"LSTM": evalLSTM[1]})
            predictions.append(LSTM_Prediction)
            text_results[3] = LSTM_Prediction
            textTones[3] = "{:.3f}".format(classTone)
            definedClasses[3] = definedClass
        tableResult = [dict(Text=text_results[0], Prediction=textTones[0], PredictionClass=definedClasses[0]),
                       dict(Text=text_results[1], Prediction=textTones[1], PredictionClass=definedClasses[1]),
                       dict(Text=text_results[2], Prediction=textTones[2], PredictionClass=definedClasses[2]),
                       dict(Text=text_results[3], Prediction=textTones[3], PredictionClass=definedClasses[3])]
        plot = self.outputGraph(histories)
        self.showTestResultsGraph(accList, lossList, plot)

        print(tableResult)
        report = self.makeReport(histories, accList, lossList, time_results)
        return histories,lossList,accList,predictions,text_results, tableResult,report

    def makeReport(self,histories,accList,lossList,timeResults):
        report=[dict(ModelName="Наївний Баєсів Класифікатор", StageData=
                    [dict(StageName = "Тестування",subStatisticsTable=
                        [dict( EpochNumber=0,Accuracy= getValueFromDictionary('Naive Bayes', accList),Loss="N/A")])
                    ],TimeCol=timeResults[0]),
                dict(ModelName="Комбінована нейронна мережа", StageData=
                    [dict(StageName="Навчання", subStatisticsTable=self.getStatisticsList(histories, 0)),
                     dict(StageName="Тестування", subStatisticsTable=
                        [dict(EpochNumber=0, Accuracy=getValueFromDictionary('CNN_LSTM', accList), Loss=getValueFromDictionary("CNN_LSTM",lossList))])
                    ], TimeCol=timeResults[1]),
                dict(ModelName="Згорткова нейронна мережа", StageData=
                    [dict(StageName="Навчання", subStatisticsTable=self.getStatisticsList(histories, 1)),
                     dict(StageName="Тестування", subStatisticsTable=
                        [dict(EpochNumber=0, Accuracy=getValueFromDictionary('CNN',accList), Loss=getValueFromDictionary("CNN",lossList))])
                     ],TimeCol=timeResults[2]),
                dict(ModelName="Рекурентна нейронна мережа з ДКЧП", StageData=
                    [dict(StageName="Навчання", subStatisticsTable=self.getStatisticsList(histories, 2)),
                     dict(StageName="Тестування", subStatisticsTable=
                        [dict(EpochNumber=0, Accuracy=getValueFromDictionary('LSTM',accList), Loss=getValueFromDictionary("LSTM",lossList))])
                    ], TimeCol=timeResults[3])
                ]
        return report
    def getStatisticsList(self,histories,algoNumber):
        statList=[]
        if histories[algoNumber]!="":
            # print(len(histories[algoNumber][1].history['acc']))
            # print(histories[algoNumber][1].history['acc'])
            for i in range(0,len(histories[algoNumber][1].history['acc'])):
                 statList.append(dict(EpochNumber=i, Accuracy=histories[algoNumber][1].history['acc'][i], Loss=histories[algoNumber][1].history['loss'][i]))
        return statList

    def showTestResultsGraph(self, accList, lossList, plot):
        accNames = list(accList.keys())
        accValues = list(accList.values())
        lossNames = list(lossList.keys())
        lossValues = list(lossList.values())
        plot.figure(1)
        fig, axs = plot.subplots(1, 2, figsize=(13, 5))
        axs[0].bar(accNames, accValues)
        axs[0].set_title("Точність аналізу тексту з тестової вибірки")
        axs[1].bar(lossNames, lossValues)
        axs[1].set_title("Значення функції втрат")
        fig.suptitle('Ефективність алгоритмів на текстах з тестової вибірки', y=0.99)
        plot.savefig("./static/graphs/graph1.png")



    def outputGraph(self, histories):
        plt.figure(figsize=(13, 5))
        for history in histories:
            if history != "":
                algoName, algoHistory = history
                plt.plot(algoHistory.history['loss'], label=('%s training loss' % algoName))
                plt.plot(algoHistory.history['acc'], label=('%s training accuracy' % algoName))
                plt.legend(loc="upper left")
        plt.xlabel('№ епохи навчання')
        plt.ylabel('Значення')
        plt.title('Ефективність алгоритмів впродовж періоду тренування моделей', y=0.99)
        plt.savefig("./static/graphs/graph2.png")
        return plt

    def estimateLSTM(self, top_words, review_len, LSTM_Config, userText,test_x, test_y, train_x, train_y):

        #config = LSTMConfiguration(32, True, 100, 0.2, 0.2, 1, 128, 3)
        config = LSTMConfiguration(LSTM_Config[0],LSTM_Config[1],LSTM_Config[2],LSTM_Config[3],
                                   LSTM_Config[4],LSTM_Config[5],LSTM_Config[6],LSTM_Config[7])

        #lstm = LSTM(5000, 50, config)
        lstm = LSTM(top_words, review_len, config)


        model, history, eval_epoch_history = lstm.defineModel(test_x, test_y, train_x, train_y)

        # model = lstm.loadModel()

        lstm_result,prediction, definedClass = lstm.runModel(model, userText, review_len)

        return history, eval_epoch_history,lstm_result,prediction, definedClass

    def estimateCNN(self, top_words, review_len, CNN_Config, userText,test_x, test_y, train_x, train_y):
        # embedding_size = 32
        #
        # kernel_size = 3
        # filters = 32
        # pool_size = 2
        #
        # dense_units1 = 250
        # dense_units2 = 1
        #
        # batch_size = 128
        # epochs = 6
        config=CNNConfiguration(CNN_Config[0],CNN_Config[1],CNN_Config[2],CNN_Config[3],
                                CNN_Config[4],CNN_Config[5],CNN_Config[6],CNN_Config[7])
        #config = CNNConfiguration(32, 3, 32, 2, 250, 1, 128, 3)
        cnn=CNN(top_words, review_len, config)
        #cnn = CNN(5000, 50, config)
        model, history, eval_epoch_history = cnn.defineModel(test_x, test_y, train_x, train_y)

        #model = cnn.loadModel()
        cnn_result,prediction, definedClass =cnn.runModel(model, userText, review_len)
        return history, eval_epoch_history,cnn_result,prediction, definedClass

    def estimateCNN_LSTM(self, top_words, review_len, CNN_LSTM_Config, userText,test_x, test_y, train_x, train_y):
        # embedding_size = 128
        #
        # # Convolution
        # kernel_size = 5
        # filters = 64
        # pool_size = 4
        #
        # # LSTM
        # lstm_output_size = 70
        #
        # # Training
        # batch_size = 128
        # epochs = 6
        #
        # dropout = 0.25
        # strides = 1
        # dense = 1
        #config = CNN_LSTMConfiguration(128, 5, 64, 4, 70, 128, 3, 0.25, 1, 1)
        config=CNN_LSTMConfiguration(CNN_LSTM_Config[0],CNN_LSTM_Config[1],CNN_LSTM_Config[2],CNN_LSTM_Config[3],CNN_LSTM_Config[4],
                                     CNN_LSTM_Config[5],CNN_LSTM_Config[6],CNN_LSTM_Config[7],CNN_LSTM_Config[8],CNN_LSTM_Config[9])

        #cnn_lstm = CNN_LSTM(5000, 100, config)
        cnn_lstm = CNN_LSTM(top_words, review_len, config)

        model, history, eval_epoch_history = cnn_lstm.defineModel(test_x, test_y, train_x, train_y)

        #model = cnn_lstm.loadModel()
        cnn_lstm_result,prediction, definedClass = cnn_lstm.runModel(model, userText, review_len)
        return history, eval_epoch_history,cnn_lstm_result,prediction, definedClass


    def estimateBayes(self, top_words, review_len, userText,training_set, training_labels, validation_set, validation_labels):
        print(training_set[0], training_labels[0])
        print(validation_set[0], validation_labels[0])

        NBClassifier = NaiveBayesClassifier()
        model, train_results = NBClassifier.defineModel(validation_set, validation_labels, training_set,
                                                        training_labels)
        results, acc, bayes_result,classTone,definedClass=NBClassifier.runModel(model,userText,None)
        return train_results,results,acc,bayes_result,classTone,definedClass

    def runCNN(self,filename,review_len,userText):
        cnn = CNN()
        model = cnn.loadModel(filename)
        cnn_result,prediction, definedClass = cnn.runModel(model, userText, review_len)
        return cnn_result,prediction, definedClass

    def runCNN_LSTM(self, filename, review_len, userText):
        cnn_lstm = CNN_LSTM()
        model = cnn_lstm.loadModel(filename)
        cnn_lstm_result,prediction, definedClass = cnn_lstm.runModel(model, userText, review_len)
        return cnn_lstm_result,prediction, definedClass

    def runLSTM(self, filename, review_len, userText):
        lstm = LSTM()
        model = lstm.loadModel(filename)
        lstm_result,prediction, definedClass = lstm.runModel(model, userText, review_len)
        return lstm_result,prediction, definedClass

    def runAll(self,filenames,review_len_s,userText):
        results=["","",""]
        classTones=["","",""]
        definedClasses=["","",""]
        if filenames[0]!=None:
            modelName,classTone, definedClass=self.runLSTM(filenames[0],review_len_s[0],userText)
            results[0]=modelName
            classTones[0] = "{:.3f}".format(classTone)
            definedClasses[0] = definedClass
        if filenames[1]!=None:
            modelName,classTone, definedClass=self.runCNN(filenames[1],review_len_s[1],userText)
            results[1]=modelName
            classTones[1] = "{:.3f}".format(classTone)
            definedClasses[1] = definedClass
        if filenames[2]!=None:
            modelName,classTone, definedClass=self.runCNN_LSTM(filenames[2],review_len_s[2],userText)
            results[2]=modelName
            classTones[2] = "{:.3f}".format(classTone)
            definedClasses[2] = definedClass
        tableResult=[dict(Text=results[0],Prediction=classTones[0],PredictionClass=definedClasses[0]),dict(Text=results[1],Prediction=classTones[1],PredictionClass=definedClasses[1]),dict(Text=results[2],Prediction=classTones[2],PredictionClass=definedClasses[2])]
        # for r,p,d in results,predictions,definedClasses:
        #     tableResult.append(dict(Text=r,Prediction=p,PredictionClass=d))
        print(tableResult)
        return results,tableResult

def deleteSavedImages():
    print("Removing old graphs... \n")
    mp = ".\\static\\graphs\\"
    for f in os.listdir(mp):
        os.remove(os.path.join(mp, f))

def getValueFromDictionary(argument, dictionary):
    value = None
    try:
        value = dictionary.get(argument, "")
    except:
        pass
    return value