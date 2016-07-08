#!/usr/bin/env python2
from gnuradio import gr
from gnuradio import audio, analog
from gnuradio import digital
from gnuradio import blocks
from grc_gnuradio import blks2 as grc_blks2
import threading
import time
import numpy
import struct
import numpy as np
import tensorflow as tf   
import specest 
from tensor import *
import matplotlib.pylab as plt
import tflearn

snr = ["20","15","10","5","0","-5","-10","-15","-20"] 
snrv = [[1,0.32],[1,0.435],[1,0.56],[1,0.75],[1,1],[0.75,1],[0.56,1],[0.435,1],[0.32,1]]
mod = ["2psk","4psk","8psk","fsk"]

Np = 4
P = 4
L = 2

train = False
input_num = 112

np.set_printoptions(threshold=np.nan)



if train == True:
    n_input = tf.placeholder(tf.float32, shape=[None, input_num], name="inp")
    n_output = tf.placeholder(tf.float32, shape=[None, len(mod)], name="outp")
    
    """
    hidden_nodes = int( 0.89 * (input_num) )
    b_hidden = tf.Variable(tf.random_normal([hidden_nodes]), name="hidden_bias")
    W_hidden = tf.Variable(tf.random_normal([input_num, hidden_nodes]), name="hidden_weights")

    # calc hidden layer's activation
    hidden = tf.sigmoid(tf.matmul(n_input, W_hidden) + b_hidden)
    W_output = tf.Variable(tf.random_normal([hidden_nodes, len(mod)]), name="output_weights")  # output layer's weight matrix
    output = tf.sigmoid(tf.matmul(hidden, W_output),name="out")  # calc output layer's activation
    cross_entropy = -tf.reduce_sum(output*tf.log(tf.clip_by_value(n_output,1e-10,1.0)))
    loss = tf.reduce_mean(cross_entropy)  # mean the cross_entropy
    optimizer = tf.train.AdamOptimizer(0.01)  # take a gradient descent for optimizing with a "stepsize" of 0.1
    train = optimizer.minimize(loss)  # let the optimizer train
    """

    """
    logits = tf.matmul(n_input, weights) + biases
    relu = tf.sigmoid(logits)
    dp = tf.nn.dropout(relu, 0.9)
    logits2 = tf.matmul(dp, weights2) + biases2
    relu2 = tf.sigmoid(logits2)
    dp2 = tf.nn.dropout(relu2, 0.9)
    logits3 = tf.matmul(dp2, weights3) + biases3  
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits3, tf_train_labels))
    train =tf.train.AdamOptimizer(learning_rate=0.001).minimize(loss)
    """






 
    init = tf.initialize_all_variables()
    
    sess = tf.Session()  # create the session and therefore the graph
    sess.run(init)  # initialize all variables  































