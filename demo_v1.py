''' Demo SDK for LiveStreaming
    Author Dan Yang
    Time 2018-10-15
    For LiveStreaming Game'''
# import the env from pip
import LiveStreamingEnv.env as env
import LiveStreamingEnv.load_trace as load_trace
import matplotlib.pyplot as plt
import time
import numpy as np
# path setting
TRAIN_TRACES = './network_trace_2/'   #train trace path setting,
#video_size_file = './video_trace/AsianCup_China_Uzbekistan/frame_trace_'      #video trace path setting
video_size_file = './video_trace_2/game/frame_trace_'
LogFile_Path = "./log/"                #log file trace path setting,
# Debug Mode: if True, You can see the debug info in the logfile
#             if False, no log ,but the training speed is high
DEBUG = False
DRAW = False
# load the trace
all_cooked_time, all_cooked_bw, all_file_names = load_trace.load_trace(TRAIN_TRACES)
#random_seed 
random_seed = 2
video_count = 0
FPS = 25
frame_time_len = 0.04
#init the environment
#setting one:
#     1,all_cooked_time : timestamp
#     2,all_cooked_bw   : throughput
#     3,all_cooked_rtt  : rtt
#     4,agent_id        : random_seed
#     5,logfile_path    : logfile_path
#     6,VIDEO_SIZE_FILE : Video Size File Path
#     7,Debug Setting   : Debug
net_env = env.Environment(all_cooked_time=all_cooked_time,
			  all_cooked_bw=all_cooked_bw,
			  random_seed=random_seed,
			  logfile_path=LogFile_Path,
			  VIDEO_SIZE_FILE=video_size_file,
			  Debug = DEBUG)

BIT_RATE      = [500.0,850.0,1200.0,1850.0] # kpbs
TARGET_BUFFER = [2.0,3.0]   # seconds
# ABR setting
RESEVOIR = 0.5
CUSHION  = 2

cnt = 0
# defalut setting
last_bit_rate = 0
bit_rate = 0
target_buffer = 0
# QOE setting
reward_frame = 0
reward_all = 0
reward_all_1 = 0
reward_all_2 = 0
reward_all_3 = 0
reward_all_4 = 0
SMOOTH_PENALTY= 0.02 
REBUF_PENALTY = 1.5 
LANTENCY_PENALTY = 0.005 

segment_count_threshold = 5
segment_count = 0
segment_count_list = []
th = 0
th_list = []
time_list = []
# plot info
idx = 0
id_list = []
bit_rate_record = []
buffer_record = []
throughput_record = []
# plot the real time image
if DRAW:
    fig = plt.figure()
    plt.ion()
    plt.xlabel("time")
    plt.axis('off')
