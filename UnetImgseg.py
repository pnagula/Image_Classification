#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 30 11:59:38 2017

@author: Pavan
"""


from __future__ import print_function

import os
from skimage.transform import resize
from skimage.io import imsave
import numpy as np
from keras.models import Model
from keras.layers import Input, Convolution2D, MaxPooling2D, Deconvolution2D
from keras.engine.topology import Merge
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from keras import backend as K
from keras import regularizers

from data import load_train_data, load_test_data

#K.set_image_data_format('channels_last')  # TF dimension ordering in this code

img_rows = 512
img_cols = 512

smooth = 1.


def dice_coef(y_true, y_pred):
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)


def dice_coef_loss(y_true, y_pred):
    return -dice_coef(y_true, y_pred)


def get_unet():
    inputs = Input((img_rows, img_cols, 3))
    
    convp0 = Conv2D(8, (3, 3),  padding='same')(inputs)
    convp0 = BatchNormalization(momentum=0.99)(convp0)
    convp0 = Activation('relu')(convp0)
    convp0 = Conv2D(8, (3, 3),  padding='same')(convp0)
    convp0 = BatchNormalization(momentum=0.99)(convp0)
    convp0 = Activation('relu')(convp0)
    poolp0 = MaxPooling2D(pool_size=(2, 2))(convp0)

    conv0 = Conv2D(16, (3, 3),  padding='same')(poolp0)
    conv0 = BatchNormalization(momentum=0.99)(conv0)
    conv0 = Activation('relu')(conv0)
    conv0 = Conv2D(16, (3, 3),  padding='same')(conv0)
    conv0 = BatchNormalization(momentum=0.99)(conv0)
    conv0 = Activation('relu')(conv0)
    pool0 = MaxPooling2D(pool_size=(2, 2))(conv0)

    conv1 = Conv2D(32, (3, 3),  padding='same')(pool0)
    conv1 = BatchNormalization(momentum=0.99)(conv1)
    conv1 = Activation('relu')(conv1)
    conv1 = Conv2D(32, (3, 3),  padding='same')(conv1)
    conv1 = BatchNormalization(momentum=0.99)(conv1)
    conv1 = Activation('relu')(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = Conv2D(64, (3, 3),  padding='same')(pool1)
    conv2 = BatchNormalization(momentum=0.99)(conv2)
    conv2 = Activation('relu')(conv2)
    conv2 = Conv2D(64, (3, 3),  padding='same')(conv2)
    conv2 = BatchNormalization(momentum=0.99)(conv2)
    conv2 = Activation('relu')(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = Conv2D(128, (3, 3),  padding='same')(pool2)
    conv3 = BatchNormalization(momentum=0.99)(conv3)
    conv3 = Activation('relu')(conv3)
    conv3 = Conv2D(128, (3, 3),  padding='same')(conv3)
    conv3 = BatchNormalization(momentum=0.99)(conv3)
    conv3 = Activation('relu')(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = Conv2D(256, (3, 3),  padding='same')(pool3)
    conv4 = BatchNormalization(momentum=0.99)(conv4)
    conv4 = Activation('relu')(conv4)
    conv4 = Conv2D(256, (3, 3),  padding='same')(conv4)
    conv4 = BatchNormalization(momentum=0.99)(conv4)
    conv4 = Activation('relu')(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = Conv2D(512, (3, 3),  padding='same')(pool4)
    conv5 = BatchNormalization(momentum=0.99)(conv5)
    conv5 = Activation('relu')(conv5)
    conv5 = Conv2D(512, (3, 3),  padding='same')(conv5)
    conv5 = BatchNormalization(momentum=0.99)(conv5)
    conv5 = Activation('relu')(conv5)
    pool5 = MaxPooling2D(pool_size=(2, 2))(conv5)
   
    convc = Conv2D(1024, (3, 3),  padding='same')(pool5)
    convc = BatchNormalization(momentum=0.99)(convc)
    convc = Activation('relu')(convc)
    convc = Conv2D(1024, (3, 3),  padding='same')(convc)
    convc = BatchNormalization(momentum=0.99)(convc)
    convc = Activation('relu')(convc)
    
    convct = Conv2DTranspose(512, (2, 2), strides=(2, 2), padding='same')(convc) 
    convct = BatchNormalization(momentum=0.99)(convct)
    convct = Activation('relu')(convct)
    convct = concatenate([convct,conv5],axis=3)
    convct = Conv2D(512, (3, 3),  padding='same')(convct)
    convct = BatchNormalization(momentum=0.99)(convct)
    convct = Activation('relu')(convct)
    convct = Conv2D(512, (3, 3),  padding='same')(convct)
    convct = BatchNormalization(momentum=0.99)(convct)
    convct = Activation('relu')(convct)
    
    conv6 = Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(convct) 
    conv6 = BatchNormalization(momentum=0.99)(conv6)
    conv6 = Activation('relu')(conv6)
    conv6 = concatenate([conv6,conv4],axis=3)
    conv6 = Conv2D(256, (3, 3),  padding='same')(conv6)
    conv6 = BatchNormalization(momentum=0.99)(conv6)
    conv6 = Activation('relu')(conv6)
    conv6 = Conv2D(256, (3, 3),  padding='same')(conv6)
    conv6 = BatchNormalization(momentum=0.99)(conv6)
    conv6 = Activation('relu')(conv6)
    
    conv7 = Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(conv6)
    conv7 = BatchNormalization(momentum=0.99)(conv7)
    conv7 = Activation('relu')(conv7)
    conv7 = concatenate([conv7, conv3], axis=3)
    conv7 = Conv2D(128, (3, 3),  padding='same')(conv7)
    conv7 = BatchNormalization(momentum=0.99)(conv7)
    conv7 = Activation('relu')(conv7)
    conv7 = Conv2D(128, (3, 3),  padding='same')(conv7)
    conv7 = BatchNormalization(momentum=0.99)(conv7)
    conv7 = Activation('relu')(conv7)

    conv8 = Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(conv7)
    conv8 = BatchNormalization(momentum=0.99)(conv8)
    conv8 = Activation('relu')(conv8)
    conv8 = concatenate([conv8, conv2], axis=3)
    conv8 = Conv2D(64, (3, 3),  padding='same')(conv8)
    conv8 = BatchNormalization(momentum=0.99)(conv8)
    conv8 = Activation('relu')(conv8)
    conv8 = Conv2D(64, (3, 3),  padding='same')(conv8)
    conv8 = BatchNormalization(momentum=0.99)(conv8)
    conv8 = Activation('relu')(conv8)

    conv9 = Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(conv8)
    conv9 = BatchNormalization(momentum=0.99)(conv9)
    conv9 = Activation('relu')(conv9)
    conv9 = concatenate([conv9, conv1], axis=3)
    conv9 = Conv2D(32, (3, 3),  padding='same')(conv9)
    conv9 = BatchNormalization(momentum=0.99)(conv9)
    conv9 = Activation('relu')(conv9)
    conv9 = Conv2D(32, (3, 3),  padding='same')(conv9)
    conv9 = BatchNormalization(momentum=0.99)(conv9)
    conv9 = Activation('relu')(conv9)

    conv10 = Conv2DTranspose(16, (2, 2), strides=(2, 2), padding='same')(conv9)
    conv10 = BatchNormalization(momentum=0.99)(conv10)
    conv10 = Activation('relu')(conv10)
    conv10 = concatenate([conv10, conv0], axis=3)
    conv10 = Conv2D(16, (3, 3),  padding='same')(conv10)
    conv10 = BatchNormalization(momentum=0.99)(conv10)
    conv10 = Activation('relu')(conv10)
    conv10 = Conv2D(16, (3, 3),  padding='same')(conv10)
    conv10 = BatchNormalization(momentum=0.99)(conv10)
    conv10 = Activation('relu')(conv10)

    conv11 = Conv2DTranspose(8, (2, 2), strides=(2, 2), padding='same')(conv10)
    conv11 = BatchNormalization(momentum=0.99)(conv11)
    conv11 = Activation('relu')(conv11)
    conv11 = concatenate([conv11, convp0], axis=3)
    conv11 = Conv2D(8, (3, 3),  padding='same')(conv11)
    conv11 = BatchNormalization(momentum=0.99)(conv11)
    conv11 = Activation('relu')(conv11)
    conv11 = Conv2D(8, (3, 3),  padding='same')(conv11)
    conv11 = BatchNormalization(momentum=0.99)(conv11)
    conv11 = Activation('relu')(conv11)

    conv12 = Conv2D(1, 1, 1, activation='sigmoid')(conv11)

    model = Model(inputs=[inputs], outputs=[conv12])

    model.compile(optimizer=Adam(lr=1e-3), loss=dice_coef_loss, metrics=[dice_coef])

    return model


def preprocess(imgs,itype='I'):
    if itype=='M':
       imgs_p = np.ndarray((imgs.shape[0], img_rows, img_cols), dtype=np.uint8)
    else:
       imgs_p = np.ndarray((imgs.shape[0], img_rows, img_cols,3), dtype=np.uint8)
    
    for i in range(imgs.shape[0]):
        if itype=='M':
           imgs_p[i] = resize(imgs[i], (img_cols, img_rows), preserve_range=True)
        else:
           imgs_p[i] = resize(imgs[i], (img_cols, img_rows,3), preserve_range=True)
    
    if itype=='M':
       imgs_p = imgs_p[..., np.newaxis]
    return imgs_p


def train_and_predict():
    print('-'*30)
    print('Loading and preprocessing train data...')
    print('-'*30)
    imgs_train, imgs_mask_train = load_train_data()
    imgs_train = preprocess(imgs_train,'I')
    imgs_mask_train = preprocess(imgs_mask_train,'M')
#
    print(imgs_train.shape)
    print(imgs_mask_train.shape)
    imgs_train = imgs_train.astype('float32')
    mean = np.mean(imgs_train)  # mean for data centering
    std = np.std(imgs_train)  # std for data normalization

    imgs_train -= mean
    imgs_train /= std

    imgs_mask_train = imgs_mask_train.astype('float32')
    imgs_mask_train /= 255.  # scale masks to [0, 1]

    print('-'*30)
    print('Creating and compiling model...')
    print('-'*30)
    model = get_unet()
    model_checkpoint = ModelCheckpoint('weights.h5', monitor='val_loss', save_best_only=True)

    print('-'*30)
    print('Fitting model...')
    print('-'*30)
    model.fit(imgs_train, imgs_mask_train, batch_size=3, nb_epoch=32, verbose=1, shuffle=True,
 #             validation_split=0.2,
              callbacks=[model_checkpoint])
    model.save('unetmodel')
#
#    print('-'*30)
#    print('Loading and preprocessing test data...')
#    print('-'*30)
#    imgs_test, imgs_id_test = load_test_data()
#    imgs_test = preprocess(imgs_test)
#
#    imgs_test = imgs_test.astype('float32')
#    imgs_test -= mean
#    imgs_test /= std
#
#    print('-'*30)
#    print('Loading saved weights...')
#    print('-'*30)
#    model.load_weights('weights.h5')
#
#    print('-'*30)
#    print('Predicting masks on test data...')
#    print('-'*30)
#    imgs_mask_test = model.predict(imgs_test, verbose=1)
#    np.save('imgs_mask_test.npy', imgs_mask_test)
#
#    print('-' * 30)
#    print('Saving predicted masks to files...')
#    print('-' * 30)
#    pred_dir = 'preds'
#    if not os.path.exists(pred_dir):
#        os.mkdir(pred_dir)
#    for image, image_id in zip(imgs_mask_test, imgs_id_test):
#        image = (image[:, :, 0] * 255.).astype(np.uint8)
#        imsave(os.path.join(pred_dir, str(image_id) + '_pred.png'), image)

if __name__ == '__main__':
    train_and_predict()