class my_top_block(gr.top_block):
    def __init__(self,modulation,snr):

        self.samp_rate = samp_rate = 32000
        gr.top_block.__init__(self)


        if modulation == "2psk":
            self.digital_mod = digital.psk.psk_mod(
                constellation_points=2,
                mod_code="gray",
                differential=True,
                samples_per_symbol=2,
                excess_bw=0.35,
                verbose=False,
                log=False,
            )
            bits = 1
        elif modulation == "4psk":
            self.digital_mod = digital.psk.psk_mod(
                constellation_points=4,
                mod_code="gray",
                differential=True,
                samples_per_symbol=2,
                excess_bw=0.35,
                verbose=False,
                log=False,
            )
            bits = 2
        elif modulation == "8psk":
            self.digital_mod = digital.psk.psk_mod(
                constellation_points=8,
                mod_code="gray",
                differential=True,
                samples_per_symbol=2,
                excess_bw=0.35,
                verbose=False,
                log=False,
            )
            bits = 3
        elif modulation == "fsk":
            self.digital_mod = digital.gfsk_mod(
        	    samples_per_symbol=2,
        	    sensitivity=1.0,
        	    bt=0.35,
        	    verbose=False,
        	    log=False,
            )
            bits = 1

        self.sink = blocks.vector_sink_f(2*Np) 

        self.sink = blocks.null_sink(gr.sizeof_float * 2 * Np)    

        self.blocks_add_xx_1 = blocks.add_vcc(1)
        self.specest_cyclo_fam_1 = specest.cyclo_fam(Np, P, L)
        self.blocks_multiply_const_vxx_3 = blocks.multiply_const_vcc((snrv[snr][0], ))
        self.blocks_throttle_0 = blocks.throttle(gr.sizeof_gr_complex*1, samp_rate,True)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 1024)
        self.blocks_null_sink_0 = blocks.null_sink(gr.sizeof_float*1)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, snrv[snr][1], 0)
        self.analog_random_source_x_0 = blocks.vector_source_b(map(int, numpy.random.randint(0, 256, 2000000)), False)
        self.msgq_out = blocks_message_sink_0_msgq_out = gr.msg_queue(1) 
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_float*2*Np, blocks_message_sink_0_msgq_out, False)   
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_1, 1))    
        self.connect((self.blocks_multiply_const_vxx_3, 0), (self.blocks_add_xx_1, 0))    
        self.connect((self.analog_random_source_x_0, 0), (self.digital_mod, 0)) 
        #self.connect((self.digital_mod, 0), (self.blocks_throttle_0, 0))  
        self.connect((self.digital_mod, 0), (self.blocks_throttle_0, 0))    
        self.connect((self.blocks_throttle_0, 0),(self.blocks_multiply_const_vxx_3, 0))    

        #self.connect((self.digital_mod, 0), (self.blocks_multiply_const_vxx_3, 0))    
        # self.connect((self.blocks_throttle_0, 0),(self.blocks_multiply_const_vxx_3, 0))    
        self.connect((self.blocks_add_xx_1, 0),(self.specest_cyclo_fam_1, 0))    
        #self.connect((self.specest_cyclo_fam_1,0),(self.blocks_message_sink_0,0))


        #self.connect((self.specest_cyclo_fam_1, 0), (self.blocks_vector_to_stream_0, 0))
        #self.connect((self.blocks_stream_to_vector_0, 0), (self.inspector_TFModel_0, 0))   
        #self.msg_connect((self.inspector_TFModel_0, 'classification'), (self.blocks_message_debug_0, 'print'))         
        self.connect((self.specest_cyclo_fam_1,0),(self.sink,0))





from tensor import *






def shuffle_in_unison_inplace(a, b):
    assert len(a) == len(b)
    p = numpy.random.permutation(len(a))
    return a[p], b[p]


















