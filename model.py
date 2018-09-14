# -*- coding: utf-8 -*-
# Author  : Super~Super
# FileName: model.py
# Python  : python3.6
# Time    : 18-9-14 16:45
import json
import numpy as np
from keras.models import Sequential, load_model
from keras import models
from keras.layers import Embedding, Bidirectional, LSTM, Dense, Dropout
from keras.preprocessing.sequence import pad_sequences
from keras_contrib.layers import CRF
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from keras.callbacks import TensorBoard
from keras.callbacks import ModelCheckpoint
from keras.layers import Input

voc_size = 3142
max_len = 80
tag_size = 7
epoches = 10

with open('data/num2word', 'r') as f:
    num2word = json.load(f)
word2num = {
    w: k for k, w in num2word.items()
}
tag2label = {"O": 0,
             "B-PER": 1, "I-PER": 2,
             "B-LOC": 3, "I-LOC": 4,
             "B-ORG": 5, "I-ORG": 6
             }
label2tag = {
    w: k for k, w in tag2label.items()
}

def gen_datasets():

    X = np.load('data/X.npy')
    Y = np.load('data/Y.npy')
    X_, Y_ = shuffle(X, Y)
    X_ = pad_sequences(X_, maxlen=max_len, value=0)
    Y_ = pad_sequences(Y_, maxlen=max_len, value=-1)
    Y_ = np.expand_dims(Y_, 2)
    X_train, X_test, Y_train, Y_test = train_test_split(X_, Y_, test_size=0.3, random_state=0)
    return X_train, X_test, Y_train, Y_test

def train():
    model = Sequential()
    model.add(Embedding(voc_size, 128, mask_zero=True))
    model.add(Bidirectional(LSTM(64, return_sequences=True)))
    model.add(Dropout(rate=0.5))
    model.add(Dense(tag_size))
    crf = CRF(tag_size, sparse_target=True)
    model.add(crf)
    model.summary()
    model.compile('adam', loss=crf.loss_function, metrics=[crf.accuracy])
    X_train, X_test, Y_train, Y_test = gen_datasets()
    # 可视化
    tb = TensorBoard(log_dir='./tb_logs/0914', histogram_freq=0, write_graph=True, write_images=False,
                     embeddings_freq=0, embeddings_layer_names=None, embeddings_metadata=None)
    # 早停，val_loss不再改善时，中止训练，epoch粒度
    # early_stopping = EarlyStopping(monitor='val_loss', patience=2)
    # keras.callbacks.Callback()除了默认包含epoch结尾的各结果还包含batch结尾的各个结果
    # modelcheckpoint
    cp = ModelCheckpoint('./models/crf.{epoch:02d}-{val_acc:.2f}.hdf5', monitor='val_acc', verbose=0,
                         save_best_only=False, save_weights_only=False, mode='auto', period=1)
    model.fit(X_train, Y_train, batch_size=100, epochs=epoches,
              validation_data=[X_test, Y_test], callbacks=[tb, cp])

    # evaluate
    score = model.evaluate(X_test, Y_test, batch_size=100)
    print('Test loss:', score[0])
    print('Test accuracy', score[1])
    model.save('keras_crf')

def create_custom_objects():
    instanceHolder = {"instance": None}
    class ClassWrapper(CRF):
        def __init__(self, *args, **kwargs):
            instanceHolder["instance"] = self
            super(ClassWrapper, self).__init__(*args, **kwargs)
    def loss(*args):
        method = getattr(instanceHolder["instance"], "loss_function")
        return method(*args)
    def accuracy(*args):
        method = getattr(instanceHolder["instance"], "accuracy")
        return method(*args)
    return {"ClassWrapper": ClassWrapper ,"CRF": ClassWrapper, "loss": loss, "accuracy":accuracy}

def predict(words):
    '''预测时也要padding!!!'''
    model = load_model('keras_crf', custom_objects=create_custom_objects())
    sentence = []
    for i in words:
        if i in word2num:
            sentence.append(word2num[i])
        else:
            sentence.append(word2num['<UNK>'])
    sentence = pad_sequences([sentence], maxlen=max_len, value=0)
    y_pred = model.predict(sentence).argmax(-1)[sentence > 0]
    print([label2tag[t] for t in y_pred])

if __name__ == '__main__':
    # train()
    predict('JAVA工程师')
    # num2word, label2tag = load_di()
    # X_train, X_test, Y_train, Y_test = gen_datasets()
    # print(X_train[0], Y_train[0])
    # x = [num2word[str(i)] for i in X_train[0]]
    # y = [label2tag[i[0]] for i in Y_train[0]]
    # print(x, y)