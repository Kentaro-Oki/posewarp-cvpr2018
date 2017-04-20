import tensorflow as tf
import os
import numpy as np
import sys
import cv2
import datareader
import preprocess
import networks
import scipy.io as sio
import param
from keras.models import load_model,Model
from keras.optimizers import Adam

batch_size = 8
gpu = '/gpu:3'
test_interval = 100
test_save_interval = 100
save_interval = 5000

n_test_vids = 13
vid_pth = '../../datasets/golfswinghd/videos/'
info_pth = '../../datasets/golfswinghd/videoinfo/'
n_end_remove = 5
img_sfx = '.jpg'
n_train_examples = 100000
n_test_examples = 1000

params = param.getParam()

def train():	
	config = tf.ConfigProto()
	config.gpu_options.allow_growth = True
	config.allow_soft_placement = True

	ex_train,ex_test = datareader.makeTransferExampleList(
		vid_pth,info_pth,n_test_vids,n_end_remove,img_sfx,n_train_examples,n_test_examples)

	train_feed = preprocess.transferExampleGenerator(ex_train,batch_size,params)
	test_feed = preprocess.transferExampleGenerator(ex_test,batch_size,params)
	
	with tf.Session(config=config) as sess:

		sess.run(tf.global_variables_initializer())
		coord = tf.train.Coordinator()
		threads = tf.train.start_queue_runners(coord=coord)

		with tf.device(gpu):
			model = networks.network_warp(params)
			model_mask = Model(model.input, model.get_layer('mask').output)
			model.compile(optimizer=Adam(lr=1e-4), loss='mae')
		
		#X_src,X_tgt,X_pose,X_warp,X_mask = next(train_feed)			
		#train_loss = model.train_on_batch([X_src,X_pose,X_warp,X_mask],X_tgt)
		#pred = model.predict([X_src,X_pose,X_warp,X_mask])
		#sio.savemat('test.mat', {'X_src': X_src, 'X_tgt': X_tgt, 'X_pose': X_pose, 'X_warp': X_warp, 'X_mask': X_mask,'pred': pred})
		#return
		#print train_loss

		step = 0	
		while(True):
			X_src,X_tgt,X_pose,X_warp,X_mask = next(train_feed)			

			with tf.device(gpu):
				train_loss = model.train_on_batch([X_src,X_pose,X_warp,X_mask],[X_tgt])

			print "0," + str(train_loss)
			sys.stdout.flush()	

			if(step % test_interval == 0):
				n_batches = 8

				test_loss = 0	
				for j in xrange(n_batches):	
					X_src,X_tgt,X_pose,X_warp,X_mask = next(test_feed)			
					test_loss += model.test_on_batch([X_src,X_pose,X_warp,X_mask], [X_tgt])

				test_loss /= (n_batches)
				print "1," + str(test_loss)
				sys.stdout.flush()

			if(step % test_save_interval==0):
				X_src,X_tgt,X_pose,X_warp,X_mask = next(test_feed)			
				pred_val = model.predict([X_src,X_pose,X_warp,X_mask])
				mask = model_mask.predict([X_src,X_pose,X_warp,X_mask])
				#X_pred = pred_val
		
				sio.savemat('../results/outputs/warp/' + str(step) + '.mat',
         		{'X_src': X_src,'X_tgt': X_tgt, 'X_warp': X_warp, 'pred': pred_val, 'mask': mask})	
	
			#if(step % save_interval==0): # and step > 0):
			#	model.save('../results/networks/warp/' + str(step) + '.h5')			
			
			step += 1	

if __name__ == "__main__":
	train()

'''
	#im_tf = tf.placeholder(tf.float32, shape=(batch_size,256,256,3))
	#x_tf = tf.placeholder(tf.float32, shape=(batch_size,256,256))
	#y_tf = tf.placeholder(tf.float32, shape=(batch_size,256,256))
	#out_tf = networks.interpolate([im_tf,x_tf,y_tf])
'''