if __name__ == '__main__':

    try:
        inp = []
        out = [] 

        mcount = 0

        for m in mod:
            """
            if not (m == "2psk" ):
                mcount += 1
                continue
            """
            z = np.zeros((len(mod),))
            z[mcount] = 1        

            print(z)
            
            for snr in range(0,1):
                print(m,"SNR",snr)
                tb = my_top_block(m,snr)
                tb.start()

                time.sleep(3)

                count = 0
                fin = False
                old = None
                while True: 
                    #data=tb.msgq_out.delete_head().to_string() # this indeed blocks
                    #data = np.array(tb.specest_cyclo_fam_1.get_estimate())
                    
                    ## Get last bytes
                    #floats =  tb.sink.data()#[-2*P*L*(2*Np):] 
                    floats = np.array(tb.specest_cyclo_fam_1.get_estimate())

                    if old == None:
                        old = floats
                    else:
                        if (floats == old).all():
                            continue
                
                    count = count + 1  
        
                    if count % 2 == 0:
                        f = floats.flatten()
                                                                                                                                                                                                                                  
                        o2 = np.array(f)                                                                                                                                                                                          
                        o = (o2/o2.max())                                                                                                                                                                                         
                        o[o == np.inf] = 0                                                                                                                                                                                          
                
                        inp.append(o)
                        out.append(z)

                    if count > 10000:
                        break

                    old = floats
                    
                    #print(floats.shape)

                    #quit()
                    #print(len(floats)/128)
                    #data = np.asarray(estimated_data)
                   
    
                 
                    """ 
                    print("SH",data.shape)
    
                    inp.append(data)
                    out.append(z)
                    count += 1
                    #if count > 5:
    
                    if count > 10:
                        tb.stop()
                        break
                    print("COUNT ",count)
                    """
                    #Np = 32                                                                                                                               
                    #P  = 128                                                                                                                              
                    #L  = Np/8 
               
                    """
                    floats = []
                   
                    for i in range(0,len(data),4):
                        floats.append(struct.unpack_from('f',data[i:i+4])[0])
                    
                    print("ll",len(floats))
                    """
                
                    """
                    for i in range(0, len(floats),input_num):
                        dat = floats[i:i+(input_num)]

                        if not len(dat) == input_num:
                            break
                        inp.append(np.array(dat))
                        out.append(z)
                        
                        if count > 1000:
                            break 
                        count += 1
            
                    break
                    """
                    

                    
            #break
                            
            mcount += 1



        

        inp, out = shuffle_in_unison_inplace(np.array(inp), np.array(out))
    
        test_i = inp[len(inp)/2:len(inp)]
        test_o = out[len(inp)/2:len(inp)]

        print(len(test_i),len(test_o))
        
        train_i = inp[0:len(inp)/2]
        train_o = out[0:len(inp)/2]

        print(len(train_i),len(train_o))

        print("About to train")
       
        #print("NEURONS",inp[0].shape[0]*inp[0].shape[1])
        # Parameters
        learning_rate = 0.001
        training_epochs = 200
        batch_size = 100
        display_step = 1

        # Network Parameters
        n_hidden_1 = input_num / 3 # 1st layer number of features
        n_hidden_2 = input_num / 3 # 2nd layer number of features
        n_input = input_num # MNIST data input (img shape: 28*28)
        n_classes = len(mod) # MNIST total classes (0-9 digits)

        # tf Graph input
        x = tf.placeholder("float", [None, n_input])
        y = tf.placeholder("float", [None, n_classes])


        # Create model
        def multilayer_perceptron(x, weights, biases):
            # Hidden layer with RELU activation
            layer_1 = tf.add(tf.matmul(x, weights['h1']), biases['b1'])
            layer_1 = tf.nn.relu(layer_1)
            # Hidden layer with RELU activation
            layer_2 = tf.add(tf.matmul(layer_1, weights['h2']), biases['b2'])
            layer_2 = tf.nn.relu(layer_2)
            # Output layer with linear activation
            out_layer = tf.matmul(layer_2, weights['out']) + biases['out']
            return out_layer

        # Store layers weight & bias
        weights = {
            'h1': tf.Variable(tf.random_normal([n_input, n_hidden_1])),
            'h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
            'out': tf.Variable(tf.random_normal([n_hidden_2, n_classes]))
        }

        biases = {
            'b1': tf.Variable(tf.random_normal([n_hidden_1])),
            'b2': tf.Variable(tf.random_normal([n_hidden_2])),
            'out': tf.Variable(tf.random_normal([n_classes]))
        }

        # Construct model
        pred = multilayer_perceptron(x, weights, biases)

        # Define loss and optimizer
        cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

        # Initializing the variables
        init = tf.initialize_all_variables()

        # Launch the graph
        with tf.Session() as sess:
            sess.run(init)

            # Training cycle
            for epoch in range(training_epochs):
                avg_cost = 0.
                total_batch = int(len(inp)/batch_size)
                # Loop over all batches
                for i in range(total_batch):
                    #batch_x, batch_y = mnist.train.next_batch(batch_size)

                    batch_x = train_i[i*batch_size:(i*batch_size)+100]
                    batch_y = train_o[i*batch_size:(i*batch_size)+100]

                    if len(batch_x) == 0 or len(batch_y) == 0:
                        break
                    # Run optimization op (backprop) and cost op (to get loss value)
                    _, c = sess.run([optimizer, cost], feed_dict={x: batch_x,
                                                          y: batch_y})
                    # Compute average loss
                    avg_cost += c / total_batch
                # Display logs per epoch step
                if epoch % display_step == 0:
                    print "Epoch:", '%04d' % (epoch+1), "cost=", \
                        "{:.9f}".format(avg_cost)
            
            print "Optimization Finished!"

            #pred.save("mlayer.ann")

            correct_prediction = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
            # Calculate accuracy
            accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
            print "Accuracy:", accuracy.eval({x: test_i, y: test_o})

        quit()
    
        
        
        with tf.Graph().as_default():


            """
            hidden = int(input_num * (0.89))
            tflearn.init_graph(num_cores=8)
            net = tflearn.input_data(shape=[None,inp[0].shape[0],inp[0].shape[1]])
            net = tflearn.fully_connected(net, hidden,activation='sigmoid') #, activation='sigmoid')
            #net = tflearn.dropout(net, 0.8)
            net = tflearn.fully_connected(net, len(mod), activation='softmax')
            regressor = tflearn.regression(net, optimizer='adam',learning_rate=0.001,loss='categorical_crossentropy') #, loss=lossv)
            m = tflearn.DNN(regressor,tensorboard_verbose=3) 
            """

            if train:
                m.fit(inp, out, n_epoch=50, snapshot_epoch=False,show_metric=True)
                m.save("fam.ann")

            else:
                m.load("fam.ann")

                print(inp[1])
                print("---")
                print(inp[2])
                print("---")
                print(inp[3])
                if (inp[1] == inp[100]).all():
                    print("error")
                    quit()
                ret = m.predict(inp)


                #for v in ret:
                #    print(np.argmax(v))

                #print(ret[0])
                #print(out[0])


                print(100.0 * np.sum(np.argmax(ret, 1) == np.argmax(out, 1))/ len(ret))

        quit()
            

        if train:

            print(len(inp),len(out))
            for epoch in xrange(0, 1000):
                cvalues = sess.run([train, loss, W_hidden, b_hidden, W_output],
                       feed_dict={n_input: inp, n_output: out})
                if epoch % 200 == 0:
                    print("")
                    print("step: {:>3}".format(epoch))
                    print("loss: {}".format(cvalues[1]))

            save_graph(sess,"/tmp/","saved_checkpoint","checkpoint_state","input_graph.pb","output_graph.pb")
        else:

            sess, inp_, out_ = load_graph("/tmp/output_graph.pb","/tmp")

            
            """
            image = plt.imshow(numpy.array(inp[1]),
                        interpolation='nearest',
                        animated=True,
                        extent=(-0.5, 0.5-1.0/Np, -1.0, 1.0-1.0/(P*L)))
            cbar = plt.colorbar(image)
            plt.xlabel('frequency / fs')
            plt.ylabel('cycle frequency / fs')
            plt.axis('normal')
            plt.title('Magnitude of estimated cyclic spectrum with FAM')

            data = numpy.array(inp[1]) 
            image.set_data(data) 
            image.changed() 
            cbar.set_clim(vmax=data.max()) 
            cbar.draw_all() 
            plt.draw()
            plt.show()  
            """

            

            print("OUT",out[0])
            
            ret = sess.run(out_,feed_dict={inp_: inp})

            print("RET",ret[0])
            print(len(ret),len(out))
            #ret = [ret[0]]
            #out = [out[0]]

            print(100.0 * np.sum(np.argmax(ret, 1) == np.argmax(out, 1))/ len(ret))
            
        
    except [[KeyboardInterrupt]]:
        pass

