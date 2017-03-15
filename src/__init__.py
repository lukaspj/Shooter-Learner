import tensorflow as tf
import numpy as np
import os

from ddqrn_trainer import DDQRNTrainer
from log_parser import parse_logs_in_folder
from sharpshooter_server import SharpShooterServer
from simple_ddqrn import DDQRN
<<<<<<< HEAD
from target_ddqrn import target_ddqrn
=======

import json

# Functions for updating the target network todo Needs review (copy-pasta)
def updateTargetGraph(tfVars,tau):
    total_vars = len(tfVars)
    op_holder = []
    middle = total_vars // 2 # "Floor division"
    for idx, var in enumerate(tfVars[0:middle]):
        op_holder.append(tfVars[idx+middle].assign((var.value()*tau) + ((1-tau)*tfVars[idx+middle].value())))
    return op_holder

# Couldn't this simply assign the target to the primary network? I.e. copy all the weights
def updateTarget(op_holder,sess):
    for op in op_holder:
        sess.run(op)
# End todo
>>>>>>> 6c22296472a93644dea5c93f0776a02fe73dd2cb

train_length = 8 #todo do we need this?
fv_size = 15 # Size of the FeatureVector (state)
actions_size = 8 # Number of actions we can take
batch_size = 32 # Number of experiences to use for each training step
discount_factor = .99

train_freq = 4 # How often do we train

input_frames = tf.placeholder(shape=[None, fv_size], dtype=tf.float32)

ddqrn = DDQRN(input_frames, train_length, fv_size, actions_size)
ddqrn_target = target_ddqrn(DDQRN(input_frames, train_length, fv_size, actions_size), tf.trainable_variables())

sess = tf.Session()
sess.run(tf.global_variables_initializer())

ddqrn_target.update(sess) # Set the target network to be equal to the primary network

logs = parse_logs_in_folder("data/game_logs")

load_model = False
save_path = "./dqn"

trainer = DDQRNTrainer(ddqrn, ddqrn_target, sess, input_frames)

if load_model == True:
    trainer.load(save_path)
else:
    for log_file in logs:
        trainer.start_episode()
        for i, event in enumerate(log_file):

            # Observe play
            s = event.feature_vector
            a = event.action
            s1 = log_file[i + 1].feature_vector
            r = log_file[i + 1].reward
            end = log_file[i + 1].end

            if event.player == 1:
                if end:
                    break
                else:
                    continue

            trainer.experience(s, a, r, s1, end)
            if end:
                break
        trainer.end_episode()

trainer.save(save_path)
print("Done training!")

# Assuming we have now done some kind of training.. Try to predict some actions!



def json_string_to_feature_vector(json_str):
    fv = json.loads(json_str)
    out = []
    out.append(fv["DeltaRot"])
    out.append(fv["DeltaMovedX"])
    out.append(fv["DeltaMovedY"])
    out.append(fv["VelX"])
    out.append(fv["VelY"])
    out.append(fv["DamageProb"])
    out.append(fv["DeltaDamageProb"])
    out.append(fv["DistanceToObstacleLeft"])
    out.append(fv["DistanceToObstacleRight"])
    out.append(fv["Health"])
    out.append(fv["EnemyHealth"])
    out.append(fv["TickCount"])
    out.append(fv["TicksSinceObservedEnemy"])
    out.append(fv["TicksSinceDamage"])
    out.append(fv["ShootDelay"])
    return out


def server_cb(msg):
    if msg["type"] == "instruction":
        return {"type": "instruction", "command": "resetMission"}

    if msg["type"] == "event":
        if msg["message"] == "game_start":
            print("Game has started!")
            return {"response": "success"}
        if msg["message"] == "game_end":
            print("Game has ended!")
            return {"response": "success"}
    if msg["type"] == "result":
        print("Game ended with result: " + str(msg))
        return {"response": "success"}

    if msg["type"] == "think":
        fv = json_string_to_feature_vector(msg["feature_vector"])
        ps = sess.run(ddqrn.predict, feed_dict={input_frames: [fv]})
        return ps[0].item()

    print("Unhandled message: " + str(msg))
    return 3

server = SharpShooterServer(server_cb)
server.start()
while True:
    server.receive_message()

#for i in range(10):
#    output = sess.run([ddqrn.output], feed_dict={input_frames:})