while True:
        reward_frame = 0
        reward_1 = 0
        reward_2 = 0
        reward_3 = 0
        reward_4 = 0
        # input the train steps
        #if cnt > 5000:
            #plt.ioff()
        #    break
        #actions bit_rate  target_buffer
        # every steps to call the environment
        # time           : physical time 
        # time_interval  : time duration in this step
        # send_data_size : download frame data size in this step
        # chunk_len      : frame time len
        # rebuf          : rebuf time in this step          
        # buffer_size    : current client buffer_size in this step          
        # rtt            : current buffer  in this step          
        # play_time_len  : played time len  in this step          
        # end_delay      : end to end latency which means the (upload end timestamp - play end timestamp)
        # decision_flag  : Only in decision_flag is True ,you can choose the new actions, other time can't Becasuse the Gop is consist by the I frame and P frame. Only in I frame you can skip your frame
        # buffer_flag    : If the True which means the video is rebuffing , client buffer is rebuffing, no play the video
        # cdn_flag       : If the True cdn has no frame to get 
        # end_of_video   : If the True ,which means the video is over.
        time, time_interval, send_data_size, chunk_len,\
                rebuf, buffer_size, play_time_len,end_delay,\
                cdn_newest_id, download_id,cdn_has_frame,decision_flag, \
                buffer_flag,cdn_flag, end_of_video = net_env.get_video_frame(bit_rate,target_buffer)
        cnt += 1
        if time_interval != 0:
            # plot bit_rate 
            id_list.append(idx)
            idx += time_interval
            bit_rate_record.append(BIT_RATE[bit_rate])
            # plot buffer 
            buffer_record.append(buffer_size)
            # plot throughput 
            trace_idx = net_env.get_trace_id()
            #print(trace_idx, idx,len(all_cooked_bw[trace_idx]))
            throughput_record.append(all_cooked_bw[trace_idx][int(idx/0.5)% 5880])
        if not cdn_flag:
            reward_frame = frame_time_len * float(BIT_RATE[bit_rate]) / 1000  - REBUF_PENALTY * rebuf - LANTENCY_PENALTY * end_delay
            reward_1 = frame_time_len * float(BIT_RATE[bit_rate]) / 1000
            reward_2 = REBUF_PENALTY * rebuf
            reward_3 = LANTENCY_PENALTY * end_delay
            if time_interval != 0:
                th += send_data_size/time_interval/1000000
            else:
                th = 0
        else:
            reward_frame = -(REBUF_PENALTY * rebuf)
            reward_1 = 0
            reward_2 = REBUF_PENALTY * rebuf
            reward_3 = 0
        
        if decision_flag or end_of_video:
            # reward formate = play_time * BIT_RATE - 4.3 * rebuf - 1.2 * end_delay
            reward_frame += -1 * SMOOTH_PENALTY * (abs(BIT_RATE[bit_rate] - BIT_RATE[last_bit_rate]) / 1000)
            reward_4 = 1 * SMOOTH_PENALTY * (abs(BIT_RATE[bit_rate] - BIT_RATE[last_bit_rate]) / 1000)
            # last_bit_rate
            last_bit_rate = bit_rate
            time_list.append(time)
            th_list.append(th/50)
            segment_count_list.append(segment_count)
            segment_count = 0
            th = 0

       
            
            # draw setting
            if DRAW:
                ax = fig.add_subplot(311)
                plt.ylabel("BIT_RATE")
                plt.ylim(300,2000)
                plt.plot(id_list,bit_rate_record,'-r')
            
                ax = fig.add_subplot(312)
                plt.ylabel("Buffer_size")
                plt.ylim(0,7)
                plt.plot(id_list,buffer_record,'-b')

                ax = fig.add_subplot(313)
                plt.ylabel("throughput")
                plt.ylim(0,2500)
                plt.plot(id_list,throughput_record,'-g')

                plt.draw()
                plt.pause(0.01)



        # -------------------------------------------Your Algorithm ------------------------------------------- 
        # which part is the althgrothm part ,the buffer based , 
        # if the buffer is enough ,choose the high quality
        # if the buffer is danger, choose the low  quality
        # if there is no rebuf ,choose the low target_buffer
        if decision_flag:
            delta_segment_count = abs(segment_count_list[-1]-50)
            ave_throughput = th_list[-1]
            if ave_throughput <= 0.5:
                bit_rate = 0
            elif ave_throughput <= 0.85:
                if delta_segment_count <= segment_count_threshold:
                    if buffer_size < 0.5:
                        bit_rate = 0
                    else: 
                        bit_rate = 0
                else:
                    if buffer_size < 0.5:
                        bit_rate = 0
                    else: 
                        bit_rate = 1
            elif ave_throughput <= 1.2:
                if delta_segment_count <= segment_count_threshold:
                    if buffer_size < 0.5:
                        bit_rate = 0
                    else: 
                        bit_rate = 1
                else:
                    if buffer_size < 0.5:
                        bit_rate = 1
                    else: 
                        bit_rate = 2
            elif ave_throughput <= 1.8:
                if delta_segment_count <= segment_count_threshold:
                    if buffer_size < 0.5:
                        bit_rate = 1
                    else: 
                        bit_rate = 2
                else:
                    if buffer_size < 0.5:
                        bit_rate = 2
                    else: 
                        bit_rate = 3
            else:
                if delta_segment_count <= segment_count_threshold:
                    if buffer_size < 0.5:
                        bit_rate = 2
                    else: 
                        bit_rate = 3
                else:
                    bit_rate = 3


            """ if buffer_size < 0.5:
                bit_rate = 0
            elif buffer_size <= 1:
                bit_rate = 1
            elif buffer_size <= 2.5:
                bit_rate = 2
            else: 
                bit_rate = 3 """

            #bit_rate = 2
            target_buffer = 0
        # ------------------------------------------- End  ------------------------------------------- 
        segment_count += 1
        reward_all += reward_frame
        reward_all_1 += reward_1
        reward_all_2 += reward_2
        reward_all_3 += reward_3
        reward_all_4 += reward_4
        if end_of_video:
            # Narrow the range of results
            break
            
if DRAW:
    plt.show()
fig = plt.figure(figsize=(16,12),dpi=80)
ax = fig.add_subplot(511)
plt.ylabel("segment_count")
plt.plot(time_list[:-1],segment_count_list[:-1],'-r')
ax = fig.add_subplot(512)
plt.ylabel("th")
plt.plot(time_list[:-1],th_list[:-1],'-g')
ax = fig.add_subplot(513)
plt.ylabel("th_record")
plt.plot(id_list,throughput_record,'-b')
ax = fig.add_subplot(514)
plt.ylabel("buffer")
plt.plot(id_list,buffer_record,'-r')
ax = fig.add_subplot(515)
plt.ylabel("bitrate")
plt.plot(id_list,bit_rate_record,'-r')
plt.show()
print(reward_all,reward_all_1,reward_all_2,reward_all_3,reward_all_4)

